"""ImageFile value object for image metadata."""
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple


class Dimensions(NamedTuple):
    """Image dimensions tuple."""
    width: int
    height: int


@dataclass(frozen=True)
class ImageFile:
    """Immutable image file value object containing metadata."""
    
    id: str
    filename: str
    path: str
    mime_type: str
    size: int
    dimensions: Dimensions
    
    def __post_init__(self):
        """Validate image file properties."""
        if not self.filename:
            raise ValueError("Filename cannot be empty")
        if not self.path:
            raise ValueError("Path cannot be empty")
        if self.size <= 0:
            raise ValueError(f"Size must be positive, got {self.size}")
        if self.dimensions.width <= 0 or self.dimensions.height <= 0:
            raise ValueError(f"Invalid dimensions: {self.dimensions}")
        
        # Validate MIME type
        valid_mime_types = {'image/jpeg', 'image/png', 'image/webp'}
        if self.mime_type not in valid_mime_types:
            raise ValueError(f"Unsupported MIME type: {self.mime_type}")
    
    @property
    def file_extension(self) -> str:
        """Get the file extension from the filename."""
        return Path(self.filename).suffix.lower()
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate the aspect ratio of the image."""
        return self.dimensions.width / self.dimensions.height
    
    def is_large_image(self, threshold: int = 1920) -> bool:
        """Check if the image exceeds the given dimension threshold."""
        return max(self.dimensions.width, self.dimensions.height) > threshold
    
    @property
    def megapixels(self) -> float:
        """Calculate the image size in megapixels."""
        return (self.dimensions.width * self.dimensions.height) / 1_000_000