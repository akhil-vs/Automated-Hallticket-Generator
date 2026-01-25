"""
Excel reading utilities for student details and timetable data.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional


class StudentDetailsReader:
    """Reads student details from Excel file with multiple sheets."""
    
    def __init__(self, excel_path: str):
        """
        Initialize reader with Excel file path.
        
        Args:
            excel_path: Path to the Excel file containing student details
        """
        self.excel_path = Path(excel_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Student details Excel file not found: {excel_path}")
    
    def read_all_classes(self) -> Dict[str, pd.DataFrame]:
        """
        Read all sheets from the Excel file.
        
        Returns:
            Dictionary mapping class names (sheet names) to DataFrames
        """
        try:
            excel_file = pd.ExcelFile(self.excel_path)
            classes_data = {}
            
            for sheet_name in excel_file.sheet_names:
                # Use row 3 (index 2) as header row - skip first 2 rows
                # Row 1 = index 0, Row 2 = index 1, Row 3 = index 2
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=2)
                except Exception:
                    # Fallback: try with header=0 if row 2 doesn't work
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=0)
                
                # Clean column names (remove extra spaces, convert to lowercase for matching)
                # Convert to strings first to handle any non-string column names
                df.columns = [str(col).strip() if col is not None and pd.notna(col) else f"Column_{i}" 
                             for i, col in enumerate(df.columns)]
                
                # Remove "Unnamed" prefix from column names
                df.columns = [col.replace('Unnamed: ', '').replace('Unnamed', '') if 'Unnamed' in col else col 
                             for col in df.columns]
                
                # Drop completely empty rows
                df = df.dropna(how='all')
                
                classes_data[sheet_name] = df
            
            return classes_data
        except Exception as e:
            raise ValueError(f"Error reading student details Excel: {str(e)}")
    
    def get_students_for_class(self, class_name: str) -> pd.DataFrame:
        """
        Get student data for a specific class.
        
        Args:
            class_name: Name of the class (sheet name)
            
        Returns:
            DataFrame with student details for the class
        """
        all_classes = self.read_all_classes()
        if class_name not in all_classes:
            raise ValueError(f"Class '{class_name}' not found in Excel file")
        return all_classes[class_name]
    
    @staticmethod
    def find_column(df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """
        Find a column by trying multiple possible names.
        
        Args:
            df: DataFrame to search
            possible_names: List of possible column names
            
        Returns:
            Column name if found, None otherwise
        """
        # Normalize column names for comparison (remove periods, extra spaces)
        normalized_cols = {col: str(col).lower().replace('.', '').replace(' ', '').strip() 
                          for col in df.columns}
        
        for name in possible_names:
            # Normalize the search name
            normalized_name = name.lower().replace('.', '').replace(' ', '').strip()
            
            # Try exact match first (case-insensitive, ignoring periods and spaces)
            for col, norm_col in normalized_cols.items():
                if norm_col == normalized_name:
                    return col
            
            # Try partial match
            for col, norm_col in normalized_cols.items():
                if normalized_name in norm_col or norm_col in normalized_name:
                    return col
        
        return None


class TimetableReader:
    """Reads timetable data from Excel file."""
    
    def __init__(self, excel_path: str):
        """
        Initialize reader with Excel file path.
        
        Args:
            excel_path: Path to the Excel file containing timetable
        """
        self.excel_path = Path(excel_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Timetable Excel file not found: {excel_path}")
    
    def read_timetable(self) -> Dict[str, pd.DataFrame]:
        """
        Read timetable data from Excel file.
        Assumes one sheet per class (similar to student details).
        
        Returns:
            Dictionary mapping class names to timetable DataFrames
        """
        try:
            excel_file = pd.ExcelFile(self.excel_path)
            timetable_data = {}
            
            for sheet_name in excel_file.sheet_names:
                # For horizontal timetable format: dates are in row 1 (header row)
                # Row 1 = dates (header), Row 2 = days, Row 3 = subjects
                # Use header=0 to make row 1 (dates) the column headers
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=0)
                except Exception:
                    # Fallback: try reading without header
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                
                # Convert column names to strings and strip whitespace
                df.columns = [str(col).strip() if col is not None and pd.notna(col) else f"Column_{i}" 
                             for i, col in enumerate(df.columns)]
                
                # Remove "Unnamed" prefix
                df.columns = [col.replace('Unnamed: ', '').replace('Unnamed', '') if 'Unnamed' in col else col 
                             for col in df.columns]
                
                # Drop empty rows
                df = df.dropna(how='all')
                
                timetable_data[sheet_name] = df
            
            return timetable_data
        except Exception as e:
            raise ValueError(f"Error reading timetable Excel: {str(e)}")
    
    def get_timetable_for_class(self, class_name: str) -> pd.DataFrame:
        """
        Get timetable data for a specific class.
        
        Args:
            class_name: Name of the class (sheet name)
            
        Returns:
            DataFrame with timetable for the class
        """
        all_timetables = self.read_timetable()
        if class_name not in all_timetables:
            # Try to find a single sheet that might contain all classes
            if len(all_timetables) == 1:
                df = list(all_timetables.values())[0]
                # Check if there's a class column to filter
                class_col = StudentDetailsReader.find_column(df, ["class", "class name", "class_name"])
                if class_col:
                    return df[df[class_col] == class_name]
                return df
            raise ValueError(f"Timetable for class '{class_name}' not found")
        return all_timetables[class_name]


def merge_student_timetable(
    students_df: pd.DataFrame,
    timetable_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge student data with timetable data.
    
    Args:
        students_df: DataFrame with student details
        timetable_df: DataFrame with timetable information
        
    Returns:
        Merged DataFrame with student and timetable information
    """
    # Find common columns for merging (if any)
    # For now, we'll return both dataframes combined conceptually
    # The actual merging logic depends on the structure of the data
    
    # If timetable has subject-wise rows, we might need to group them
    # For now, return students_df with timetable_df as additional context
    return students_df.copy()
