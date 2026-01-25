"""
Photo loading and matching utilities for student photos.
"""
from pathlib import Path
from typing import Optional, Dict
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class PhotoLoader:
    """Loads and matches student photos by roll number."""
    
    def __init__(self, photos_base_path: str):
        """
        Initialize photo loader with base path.
        
        Args:
            photos_base_path: Base path where class folders are located
        """
        self.photos_base_path = Path(photos_base_path)
        if not self.photos_base_path.exists():
            raise FileNotFoundError(f"Photos folder not found: {photos_base_path}")
    
    def _fuzzy_match_filename(self, target_roll: str, filename: str) -> bool:
        """
        Check if a filename matches a roll number with fuzzy matching.
        
        Args:
            target_roll: Target roll number to match
            filename: Filename to check
            
        Returns:
            True if filename likely matches roll number
        """
        # Remove extension
        name_without_ext = Path(filename).stem.lower()
        target_lower = str(target_roll).strip().lower()
        
        # Exact match
        if name_without_ext == target_lower:
            return True
        
        # Match with leading zeros
        if name_without_ext == target_lower.zfill(len(name_without_ext)):
            return True
        
        # Match without leading zeros
        if name_without_ext.lstrip('0') == target_lower.lstrip('0'):
            return True
        
        # Match if roll number is contained in filename
        if target_lower in name_without_ext or name_without_ext in target_lower:
            return True
        
        # Match if only digits differ slightly (e.g., "101" vs "0101")
        if name_without_ext.isdigit() and target_lower.isdigit():
            if int(name_without_ext) == int(target_lower):
                return True
        
        return False
    
    def get_photo_path(self, class_name: str, roll_number: str) -> Optional[Path]:
        """
        Get photo path for a student by class and roll number with fuzzy matching.
        
        Args:
            class_name: Name of the class
            roll_number: Roll number of the student
            
        Returns:
            Path to photo if found, None otherwise
        """
        class_folder = self.photos_base_path / class_name
        
        if not class_folder.exists():
            logger.warning(f"Class folder not found: {class_folder}")
            return None
        
        # Try exact matches first (fastest)
        extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
        roll_str = str(roll_number).strip()
        
        for ext in extensions:
            photo_path = class_folder / f"{roll_str}{ext}"
            if photo_path.exists():
                return photo_path
        
        # Try with leading zeros removed
        roll_clean = roll_str.lstrip('0') if roll_str.lstrip('0') else roll_str
        for ext in extensions:
            photo_path = class_folder / f"{roll_clean}{ext}"
            if photo_path.exists():
                return photo_path
        
        # Try with leading zeros added (up to 4 digits)
        for width in range(len(roll_str), 5):
            roll_padded = roll_str.zfill(width)
            for ext in extensions:
                photo_path = class_folder / f"{roll_padded}{ext}"
                if photo_path.exists():
                    return photo_path
        
        # Fuzzy match: search all image files in the folder
        roll_lower = roll_str.lower()
        image_files = []
        for ext in extensions:
            image_files.extend(list(class_folder.glob(f"*{ext}")))
            image_files.extend(list(class_folder.glob(f"*{ext.upper()}")))
        
        # Try fuzzy matching
        for img_file in image_files:
            if self._fuzzy_match_filename(roll_number, img_file.name):
                logger.info(f"Found photo using fuzzy match: {img_file.name} for roll {roll_number}")
                return img_file
        
        logger.warning(f"Photo not found for roll number {roll_number} in class {class_name}")
        return None
    
    def load_photo(self, class_name: str, roll_number: str, max_size: tuple = (200, 200)) -> Optional[Image.Image]:
        """
        Load and resize student photo.
        
        Args:
            class_name: Name of the class
            roll_number: Roll number of the student
            max_size: Maximum size (width, height) for the photo
            
        Returns:
            PIL Image object if found, None otherwise
        """
        photo_path = self.get_photo_path(class_name, roll_number)
        
        if photo_path is None:
            return None
        
        try:
            img = Image.open(photo_path)
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # Resize maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            return img
        except Exception as e:
            logger.error(f"Error loading photo {photo_path}: {str(e)}")
            return None
    
    def load_all_photos_for_class(self, class_name: str, roll_numbers: list) -> Dict[str, Optional[Image.Image]]:
        """
        Load all photos for a class.
        
        Args:
            class_name: Name of the class
            roll_numbers: List of roll numbers for the class
            
        Returns:
            Dictionary mapping roll numbers to Image objects (or None if not found)
        """
        photos = {}
        for roll_number in roll_numbers:
            photos[str(roll_number)] = self.load_photo(class_name, str(roll_number))
        return photos
    
    @staticmethod
    def load_image_file(image_path: str, max_size: Optional[tuple] = None) -> Optional[Image.Image]:
        """
        Load an image file (for logo, signature, etc.).
        
        Args:
            image_path: Path to the image file
            max_size: Optional maximum size (width, height) for resizing
            
        Returns:
            PIL Image object if found, None otherwise
        """
        path = Path(image_path)
        if not path.exists():
            logger.warning(f"Image file not found: {image_path}")
            return None
        
        try:
            img = Image.open(path)
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            if max_size:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            return img
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {str(e)}")
            return None
