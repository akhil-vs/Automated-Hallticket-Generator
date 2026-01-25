# Automated Hall Ticket Generator

A Python application that automatically generates hall tickets for students by combining data from Excel files (student details and timetables) with student photos.

## Features

- Reads student details from Excel files with multiple sheets (one per class)
- Reads timetable information from Excel files
- **Smart photo matching**: Fuzzy matching for student photos by roll number with support for various filename formats
- **Configuration file support**: Use JSON/YAML config files for school details
- **Comprehensive validation**: Validates input files, columns, and data before processing
- **Progress indicators**: Shows progress when processing large batches
- Includes school branding: logo, name, and address
- Adds principal signature photo to each ticket
- Generates professional PDF hall tickets with 3 tickets per A4 page
- Outputs one PDF file per class

## Requirements

- Python 3.8 or higher
- See `requirements.txt` for Python dependencies

## Installation

1. Install Python dependencies:
```bash
python3 -m pip install -r requirements.txt
```

## Usage

```bash
python3 main.py --students <student_excel_path> --timetable <timetable_excel_path> --photos <photos_folder_path> --output <output_folder> --school-name "School Name" --school-address "School Address"
```

### Configuration

You can configure school details in one of the following ways:

1. **Configuration file** (recommended for repeated use):
   ```bash
   python3 main.py --config-file school_config.json --students ... --timetable ... --photos ...
   ```
   
   Create a JSON or YAML file with:
   ```json
   {
     "school_name": "Your School Name",
     "school_address": "123 School Street, City, State, ZIP",
     "logo_path": "assets/school_logo.png",
     "signature_path": "assets/principal_signature.png"
   }
   ```
   
   Use `--config-file` option to load from file. This avoids long command-line arguments.

2. **Command-line arguments**:
   - `--school-name`: School name
   - `--school-address`: School address
   - `--logo-path`: Path to school logo image (optional)
   - `--signature-path`: Path to principal signature image (optional)

### Input Files

1. **Student Details Excel**: 
   - Multiple sheets, one per class (sheet name = class name)
   - Columns: Name, Roll Number (at minimum)
   
2. **Timetable Excel**:
   - Contains exam schedule with dates, times, subjects, and venue
   - Should be organized by class

3. **Student Photos**:
   - Organized in folders by class name
   - Photo filenames should match roll numbers (e.g., "123.jpg", "456.png")

4. **School Assets** (optional):
   - School logo image (PNG/JPG)
   - Principal signature image (PNG/JPG)

### Output

Generated PDF files will be saved in the specified output folder, with one PDF per class (e.g., `Class1.pdf`, `Class2.pdf`).

## Project Structure

```
AutomatedHallticketGenerator/
├── main.py                 # Main entry point
├── excel_reader.py         # Excel reading utilities
├── photo_loader.py         # Photo loading and fuzzy matching
├── pdf_generator.py        # PDF generation with 3-per-page layout
├── config.py               # School details and configuration
├── config_loader.py        # Configuration file loader (JSON/YAML)
├── validator.py            # Input validation utilities
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── school_config.example.json  # Example configuration file
└── output/                # Generated PDF files (created at runtime)
```

## License

MIT License
