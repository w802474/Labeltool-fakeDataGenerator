"""OCR service port definition."""
from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.text_region import TextRegion


class OCRServicePort(ABC):
    """Port for OCR service integration."""
    
    @abstractmethod
    async def detect_text_regions(self, image_path: str) -> List[TextRegion]:
        """
        Detect text regions in an image.
        
        Args:
            image_path: Path to the image file to process
            
        Returns:
            List of detected TextRegion objects
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image cannot be processed
        """
        pass
    
    @abstractmethod
    def get_device_info(self) -> dict:
        """
        Get information about OCR service device configuration.
        
        Returns:
            Dictionary with device information
        """
        pass