"""
Flask backend API for Hall Ticket Generator web application.
"""
import os
import sys
from pathlib import Path

# Fix for ReportLab compatibility with newer OpenSSL/Python versions
# Patch hashlib.md5 to handle usedforsecurity parameter gracefully
import hashlib
_original_md5 = hashlib.md5
def _patched_md5(*args, **kwargs):
    # Remove usedforsecurity if it's not supported by the underlying implementation
    if 'usedforsecurity' in kwargs:
        # Try with the parameter first
        try:
            return _original_md5(*args, **kwargs)
        except TypeError:
            # If usedforsecurity is not supported, remove it and try again
            kwargs_copy = kwargs.copy()
            kwargs_copy.pop('usedforsecurity')
            return _original_md5(*args, **kwargs_copy)
    return _original_md5(*args, **kwargs)
hashlib.md5 = _patched_md5

# Force stdout to be unbuffered so print statements appear immediately
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import tempfile
import shutil
import zipfile
import logging
import pandas as pd

# Modules are now in the same directory (backend/)
from excel_reader import StudentDetailsReader, TimetableReader
from photo_loader import PhotoLoader
from pdf_generator import HallTicketGenerator
from config import SchoolConfig
from validator import InputValidator

app = Flask(__name__)

# Add request logging middleware
@app.before_request
def log_request_info():
    if request.path == '/api/generate':
        print(f"\n[REQUEST] {request.method} {request.path}", flush=True)
        print(f"[REQUEST] Content-Type: {request.content_type}", flush=True)
        print(f"[REQUEST] Form keys: {list(request.form.keys())}", flush=True)
        print(f"[REQUEST] Files keys: {list(request.files.keys())}", flush=True)
        if 'show_photo_box' in request.form:
            print(f"[REQUEST] show_photo_box from form: '{request.form.get('show_photo_box')}'", flush=True)

# CORS configuration - allow environment variable for production
allowed_origins = os.getenv('CORS_ORIGINS', '*').split(',')
if allowed_origins == ['*']:
    # Development: allow all origins
    cors_origins = "*"
else:
    # Production: specific origins
    cors_origins = [origin.strip() for origin in allowed_origins]

CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "DELETE", "OPTIONS", "PUT"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
}, supports_credentials=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Temporary directory for file uploads
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / 'hallticket_uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True, parents=True)

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size


