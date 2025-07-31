"""Image service port definition."""
from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.text_region import TextRegion
from app.domain.value_objects.image_file import ImageFile


class ImageServicePort(ABC):
    """Port for image processing service integration."""
    
    @abstractmethod
    async def save_uploaded_image(self, file_data: bytes, filename: str) -> ImageFile:
        """
        Save uploaded image with validation and security checks.
        
        Args:
            file_data: Raw file data bytes
            filename: Original filename
            
        Returns:
            ImageFile value object with metadata
            
        Raises:
            ValueError: If file validation fails
        """
        pass
    
    @abstractmethod
    async def create_processed_image_metadata(
        self, 
        processed_path: str, 
        original: ImageFile
    ) -> ImageFile:
        """
        Create metadata for a processed image.
        
        Args:
            processed_path: Path to the processed image
            original: Original ImageFile for reference
            
        Returns:
            ImageFile value object for processed image
        """
        pass


class InpaintingServicePort(ABC):
    """Port for image inpainting service integration."""
    
    @abstractmethod
    async def remove_text_regions(
        self, 
        image_path: str, 
        regions: List[TextRegion],
        output_dir: str = "processed"
    ) -> str:
        """
        Remove text regions from image and return path to processed image.
        
        Args:
            image_path: Path to input image
            regions: List of text regions to remove
            output_dir: Directory to save processed image
            
        Returns:
            Path to processed image file
            
        Raises:
            ValueError: If processing fails
            FileNotFoundError: If input image doesn't exist
        """
        pass
    
    @abstractmethod
    def validate_regions_for_inpainting(self, regions: List[TextRegion]) -> dict:
        """
        Validate regions and provide recommendations for inpainting.
        
        Args:
            regions: List of text regions to validate
            
        Returns:
            Dictionary with validation results and recommendations
        """
        pass