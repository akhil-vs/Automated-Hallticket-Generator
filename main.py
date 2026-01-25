#!/usr/bin/env python3
"""
Main script for automated hall ticket generation.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List

from excel_reader import StudentDetailsReader, TimetableReader
from photo_loader import PhotoLoader
from pdf_generator import HallTicketGenerator
from config import SchoolConfig
from config_loader import load_config_from_file
from validator import InputValidator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_timetable_data(timetable_df, student_roll_numbers: List[str]) -> Dict[str, Dict]:
    """
    Parse timetable DataFrame and create a dictionary mapping roll numbers to timetable data.
    Supports both horizontal format (dates as columns) and vertical format (date/subject as rows).
    
    Args:
        timetable_df: DataFrame with timetable information
        student_roll_numbers: List of student roll numbers
        
    Returns:
        Dictionary mapping roll numbers to timetable data
    """
    import pandas as pd
    timetable_dict = {}
    
    # Check if timetable is in horizontal format (dates as column headers)
    # Look for date-like column names (DD/MM/YYYY format or Excel serial numbers)
    date_columns = []
    first_col = timetable_df.columns[0] if len(timetable_df.columns) > 0 else None
    
    # Check if columns look like dates - multiple formats
    for col in timetable_df.columns:
        col_str = str(col).strip()
        # Skip first column if it's a label like "Date" or empty
        if col == first_col and (col_str.lower() in ['date', ''] or 'unnamed' in col_str.lower()):
            continue
        
        # Check if column is a datetime object
        if isinstance(col, pd.Timestamp) or 'datetime' in str(type(col)).lower():
            date_columns.append(col)
            continue
        
        # Check if column is an Excel serial date number (e.g., 46025, 46026)
        try:
            if col_str.isdigit() and len(col_str) >= 4:
                col_num = float(col_str)
                # Excel serial dates: dates from 2000s are ~36000-50000
                if 1 <= col_num <= 100000:
                    date_columns.append(col)
                    continue
        except (ValueError, TypeError):
            pass
        
        # Check if column looks like a date string (DD/MM/YYYY or DD-MM-YYYY)
        if '/' in col_str or '-' in col_str:
            if any(c.isdigit() for c in col_str):
                parts = col_str.replace('-', '/').split('/')
                if len(parts) == 3:
                    try:
                        if all(p.isdigit() for p in parts):
                            date_columns.append(col)
                        elif len(parts[0]) <= 2 and len(parts[1]) <= 2 and len(parts[2]) == 4:
                            date_columns.append(col)
                    except:
                        pass
    
    # Fallback: If no date columns detected, assume all columns except first are dates
    if not date_columns and len(timetable_df.columns) > 1:
        logger.warning("No date columns detected. Using fallback: treating all columns (except first) as date columns.")
        date_columns = [col for col in timetable_df.columns[1:] if col != first_col]
    
    if date_columns:
        # Horizontal format: dates are columns
        logger.info(f"Detected horizontal timetable format with {len(date_columns)} date columns")
        
        # Find Day and Subject rows
        day_row_idx = None
        subject_row_idx = None
        
        for idx, row in timetable_df.iterrows():
            first_cell = str(row.iloc[0]).strip().lower() if len(row) > 0 else ''
            if 'day' in first_cell:
                day_row_idx = idx
            elif 'subject' in first_cell:
                subject_row_idx = idx
        
        # Extract dates, days, and subjects
        exams = []
        from datetime import datetime, timedelta
        
        for date_col in date_columns:
            # Handle date column - could be string, datetime object, or Excel serial number
            date_str = None
            
            # Check if it's a datetime object
            if isinstance(date_col, pd.Timestamp):
                date_str = date_col.strftime('%d/%m/%Y')
            else:
                col_str = str(date_col).strip()
                
                # Check if it's an Excel serial date number
                try:
                    if col_str.isdigit() or (col_str.replace('.', '').isdigit()):
                        col_num = float(col_str)
                        # Excel serial date: convert to datetime
                        excel_epoch = datetime(1899, 12, 30)
                        date_obj = excel_epoch + timedelta(days=int(col_num))
                        date_str = date_obj.strftime('%d/%m/%Y')
                        logger.debug(f"Converted Excel serial {col_str} to date: {date_str}")
                except (ValueError, TypeError, OverflowError):
                    pass
                
                # If not a serial number, treat as string
                if date_str is None:
                    date_str = col_str
                    # Format date string if needed
                    try:
                        if ' ' in date_str:
                            date_str = date_str.split(' ')[0]
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
        
        # Assign same timetable to all students in the class
        for roll_num in student_roll_numbers:
            timetable_dict[str(roll_num)] = exams if len(exams) > 1 else (exams[0] if exams else None)
        
        logger.info(f"Parsed {len(exams)} exams from horizontal timetable format")
    else:
        # Vertical format: try to find roll number column
        roll_col = StudentDetailsReader.find_column(timetable_df, ["roll number", "roll_number", "roll", "roll no"])
        
        if roll_col:
            # Timetable has roll number column - match directly
            for _, row in timetable_df.iterrows():
                roll_num = str(row[roll_col]).strip()
                if roll_num in [str(rn).strip() for rn in student_roll_numbers]:
                    # Extract timetable information
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
                    
                    # If multiple exams per student, store as list
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
                logger.warning(f"Could not parse timetable format. No date columns or date/subject columns found.")
    
    return timetable_dict


def process_class(class_name: str, students_df, timetable_df, photo_loader: PhotoLoader,
                 pdf_generator: HallTicketGenerator, output_dir: Path):
    """
    Process a single class and generate PDF.
    
    Args:
        class_name: Name of the class
        students_df: DataFrame with student details
        timetable_df: DataFrame with timetable information
        photo_loader: PhotoLoader instance
        pdf_generator: HallTicketGenerator instance
        output_dir: Output directory for PDF files
    """
    total_students = len(students_df)
    logger.info(f"Processing {total_students} students in class: {class_name}")
    
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
    
    if not name_col or not roll_col:
        logger.error(f"Required columns not found in class {class_name}. Found columns: {list(students_df.columns)}")
        return
    
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
        
        # Load student photo
        photo = photo_loader.load_photo(class_name, roll_number)
        student_photos[roll_number] = photo
        
        if photo is None:
            logger.warning(f"Photo not found for {name} (Roll: {roll_number})")
        
        # Progress indicator for large classes
        if len(students_data) % 10 == 0:
            logger.debug(f"  Loaded {len(students_data)}/{total_students} students...")
    
    if not students_data:
        logger.warning(f"No valid students found in class {class_name}")
        return
    
    # Parse timetable data
    timetable_dict = parse_timetable_data(timetable_df, student_roll_numbers)
    
    # Generate PDF
    output_path = output_dir / f"{class_name}.pdf"
    logger.info(f"Generating PDF: {output_path}")
    
    try:
        pdf_generator.generate_pdf(
            str(output_path),
            students_data,
            student_photos,
            timetable_dict
        )
        logger.info(f"Successfully generated PDF for {class_name} with {len(students_data)} students")
    except Exception as e:
        logger.error(f"Error generating PDF for {class_name}: {str(e)}", exc_info=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate hall tickets from Excel files and student photos'
    )
    
    parser.add_argument(
        '--students',
        required=True,
        help='Path to Excel file with student details (multiple sheets, one per class)'
    )
    
    parser.add_argument(
        '--timetable',
        required=True,
        help='Path to Excel file with timetable information'
    )
    
    parser.add_argument(
        '--photos',
        required=True,
        help='Base path to folder containing class folders with student photos'
    )
    
    parser.add_argument(
        '--output',
        default='output',
        help='Output directory for generated PDF files (default: output)'
    )
    
    parser.add_argument(
        '--school-name',
        help='School name (required if --config-file not used)'
    )
    
    parser.add_argument(
        '--school-address',
        help='School address (required if --config-file not used)'
    )
    
    parser.add_argument(
        '--logo-path',
        help='Path to school logo image file (optional)'
    )
    
    parser.add_argument(
        '--signature-path',
        help='Path to principal signature image file (optional)'
    )
    
    parser.add_argument(
        '--examination-name',
        help='Name of the examination (e.g., "ANNUAL EXAMINATION ADMIT CARD") (optional)'
    )
    
    parser.add_argument(
        '--config-file',
        help='Path to JSON/YAML configuration file with school details (overrides command-line arguments)'
    )
    
    args = parser.parse_args()
    
    # Validate that either config file or required args are provided
    if not args.config_file:
        if not args.school_name or not args.school_address:
            parser.error("Either --config-file must be provided, or both --school-name and --school-address are required")
    
    # Validate inputs
    students_path = Path(args.students)
    timetable_path = Path(args.timetable)
    photos_path = Path(args.photos)
    output_dir = Path(args.output)
    
    validator = InputValidator()
    all_errors = []
    
    # Validate Excel files
    is_valid, errors = validator.validate_excel_file(students_path, "Student details")
    if not is_valid:
        all_errors.extend(errors)
    
    is_valid, errors = validator.validate_excel_file(timetable_path, "Timetable")
    if not is_valid:
        all_errors.extend(errors)
    
    # Validate photos directory
    is_valid, errors = validator.validate_photos_directory(photos_path)
    if not is_valid:
        all_errors.extend(errors)
    
    # Validate image files if provided
    if args.logo_path:
        is_valid, errors = validator.validate_image_file(Path(args.logo_path), "Logo")
        if not is_valid:
            all_errors.extend(errors)
    
    if args.signature_path:
        is_valid, errors = validator.validate_image_file(Path(args.signature_path), "Signature")
        if not is_valid:
            all_errors.extend(errors)
    
    if all_errors:
        logger.error("Input validation failed:")
        for error in all_errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup school configuration
    if args.config_file:
        # Load from config file
        try:
            school_config = load_config_from_file(args.config_file)
            if school_config is None:
                logger.error(f"Could not load configuration from {args.config_file}")
                sys.exit(1)
            logger.info(f"Loaded configuration from {args.config_file}")
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
            sys.exit(1)
    else:
        # Use command-line arguments
        school_config = SchoolConfig(
            school_name=args.school_name,
            school_address=args.school_address,
            logo_path=args.logo_path,
            signature_path=args.signature_path,
            examination_name=args.examination_name
        )
    
    is_valid, errors = school_config.validate()
    if not is_valid:
        for error in errors:
            logger.warning(error)
    
    # Initialize components
    try:
        student_reader = StudentDetailsReader(str(students_path))
        timetable_reader = TimetableReader(str(timetable_path))
        photo_loader = PhotoLoader(str(photos_path))
        pdf_generator = HallTicketGenerator(school_config)
    except Exception as e:
        logger.error(f"Error initializing components: {str(e)}", exc_info=True)
        sys.exit(1)
    
    # Read all classes
    try:
        classes_data = student_reader.read_all_classes()
        timetables_data = timetable_reader.read_timetable()
    except Exception as e:
        logger.error(f"Error reading Excel files: {str(e)}", exc_info=True)
        sys.exit(1)
    
    logger.info(f"Found {len(classes_data)} classes in student details file")
    
    # Validate student data columns
    validation_errors = []
    for class_name, students_df in classes_data.items():
        is_valid, errors = validator.validate_student_columns(students_df, class_name)
        if not is_valid:
            validation_errors.extend(errors)
    
    if validation_errors:
        logger.error("Student data validation failed:")
        for error in validation_errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    # Process each class
    total_classes = len(classes_data)
    for class_idx, (class_name, students_df) in enumerate(classes_data.items(), 1):
        logger.info(f"Processing class {class_idx}/{total_classes}: {class_name}")
        # Get timetable for this class
        try:
            timetable_df = timetables_data.get(class_name)
            if timetable_df is None:
                # Try to get from single sheet or find by class column
                if len(timetables_data) == 1:
                    timetable_df = list(timetables_data.values())[0]
                else:
                    logger.warning(f"No timetable found for class {class_name}, using empty timetable")
                    timetable_df = None
        except Exception as e:
            logger.warning(f"Error getting timetable for {class_name}: {e}")
            timetable_df = None
        
        if timetable_df is None:
            # Create empty DataFrame with expected columns
            import pandas as pd
            timetable_df = pd.DataFrame(columns=['subject', 'date', 'time', 'venue'])
        
        process_class(
            class_name,
            students_df,
            timetable_df,
            photo_loader,
            pdf_generator,
            output_dir
        )
    
    logger.info("Hall ticket generation completed!")


if __name__ == '__main__':
    main()
