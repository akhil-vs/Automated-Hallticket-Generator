"""
Input validation utilities for hall ticket generator.
"""
from pathlib import Path
from typing import List, Tuple
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class InputValidator:
    """Validates input files and data for hall ticket generation."""
    
    @staticmethod
    def validate_excel_file(file_path: Path, file_type: str = "Excel") -> Tuple[bool, List[str]]:
        """
        Validate that an Excel file exists and is readable.
        
        Args:
            file_path: Path to Excel file
            file_type: Type description for error messages
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not file_path.exists():
            errors.append(f"{file_type} file not found: {file_path}")
            return False, errors
        
        if not file_path.suffix.lower() in ['.xlsx', '.xls']:
            errors.append(f"{file_type} file must be .xlsx or .xls format: {file_path}")
            return False, errors
        
        try:
            excel_file = pd.ExcelFile(file_path)
            if len(excel_file.sheet_names) == 0:
                errors.append(f"{file_type} file has no sheets: {file_path}")
                return False, errors
        except Exception as e:
            errors.append(f"Cannot read {file_type} file {file_path}: {str(e)}")
            return False, errors
        
        return True, errors
    
    @staticmethod
    def validate_photos_directory(photos_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate photos directory structure.
        
        Args:
            photos_path: Path to photos base directory
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not photos_path.exists():
            errors.append(f"Photos directory not found: {photos_path}")
            return False, errors
        
        if not photos_path.is_dir():
            errors.append(f"Photos path is not a directory: {photos_path}")
            return False, errors
        
        # Check if there are any subdirectories (class folders)
        subdirs = [d for d in photos_path.iterdir() if d.is_dir()]
        if len(subdirs) == 0:
            errors.append(f"No class folders found in photos directory: {photos_path}")
            return False, errors
        
        return True, errors
    
    @staticmethod
    def validate_student_columns(df: pd.DataFrame, class_name: str) -> Tuple[bool, List[str]]:
        """
        Validate that required columns exist in student DataFrame.
        
        Args:
            df: Student DataFrame
            class_name: Name of the class
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        required_columns = ['name', 'roll number']
        found_columns = [col.lower() for col in df.columns]
        
        # Check for name column
        name_found = any('name' in col for col in found_columns)
        if not name_found:
            errors.append(f"Class '{class_name}': No 'Name' column found. Available columns: {list(df.columns)}")
        
        # Check for roll number column
        roll_found = any('roll' in col for col in found_columns)
        if not roll_found:
            errors.append(f"Class '{class_name}': No 'Roll Number' column found. Available columns: {list(df.columns)}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_timetable_columns(df: pd.DataFrame, class_name: str) -> Tuple[bool, List[str]]:
        """
        Validate that timetable has expected columns.
        
        Args:
            df: Timetable DataFrame
            class_name: Name of the class
            
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        found_columns = [col.lower() for col in df.columns]
        
        # Check for common timetable columns (warnings, not errors)
        if not any('subject' in col for col in found_columns):
            warnings.append(f"Class '{class_name}': No 'Subject' column found in timetable")
        
        if not any('date' in col for col in found_columns):
            warnings.append(f"Class '{class_name}': No 'Date' column found in timetable")
        
        if not any('time' in col for col in found_columns):
            warnings.append(f"Class '{class_name}': No 'Time' column found in timetable")
        
        if not any('venue' in col or 'hall' in col or 'location' in col for col in found_columns):
            warnings.append(f"Class '{class_name}': No 'Venue' column found in timetable")
        
        return True, warnings  # Warnings don't fail validation
    
    @staticmethod
    def validate_image_file(image_path: Path, image_type: str = "Image") -> Tuple[bool, List[str]]:
        """
        Validate that an image file exists and is readable.
        
        Args:
            image_path: Path to image file
            image_type: Type description for error messages
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if image_path is None:
            return True, errors  # Optional file
        
        if not image_path.exists():
            errors.append(f"{image_type} file not found: {image_path}")
            return False, errors
        
        if not image_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            errors.append(f"{image_type} file must be PNG or JPG format: {image_path}")
            return False, errors
        
        return True, errors
