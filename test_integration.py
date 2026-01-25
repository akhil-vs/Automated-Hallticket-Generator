#!/usr/bin/env python3
"""
Integration test script to verify all components work together.
This creates sample data and tests the hall ticket generation pipeline.
"""
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

# Add backend directory to path
backend_dir = Path(__file__).parent / 'webapp' / 'backend'
sys.path.insert(0, str(backend_dir))

from config import SchoolConfig
from excel_reader import StudentDetailsReader, TimetableReader
from photo_loader import PhotoLoader
from pdf_generator import HallTicketGenerator


def create_sample_image(filename: Path, text: str = "Sample"):
    """Create a sample image file."""
    img = Image.new('RGB', (200, 250), color='white')
    draw = ImageDraw.Draw(img)
    # Draw a simple rectangle and text
    draw.rectangle([10, 10, 190, 240], outline='black', width=2)
    draw.text((50, 100), text, fill='black')
    img.save(filename)


def create_test_data():
    """Create temporary test data files."""
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Creating test data in: {temp_dir}")
    
    # Create sample student Excel
    students_file = temp_dir / "students.xlsx"
    with pd.ExcelWriter(students_file, engine='openpyxl') as writer:
        # Class 1
        class1_data = pd.DataFrame({
            'Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'Roll Number': ['101', '102', '103']
        })
        class1_data.to_excel(writer, sheet_name='Class1', index=False)
        
        # Class 2
        class2_data = pd.DataFrame({
            'Name': ['Alice Brown', 'Charlie Wilson'],
            'Roll Number': ['201', '202']
        })
        class2_data.to_excel(writer, sheet_name='Class2', index=False)
    
    # Create sample timetable Excel
    timetable_file = temp_dir / "timetable.xlsx"
    with pd.ExcelWriter(timetable_file, engine='openpyxl') as writer:
        # Class 1 timetable
        class1_timetable = pd.DataFrame({
            'Subject': ['Math', 'Science', 'English'],
            'Date': ['2024-01-15', '2024-01-16', '2024-01-17'],
            'Time': ['9:00 AM', '10:00 AM', '11:00 AM'],
            'Venue': ['Hall A', 'Hall B', 'Hall A']
        })
        class1_timetable.to_excel(writer, sheet_name='Class1', index=False)
        
        # Class 2 timetable
        class2_timetable = pd.DataFrame({
            'Subject': ['Math', 'Science'],
            'Date': ['2024-01-15', '2024-01-16'],
            'Time': ['9:00 AM', '10:00 AM'],
            'Venue': ['Hall C', 'Hall C']
        })
        class2_timetable.to_excel(writer, sheet_name='Class2', index=False)
    
    # Create photos directory structure
    photos_dir = temp_dir / "photos"
    photos_dir.mkdir()
    
    # Class 1 photos
    class1_photos = photos_dir / "Class1"
    class1_photos.mkdir()
    create_sample_image(class1_photos / "101.jpg", "John")
    create_sample_image(class1_photos / "102.jpg", "Jane")
    create_sample_image(class1_photos / "103.jpg", "Bob")
    
    # Class 2 photos
    class2_photos = photos_dir / "Class2"
    class2_photos.mkdir()
    create_sample_image(class2_photos / "201.jpg", "Alice")
    create_sample_image(class2_photos / "202.jpg", "Charlie")
    
    # Create school logo and signature
    logo_file = temp_dir / "logo.png"
    signature_file = temp_dir / "signature.png"
    create_sample_image(logo_file, "LOGO")
    create_sample_image(signature_file, "SIGN")
    
    # Output directory
    output_dir = temp_dir / "output"
    output_dir.mkdir()
    
    return temp_dir, students_file, timetable_file, photos_dir, logo_file, signature_file, output_dir


def test_components():
    """Test all components."""
    print("=" * 60)
    print("Testing Hall Ticket Generator Components")
    print("=" * 60)
    
    # Create test data
    temp_dir, students_file, timetable_file, photos_dir, logo_file, signature_file, output_dir = create_test_data()
    
    try:
        # Test 1: School Config
        print("\n1. Testing SchoolConfig...")
        config = SchoolConfig(
            school_name="Test School",
            school_address="123 Test Street, Test City",
            logo_path=str(logo_file),
            signature_path=str(signature_file)
        )
        is_valid, errors = config.validate()
        assert is_valid, f"Config validation failed: {errors}"
        print("   ✓ SchoolConfig created successfully")
        
        # Test 2: Excel Readers
        print("\n2. Testing Excel Readers...")
        student_reader = StudentDetailsReader(str(students_file))
        timetable_reader = TimetableReader(str(timetable_file))
        
        classes_data = student_reader.read_all_classes()
        assert len(classes_data) == 2, f"Expected 2 classes, got {len(classes_data)}"
        assert 'Class1' in classes_data and 'Class2' in classes_data
        print(f"   ✓ Found {len(classes_data)} classes")
        
        timetables_data = timetable_reader.read_timetable()
        assert len(timetables_data) == 2
        print(f"   ✓ Found {len(timetables_data)} timetables")
        
        # Test 3: Photo Loader
        print("\n3. Testing PhotoLoader...")
        photo_loader = PhotoLoader(str(photos_dir))
        photo = photo_loader.load_photo('Class1', '101')
        assert photo is not None, "Failed to load photo"
        print("   ✓ PhotoLoader working correctly")
        
        # Test 4: PDF Generator
        print("\n4. Testing PDF Generator...")
        pdf_generator = HallTicketGenerator(config)
        
        # Get sample student data
        class1_df = classes_data['Class1']
        class1_timetable = timetables_data['Class1']
        
        # Prepare student data
        students_data = []
        student_photos = {}
        student_roll_numbers = []
        
        name_col = 'Name'
        roll_col = 'Roll Number'
        
        for _, row in class1_df.iterrows():
            name = str(row[name_col])
            roll_number = str(row[roll_col])
            student_data = {
                'name': name,
                'roll_number': roll_number,
                'class': 'Class1'
            }
            students_data.append(student_data)
            student_roll_numbers.append(roll_number)
            photo = photo_loader.load_photo('Class1', roll_number)
            student_photos[roll_number] = photo
        
        # Parse timetable
        timetable_dict = {}
        for roll_num in student_roll_numbers:
            exams = []
            for _, row in class1_timetable.iterrows():
                exam_data = {
                    'subject': str(row['Subject']),
                    'date': str(row['Date']),
                    'time': str(row['Time']),
                    'venue': str(row['Venue'])
                }
                exams.append(exam_data)
            timetable_dict[roll_num] = exams
        
        # Generate PDF
        output_pdf = output_dir / "Class1_test.pdf"
        pdf_generator.generate_pdf(
            str(output_pdf),
            students_data,
            student_photos,
            timetable_dict
        )
        
        assert output_pdf.exists(), "PDF file was not created"
        print(f"   ✓ PDF generated successfully: {output_pdf}")
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        print(f"\nTest files are in: {temp_dir}")
        print(f"Generated PDF: {output_pdf}")
        print("\nYou can manually verify the PDF output.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Optionally clean up - comment out to keep test files
        # shutil.rmtree(temp_dir)
        pass


if __name__ == '__main__':
    success = test_components()
    sys.exit(0 if success else 1)
