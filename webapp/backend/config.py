"""
Configuration module for school details and hall ticket settings.
"""
from pathlib import Path
from typing import Optional, Tuple, List


class SchoolConfig:
    """Configuration class for school details and assets."""
    
    def __init__(
        self,
        school_name: str = "",
        school_address: str = "",
        logo_path: Optional[str] = None,
        signature_path: Optional[str] = None,
        academic_year: Optional[str] = None,
        principal_name: Optional[str] = None,
        examination_name: Optional[str] = None,
        examination_timing: Optional[dict] = None
    ):
        """
        Initialize school configuration.
        
        Args:
            school_name: Name of the school
            school_address: Address of the school
            logo_path: Path to school logo image file
            signature_path: Path to principal signature image file
            academic_year: Academic year (e.g., "ACADEMIC YEAR 2025-26")
            principal_name: Name of the principal
            examination_name: Name of the examination (e.g., "ANNUAL EXAMINATION ADMIT CARD")
            examination_timing: Dictionary with examination timing details (optional)
        """
        self.school_name = school_name
        self.school_address = school_address
        self.logo_path = Path(logo_path) if logo_path else None
        self.signature_path = Path(signature_path) if signature_path else None
        self.academic_year = academic_year
        self.principal_name = principal_name
        self.examination_name = examination_name
        self.examination_timing = examination_timing or self._default_timing()
    
    def _default_timing(self) -> dict:
        """Return default examination timing."""
        return {
            'reporting_time': '08:30 a.m.',
            'entry_time': '08:45 a.m.',
            'cooloff_time': '09:00 a.m. to 09:15 a.m.',
            'reading_time': '09:15 a.m. to 09:30 a.m.',
            'writing_time': '09:30 a.m. to 11:30 a.m.'
        }
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.school_name:
            errors.append("School name is required")
        
        if not self.school_address:
            errors.append("School address is required")
        
        if self.logo_path and not self.logo_path.exists():
            errors.append(f"Logo file not found: {self.logo_path}")
        
        if self.signature_path and not self.signature_path.exists():
            errors.append(f"Signature file not found: {self.signature_path}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'SchoolConfig':
        """Create SchoolConfig from dictionary."""
        return cls(
            school_name=config_dict.get("school_name", ""),
            school_address=config_dict.get("school_address", ""),
            logo_path=config_dict.get("logo_path"),
            signature_path=config_dict.get("signature_path"),
            academic_year=config_dict.get("academic_year"),
            principal_name=config_dict.get("principal_name"),
            examination_name=config_dict.get("examination_name"),
            examination_timing=config_dict.get("examination_timing")
        )