@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint."""
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'status': 'ok', 
        'message': 'Hall Ticket Generator API is running',
        'version': '1.0.0'
    }), 200


@app.route('/api/generate', methods=['POST', 'OPTIONS'])
def generate_hall_tickets():
    """Generate hall tickets from uploaded files."""
    import sys
    sys.stdout.write("=" * 50 + "\n")
    sys.stdout.write("GENERATE HALL TICKETS REQUEST RECEIVED\n")
    sys.stdout.write("=" * 50 + "\n")
    sys.stdout.flush()
    
    print("=" * 50, flush=True)
    print("GENERATE HALL TICKETS REQUEST RECEIVED", flush=True)
    print("=" * 50, flush=True)
    print(f"Request method: {request.method}", flush=True)
    print(f"Request content type: {request.content_type}", flush=True)
    print(f"Form keys: {list(request.form.keys())}", flush=True)
    print(f"Files keys: {list(request.files.keys())}", flush=True)
    
    try:
        # Get form data
        school_name = request.form.get('school_name', '').strip()
        school_address = request.form.get('school_address', '').strip()
        examination_name = request.form.get('examination_name', '').strip()
        logo_path = request.files.get('logo')
        signature_path = request.files.get('signature')
        
        # Get show_photo_box setting (default: True)
        show_photo_box_str = request.form.get('show_photo_box', 'true').strip().lower()
        print(f"[DEBUG] Raw show_photo_box value from form: '{show_photo_box_str}'", flush=True)
        # Explicitly check for 'false' to handle edge cases
        if show_photo_box_str in ('false', '0', 'no', 'off'):
            show_photo_box = False
        else:
            show_photo_box = show_photo_box_str == 'true'
        print(f"[DEBUG] Parsed show_photo_box: {show_photo_box} (type: {type(show_photo_box)})", flush=True)
        logger.info(f"Received show_photo_box value: '{show_photo_box_str}' -> {show_photo_box} (type: {type(show_photo_box)})")
        
        # Get examination timing data (optional)
        examination_timing = None
        if request.form.get('reporting_time'):
            examination_timing = {
                'reporting_time': request.form.get('reporting_time', '').strip(),
                'entry_time': request.form.get('entry_time', '').strip(),
                'cooloff_time': request.form.get('cooloff_time', '').strip(),
                'reading_time': request.form.get('reading_time', '').strip(),
                'writing_time': request.form.get('writing_time', '').strip()
            }
        
        if not school_name or not school_address:
            return jsonify({'error': 'School name and address are required'}), 400
        
        # Create temporary directory for this request
        request_id = request.form.get('request_id', 'default')
        work_dir = UPLOAD_FOLDER / request_id
        work_dir.mkdir(exist_ok=True, parents=True)
        
        try:
            # Save uploaded files
            students_file = None
            timetable_file = None
            photos_zip = None
            
            if 'students' in request.files:
                students_file = request.files['students']
                if students_file.filename:
                    students_path = work_dir / 'students.xlsx'
                    students_file.save(students_path)
            
            if 'timetable' in request.files:
                timetable_file = request.files['timetable']
                if timetable_file.filename:
                    timetable_path = work_dir / 'timetable.xlsx'
                    timetable_file.save(timetable_path)
            
            photos_uploaded = False
            photos_dir = None  # Initialize to None
            # Only process photos if photo box is enabled
            if show_photo_box and 'photos' in request.files:
                photos_zip = request.files['photos']
                if photos_zip.filename:
                    photos_uploaded = True
                    photos_zip_path = work_dir / 'photos.zip'
                    photos_zip.save(photos_zip_path)
                    # Extract photos
                    photos_dir = work_dir / 'photos'
                    photos_dir.mkdir(exist_ok=True)
                    with zipfile.ZipFile(photos_zip_path, 'r') as zip_ref:
                        zip_ref.extractall(photos_dir)
            else:
                # Photo box is disabled - explicitly skip photo processing
                logger.info(f"Photo box is disabled (show_photo_box={show_photo_box}), skipping all photo processing")
                photos_dir = None
            
            # Save logo and signature if provided
            logo_file_path = None
            if logo_path and logo_path.filename:
                logo_file_path = work_dir / 'logo.png'
                logo_path.save(logo_file_path)
            
            signature_file_path = None
            if signature_path and signature_path.filename:
                # Preserve original extension or default to .png
                original_ext = Path(signature_path.filename).suffix.lower()
                if original_ext in ['.png', '.jpg', '.jpeg']:
                    signature_file_path = work_dir / f'signature{original_ext}'
                else:
                    signature_file_path = work_dir / 'signature.png'
                signature_path.save(signature_file_path)
            
            # Validate inputs
            validator = InputValidator()
            errors = []
            
            if students_file and students_file.filename:
                is_valid, errs = validator.validate_excel_file(work_dir / 'students.xlsx', "Student details")
                if not is_valid:
                    errors.extend(errs)
            
            if timetable_file and timetable_file.filename:
                is_valid, errs = validator.validate_excel_file(work_dir / 'timetable.xlsx', "Timetable")
                if not is_valid:
                    errors.extend(errs)
            
            if errors:
                return jsonify({'error': 'Validation failed', 'details': errors}), 400
            
            # Setup school configuration
            school_config = SchoolConfig(
                school_name=school_name,
                school_address=school_address,
                logo_path=str(logo_file_path) if logo_file_path else None,
                signature_path=str(signature_file_path) if signature_file_path else None,
                examination_name=examination_name if examination_name else None,
                examination_timing=examination_timing,
                show_photo_box=show_photo_box
            )
            
            # Validate files exist before processing
            students_excel = work_dir / 'students.xlsx'
            timetable_excel = work_dir / 'timetable.xlsx'
            
            if not students_excel.exists():
                return jsonify({'error': 'Students Excel file not found after upload'}), 400
            if not timetable_excel.exists():
                return jsonify({'error': 'Timetable Excel file not found after upload'}), 400
            
            # Only require photos directory if photo box is enabled AND photos were uploaded
            print(f"[DEBUG] Photo validation check: show_photo_box={show_photo_box} (type: {type(show_photo_box)}), photos_uploaded={photos_uploaded}, photos_dir={photos_dir}", flush=True)
            logger.info(f"Photo validation check: show_photo_box={show_photo_box} (type: {type(show_photo_box)}), photos_uploaded={photos_uploaded}, photos_dir={photos_dir}")
            
            # CRITICAL: If photo box is disabled, skip ALL photo validation
            # Use explicit boolean check to avoid any edge cases
            is_photo_box_disabled = (show_photo_box is False or show_photo_box == False or not bool(show_photo_box))
            print(f"[DEBUG] is_photo_box_disabled check: {is_photo_box_disabled}", flush=True)
            print(f"[DEBUG] show_photo_box={show_photo_box}, type={type(show_photo_box)}, bool={bool(show_photo_box)}", flush=True)
            
            if is_photo_box_disabled:
                # Photo box is disabled - skip all photo-related validation completely
                print(f"[DEBUG] Photo box is DISABLED - SKIPPING ALL PHOTO VALIDATION", flush=True)
                logger.info(f"Photo box is DISABLED (show_photo_box={show_photo_box}, type={type(show_photo_box)}), completely skipping all photo validation and processing")
                photos_dir = None
                photos_uploaded = False  # Ensure this is also False
                # Skip to end of photo validation - do not check photos_dir at all
                print(f"[DEBUG] After setting photos_dir=None, photos_uploaded=False", flush=True)
            elif bool(show_photo_box) and photos_uploaded:
                # Photo box is enabled and photos were uploaded - validate directory exists
                print(f"[ERROR] ENTERED PHOTO VALIDATION BLOCK - THIS SHOULD NOT HAPPEN IF PHOTO BOX IS OFF!", flush=True)
                print(f"[ERROR] show_photo_box={show_photo_box}, photos_uploaded={photos_uploaded}", flush=True)
                print(f"[DEBUG] Photo box ENABLED and photos uploaded - validating photos directory: {photos_dir}")
                logger.info(f"Photo box enabled and photos uploaded - validating photos directory: {photos_dir}")
                if photos_dir is None:
                    print(f"[ERROR] Photos directory is None but photos_uploaded is True. This should not happen.", flush=True)
                    logger.error(f"Photos directory is None but photos_uploaded is True. This should not happen.")
                    return jsonify({'error': 'Photos directory not found after extraction'}), 400
                if not photos_dir.exists():
                    print(f"[ERROR] Photos directory does not exist: {photos_dir}", flush=True)
                    logger.error(f"Photos directory does not exist: {photos_dir}")
                    return jsonify({'error': 'Photos directory not found after extraction'}), 400
                if not photos_dir.is_dir():
                    print(f"[ERROR] Photos path exists but is not a directory: {photos_dir}", flush=True)
                    logger.error(f"Photos path exists but is not a directory: {photos_dir}")
                    return jsonify({'error': 'Photos directory not found after extraction'}), 400
                print(f"[DEBUG] Photos directory validation passed: {photos_dir}")
                logger.info(f"Photos directory validation passed: {photos_dir}")
            elif show_photo_box and not photos_uploaded:
                # Photo box is enabled but no photos file was uploaded
                logger.warning(f"Photo box is enabled but no photos file was uploaded")
                return jsonify({'error': 'Photo box is enabled but no photos file was uploaded. Please upload a photos ZIP file or disable the photo box.'}), 400
            
            logger.info(f"Processing files: students={students_excel.exists()}, timetable={timetable_excel.exists()}, photos={photos_dir.exists() if (show_photo_box and photos_dir) else 'N/A (photo box disabled)'}")
            
            # Initialize components
            student_reader = StudentDetailsReader(str(students_excel))
            timetable_reader = TimetableReader(str(timetable_excel))
            photo_loader = PhotoLoader(str(photos_dir)) if (show_photo_box and photos_dir) else None
            pdf_generator = HallTicketGenerator(school_config)
            
            # Read all classes
            try:
                classes_data = student_reader.read_all_classes()
                logger.info(f"Read {len(classes_data)} classes from student Excel")
                if not classes_data:
                    return jsonify({'error': 'No classes found in student Excel file. Make sure sheets are named with class names.'}), 400
            except Exception as e:
                logger.error(f"Error reading student Excel: {str(e)}", exc_info=True)
                return jsonify({'error': f'Error reading student Excel: {str(e)}'}), 400
            
            try:
                timetables_data = timetable_reader.read_timetable()
                logger.info(f"Read {len(timetables_data)} timetables from timetable Excel")
            except Exception as e:
                logger.error(f"Error reading timetable Excel: {str(e)}", exc_info=True)
                return jsonify({'error': f'Error reading timetable Excel: {str(e)}'}), 400
            
            # Process each class
            output_dir = work_dir / 'output'
            output_dir.mkdir(exist_ok=True)
            
            generated_files = []
            for class_name, students_df in classes_data.items():
                logger.info(f"Processing class: {class_name} with {len(students_df)} students")
                # Get timetable for this class - match by sheet name
                timetable_df = timetables_data.get(class_name)
                if timetable_df is None:
                    logger.warning(f"No timetable found for class '{class_name}'. Available timetable sheets: {list(timetables_data.keys())}")
                    # If only one timetable sheet exists, use it for all classes
                    if len(timetables_data) == 1:
                        timetable_df = list(timetables_data.values())[0]
                        logger.info(f"Using single timetable sheet for class {class_name}")
                
                if timetable_df is None:
                    logger.warning(f"No timetable data available for class {class_name}, creating empty timetable")
                    timetable_df = pd.DataFrame(columns=['subject', 'date', 'time', 'venue'])
                else:
                    logger.info(f"Found timetable for class {class_name} with {len(timetable_df)} rows and columns: {list(timetable_df.columns)}")
                
                # Process class (inline implementation to avoid import issues)
                # Find column names - handle various formats including "Roll No." with period
                name_col = StudentDetailsReader.find_column(students_df, [
                    "name", "student name", "student_name", "studentname", "full name", "fullname"
                ])
                roll_col = StudentDetailsReader.find_column(students_df, [
                    "roll no", "roll no.", "roll number", "roll_number", "roll", "rollno", 
                    "rollnumber", "rollno.", "rollnumber."
                ])
                admission_col = StudentDetailsReader.find_column(students_df, [
                    "admn no", "admn no.", "admission no", "admission no.", "admission number",
                    "admission_number", "admn number", "admnnumber", "admissionno", "admissionno."
                ])
                
                logger.info(f"Class {class_name}: Found columns - name: {name_col}, roll: {roll_col}, admission: {admission_col}")
                logger.info(f"Available columns: {list(students_df.columns)}")
                
                if not name_col or not roll_col:
                    error_msg = f"Required columns not found in class {class_name}. Found columns: {list(students_df.columns)}"
                    logger.error(error_msg)
                    return jsonify({'error': error_msg}), 400
                
                # Prepare student data
                students_data = []
                student_photos = {}
                student_roll_numbers = []
                
                for _, row in students_df.iterrows():
                    name = str(row[name_col]).strip()
                    roll_number = str(row[roll_col]).strip()
                    admission_number = str(row[admission_col]).strip() if admission_col else None
                    
                    if not name or not roll_number or name == 'nan' or roll_number == 'nan':
                        continue
                    
                    # Clean admission number
                    if admission_number and (admission_number == 'nan' or admission_number == 'None'):
                        admission_number = None
                    
                    student_data = {
                        'name': name,
                        'roll_number': roll_number,
                        'class': class_name,
                        'admission_number': admission_number
                    }
                    students_data.append(student_data)
                    student_roll_numbers.append(roll_number)
                    
                    # Load student photo only if photo box is enabled
                    if show_photo_box and photo_loader:
                        photo = photo_loader.load_photo(class_name, roll_number)
                        student_photos[roll_number] = photo
                    else:
                        student_photos[roll_number] = None
                
                if not students_data:
                    error_msg = f"No valid students found in class {class_name}. Please check your student data."
                    logger.warning(error_msg)
                    return jsonify({'error': error_msg}), 400
                
                logger.info(f"Prepared {len(students_data)} students for class {class_name}")
                
                # Parse timetable data - handle horizontal format (dates as columns)
                timetable_dict = {}
                
                # Check if timetable is in horizontal format (dates as column headers)
                # Look for date-like column names (DD/MM/YYYY format)
                date_columns = []
                first_col = timetable_df.columns[0] if len(timetable_df.columns) > 0 else None
                
                logger.info(f"Timetable columns: {list(timetable_df.columns)}")
                logger.info(f"Timetable shape: {timetable_df.shape}")
                logger.info(f"First few rows:\n{timetable_df.head()}")
                
                # Check if columns look like dates - multiple formats
                for col in timetable_df.columns:
                    col_str = str(col).strip()
                    # Skip first column if it's a label like "Date" or empty
                    if col == first_col and (col_str.lower() in ['date', ''] or 'unnamed' in col_str.lower()):
                        continue
                    
                    # Check if column is a datetime object (Excel might convert dates)
                    if isinstance(col, pd.Timestamp) or 'datetime' in str(type(col)).lower():
                        date_columns.append(col)
                        continue
                    
                    # Check if column is an Excel serial date number (e.g., 46025, 46026)
                    # Excel serial dates are typically 5-digit numbers (dates from 2000s)
                    try:
                        if col_str.isdigit() and len(col_str) >= 4:
                            col_num = float(col_str)
                            # Excel serial dates: 1 = Jan 1, 1900, so dates from 2000s are ~36000-50000
                            # Check if it's in a reasonable date range (1900-2100)
                            if 1 <= col_num <= 100000:
                                # Likely an Excel serial date
                                date_columns.append(col)
                                logger.debug(f"Detected Excel serial date: {col_str} -> {col}")
                                continue
                    except (ValueError, TypeError):
                        pass
                    
                    # Check if column looks like a date string (DD/MM/YYYY or DD-MM-YYYY)
                    if '/' in col_str or '-' in col_str:
                        if any(c.isdigit() for c in col_str):
                            # Try to parse as date
                            parts = col_str.replace('-', '/').split('/')
                            if len(parts) == 3:
                                # Check if all parts are digits or if it's a valid date format
                                try:
                                    # Try to validate as date
                                    if all(p.isdigit() for p in parts):
                                        date_columns.append(col)
                                    # Also check if it's a date-like string (e.g., "03/01/2026")
                                    elif len(parts[0]) <= 2 and len(parts[1]) <= 2 and len(parts[2]) == 4:
                                        date_columns.append(col)
                                except:
                                    pass
                
                # If no date columns found in headers, check first row (dates might be in first data row)
                if not date_columns and len(timetable_df) > 0:
                    logger.info("No dates in column headers, checking first row for dates...")
                    first_row = timetable_df.iloc[0]
                    for idx, val in enumerate(first_row):
                        if idx == 0:  # Skip first column (label)
                            continue
                        val_str = str(val).strip()
                        
                        # Check if value is an Excel serial date number
                        try:
                            if val_str.replace('.', '').isdigit():
                                val_num = float(val_str)
                                if 1 <= val_num <= 100000:  # Likely Excel serial date
                                    col_name = timetable_df.columns[idx]
                                    if col_name not in date_columns:
                                        date_columns.append(col_name)
                                        logger.info(f"Found Excel serial date in first row, column: {col_name}, value: {val_str}")
                                        continue
                        except (ValueError, TypeError):
                            pass
                        
                        # Check if value looks like a date string
                        if ('/' in val_str or '-' in val_str) and any(c.isdigit() for c in val_str):
                            parts = val_str.replace('-', '/').split('/')
                            if len(parts) == 3 and all(p.isdigit() for p in parts):
                                # This column might contain dates - use column name or index
                                col_name = timetable_df.columns[idx]
                                if col_name not in date_columns:
                                    date_columns.append(col_name)
                                    logger.info(f"Found date in first row, column: {col_name}, value: {val_str}")
                
                logger.info(f"Found {len(date_columns)} date columns: {date_columns[:5]}...")
                
                # Fallback: If no date columns detected but we have data, assume all columns except first are dates
                if not date_columns and len(timetable_df.columns) > 1:
                    logger.warning("No date columns detected. Using fallback: treating all columns (except first) as date columns.")
                    date_columns = [col for col in timetable_df.columns[1:] if col != first_col]
                    logger.info(f"Using {len(date_columns)} columns as date columns: {date_columns[:5]}...")
                
                if date_columns:
                    # Horizontal format: dates are columns
                    logger.info(f"Detected horizontal timetable format with {len(date_columns)} date columns")
                    
                    # Find Day and Subject rows
                    # After reading with header=0, row 1 (index 0) should be Days, row 2 (index 1) should be Subjects
                    day_row_idx = None
                    subject_row_idx = None
                    
                    # Check all rows for Day/Subject labels
                    for idx, row in timetable_df.iterrows():
                        first_cell = str(row.iloc[0]).strip().lower() if len(row) > 0 else ''
                        logger.debug(f"Row {idx}, first cell: '{first_cell}'")
                        if 'day' in first_cell and day_row_idx is None:
                            day_row_idx = idx
                            logger.info(f"Found Day row at index {idx}")
                        elif 'subject' in first_cell and subject_row_idx is None:
                            subject_row_idx = idx
                            logger.info(f"Found Subject row at index {idx}")
                    
                    # If not found by label, assume row 0 = Day, row 1 = Subject (common format)
                    if day_row_idx is None and len(timetable_df) > 0:
                        day_row_idx = 0
                        logger.info(f"Assuming Day row at index 0 (first data row)")
                    if subject_row_idx is None and len(timetable_df) > 1:
                        subject_row_idx = 1
                        logger.info(f"Assuming Subject row at index 1 (second data row)")
                    
                    # Extract dates, days, and subjects
                    exams = []
                    for date_col in date_columns:
                        # Handle date column - could be string, datetime object, or Excel serial number
                        date_str = None
                        
                        # Check if it's a datetime object
                        if isinstance(date_col, pd.Timestamp):
                            # Convert datetime to DD/MM/YYYY format
                            date_str = date_col.strftime('%d/%m/%Y')
                        else:
                            col_str = str(date_col).strip()
                            
                            # Check if it's an Excel serial date number
                            try:
                                if col_str.isdigit() or (col_str.replace('.', '').isdigit()):
                                    col_num = float(col_str)
                                    # Excel serial date: convert to datetime
                                    # Excel epoch: January 1, 1900 (but Excel incorrectly treats 1900 as leap year)
                                    # So we use: datetime(1899, 12, 30) + timedelta(days=col_num)
                                    from datetime import datetime, timedelta
                                    excel_epoch = datetime(1899, 12, 30)
                                    date_obj = excel_epoch + timedelta(days=int(col_num))
                                    date_str = date_obj.strftime('%d/%m/%Y')
                                    logger.debug(f"Converted Excel serial {col_str} to date: {date_str}")
                            except (ValueError, TypeError, OverflowError):
                                pass
                            
                            # If not a serial number, treat as string
                            if date_str is None:
                                date_str = col_str
                                # If date_str looks like a datetime string, try to format it
                                try:
                                    # Try parsing as datetime
                                    if ' ' in date_str:
                                        date_str = date_str.split(' ')[0]  # Take date part only
                                    # Convert to DD/MM/YYYY if needed
                                    if '-' in date_str and '/' not in date_str:
                                        parts = date_str.split('-')
                                        if len(parts) == 3:
                                            date_str = '/'.join(parts)
                                except:
                                    pass
                        
                        # Get day from day row
                        day = ''
                        if day_row_idx is not None:
                            try:
                                day_val = timetable_df.loc[day_row_idx, date_col]
                                day = str(day_val).strip() if pd.notna(day_val) else ''
                            except Exception as e:
                                logger.warning(f"Error getting day for column {date_col}: {e}")
                        
                        # Get subject from subject row
                        subject = ''
                        if subject_row_idx is not None:
                            try:
                                subject_val = timetable_df.loc[subject_row_idx, date_col]
                                subject = str(subject_val).strip() if pd.notna(subject_val) else 'N/A'
                            except Exception as e:
                                logger.warning(f"Error getting subject for column {date_col}: {e}")
                        
                        if date_str and date_str != 'nan' and date_str.lower() != 'none':
                            exam_data = {
                                'date': date_str,
                                'day': day,
                                'subject': subject,
                                'time': 'N/A',  # Time not in horizontal format
                                'venue': 'N/A'  # Venue not in horizontal format
                            }
                            exams.append(exam_data)
                            logger.debug(f"Added exam: date={date_str}, day={day}, subject={subject}")
                    
                    # Assign same timetable to all students in the class
                    for roll_num in student_roll_numbers:
                        timetable_dict[str(roll_num)] = exams if len(exams) > 1 else (exams[0] if exams else None)
                    
                    logger.info(f"Parsed {len(exams)} exams from horizontal timetable format for class {class_name}")
                    logger.debug(f"Sample exam data: {exams[0] if exams else 'No exams'}")
                    logger.debug(f"Timetable dict keys (roll numbers): {list(timetable_dict.keys())[:5]}...")  # Show first 5
                else:
                    # Vertical format: try to find roll number column
                    roll_col_tt = StudentDetailsReader.find_column(timetable_df, ["roll number", "roll_number", "roll", "roll no"])
                    
                    if roll_col_tt:
                        # Timetable has roll number column - match directly
                        for _, row in timetable_df.iterrows():
                            roll_num = str(row[roll_col_tt]).strip()
                            if roll_num in [str(rn).strip() for rn in student_roll_numbers]:
                                subject_col = StudentDetailsReader.find_column(timetable_df, ["subject", "subjects"])
                                date_col = StudentDetailsReader.find_column(timetable_df, ["date", "exam date"])
                                time_col = StudentDetailsReader.find_column(timetable_df, ["time", "exam time"])
                                venue_col = StudentDetailsReader.find_column(timetable_df, ["venue", "hall", "location"])
                                
                                exam_data = {
                                    'subject': row[subject_col] if subject_col else 'N/A',
                                    'date': row[date_col] if date_col else 'N/A',
                                    'time': row[time_col] if time_col else 'N/A',
                                    'venue': row[venue_col] if venue_col else 'N/A'
                                }
                                
                                if roll_num in timetable_dict:
                                    if not isinstance(timetable_dict[roll_num], list):
                                        timetable_dict[roll_num] = [timetable_dict[roll_num]]
                                    timetable_dict[roll_num].append(exam_data)
                                else:
                                    timetable_dict[roll_num] = exam_data
                    else:
                        # No roll number column - try vertical format with date/subject columns
                        subject_col = StudentDetailsReader.find_column(timetable_df, ["subject", "subjects"])
                        date_col = StudentDetailsReader.find_column(timetable_df, ["date", "exam date"])
                        time_col = StudentDetailsReader.find_column(timetable_df, ["time", "exam time"])
                        venue_col = StudentDetailsReader.find_column(timetable_df, ["venue", "hall", "location"])
                        
                        if date_col and subject_col:
                            # Vertical format with date and subject columns
                            exams = []
                            for _, row in timetable_df.iterrows():
                                exam_data = {
                                    'subject': str(row[subject_col]).strip() if subject_col and pd.notna(row[subject_col]) else 'N/A',
                                    'date': str(row[date_col]).strip() if date_col and pd.notna(row[date_col]) else 'N/A',
                                    'time': str(row[time_col]).strip() if time_col and pd.notna(row[time_col]) else 'N/A',
                                    'venue': str(row[venue_col]).strip() if venue_col and pd.notna(row[venue_col]) else 'N/A'
                                }
                                exams.append(exam_data)
                            
                            # Assign same timetable to all students
                            for roll_num in student_roll_numbers:
                                timetable_dict[str(roll_num)] = exams if len(exams) > 1 else (exams[0] if exams else None)
                        else:
                            logger.warning(f"Could not parse timetable format for class {class_name}. No date columns or date/subject columns found.")
                
                # Generate PDF
                pdf_path = output_dir / f"{class_name}.pdf"
                try:
                    logger.info(f"Generating PDF for {class_name} with {len(students_data)} students...")
                    pdf_generator.generate_pdf(
                        str(pdf_path),
                        students_data,
                        student_photos,
                        timetable_dict
                    )
                    
                    # Wait a moment for file to be written
                    import time
                    time.sleep(0.5)
                    
                    if pdf_path.exists():
                        pdf_size = pdf_path.stat().st_size
                        if pdf_size > 0:
                            generated_files.append(str(pdf_path))
                            logger.info(f"✓ Generated PDF for {class_name}: {pdf_size} bytes")
                        else:
                            error_msg = f"PDF file created but is empty for {class_name}"
                            logger.error(error_msg)
                            return jsonify({'error': error_msg}), 500
                    else:
                        error_msg = f"PDF file was not created for {class_name}"
                        logger.error(error_msg)
                        return jsonify({'error': error_msg}), 500
                except Exception as e:
                    error_msg = f"Error generating PDF for {class_name}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    return jsonify({'error': error_msg}), 500
            
            # Check if any PDFs were generated
            if not generated_files:
                error_details = []
                error_details.append(f"Processed {len(classes_data)} class(es) but no PDFs were generated.")
                error_details.append("Possible issues:")
                error_details.append("- Check that student Excel has 'Name' and 'Roll Number' columns")
                error_details.append("- Verify student data is not empty")
                error_details.append("- Check backend logs for specific errors")
                
                logger.error("No PDFs generated. Summary:")
                logger.error(f"  Classes processed: {len(classes_data)}")
                logger.error(f"  PDFs generated: {len(generated_files)}")
                
                return jsonify({
                    'error': 'No PDF files were generated.',
                    'details': error_details,
                    'classes_processed': len(classes_data),
                    'pdfs_generated': len(generated_files)
                }), 400
            
            # Create zip file of all PDFs
            zip_path = work_dir / 'hall_tickets.zip'
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for pdf_file in generated_files:
                        pdf_path = Path(pdf_file)
                        if pdf_path.exists() and pdf_path.stat().st_size > 0:
                            zipf.write(pdf_file, pdf_path.name)
                            logger.info(f"Added {pdf_path.name} to ZIP ({pdf_path.stat().st_size} bytes)")
                        else:
                            logger.warning(f"Skipping {pdf_file} - file doesn't exist or is empty")
                
                # Verify ZIP file was created and has content
                if not zip_path.exists():
                    raise Exception("ZIP file was not created")
                
                zip_size = zip_path.stat().st_size
                if zip_size == 0:
                    raise Exception("ZIP file is empty")
                
                logger.info(f"Created ZIP file: {zip_path} ({zip_size} bytes, {len(generated_files)} files)")
                
                # Verify ZIP file is readable
                try:
                    with zipfile.ZipFile(zip_path, 'r') as test_zip:
                        file_list = test_zip.namelist()
                        logger.info(f"ZIP file contains {len(file_list)} files: {file_list}")
                        if len(file_list) == 0:
                            raise Exception("ZIP file is empty - no files inside")
                except Exception as e:
                    logger.error(f"ZIP file verification failed: {str(e)}")
                    return jsonify({'error': f'ZIP file is corrupted or empty: {str(e)}'}), 500
                
                # Send the file
                return send_file(
                    str(zip_path),
                    mimetype='application/zip',
                    as_attachment=True,
                    download_name='hall_tickets.zip',
                    conditional=True
                )
            except Exception as e:
                logger.error(f"Error creating ZIP file: {str(e)}", exc_info=True)
                return jsonify({'error': f'Error creating ZIP file: {str(e)}'}), 500
        
        finally:
            # Cleanup will happen after file is sent
            pass
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"[EXCEPTION] Top-level exception caught: {error_msg}", flush=True)
        print(f"[EXCEPTION] Exception type: {type(e)}", flush=True)
        print(f"[EXCEPTION] Traceback:\n{traceback.format_exc()}", flush=True)
        sys.stdout.write(f"[EXCEPTION] Error: {error_msg}\n")
        sys.stdout.write(f"[EXCEPTION] Type: {type(e)}\n")
        sys.stdout.write(f"[EXCEPTION] Traceback:\n{traceback.format_exc()}\n")
        sys.stdout.flush()
        logger.error(f"Error generating hall tickets: {str(e)}", exc_info=True)
        # Check if this is the photos directory error
        if 'Photos directory' in error_msg or 'photos' in error_msg.lower():
            print(f"[EXCEPTION] THIS IS A PHOTOS DIRECTORY ERROR!", flush=True)
            sys.stdout.write("[EXCEPTION] THIS IS A PHOTOS DIRECTORY ERROR!\n")
            sys.stdout.flush()
        return jsonify({'error': str(e)}), 500


@app.route('/api/cleanup/<request_id>', methods=['DELETE'])
def cleanup(request_id):
    """Clean up temporary files for a request."""
    try:
        work_dir = UPLOAD_FOLDER / request_id
        if work_dir.exists():
            shutil.rmtree(work_dir)
        return jsonify({'status': 'cleaned'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Serve static files in production
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve React frontend in production."""
    if path != "" and os.path.exists(os.path.join('../frontend/dist', path)):
        return send_from_directory('../frontend/dist', path)
    else:
        return send_from_directory('../frontend/dist', 'index.html')


if __name__ == '__main__':
    # In development, only run API
    # In production, serve both API and frontend
    import os
    # Use 5001 by default since 5000 is often used by AirPlay on macOS
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting Flask server on http://0.0.0.0:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)
