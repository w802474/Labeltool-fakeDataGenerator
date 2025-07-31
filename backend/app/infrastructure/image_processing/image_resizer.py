"""
Image resizing utilities for OCR processing.
"""
import cv2
import numpy as np
from typing import Tuple
from loguru import logger


class ImageResizer:
    """Handles image resizing for OCR processing while maintaining aspect ratio."""
    
    def __init__(self, target_size: int = 1280):
        """
        Initialize image resizer with target size.
        
        Args:
            target_size: Maximum dimension (width or height) for the resized image.
                        Default 1280 is a balanced choice for PaddleOCR 3.1.
        """
        self.target_size = target_size
        logger.info(f"ImageResizer initialized with target_size={target_size}")
    
    def calculate_resize_params(self, original_width: int, original_height: int) -> Tuple[int, int, float]:
        """
        Calculate resize parameters maintaining aspect ratio.
        
        Args:
            original_width: Original image width
            original_height: Original image height
            
        Returns:
            Tuple of (new_width, new_height, scale_factor)
        """
        # Check if resizing is needed
        max_dim = max(original_width, original_height)
        
        if max_dim <= self.target_size:
            # No resizing needed
            return original_width, original_height, 1.0
        
        # Calculate scale factor to fit within target size
        scale_factor = self.target_size / max_dim
        
        # Calculate new dimensions
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Ensure dimensions are even (some OCR models prefer even dimensions)
        new_width = new_width if new_width % 2 == 0 else new_width - 1
        new_height = new_height if new_height % 2 == 0 else new_height - 1
        
        logger.info(f"Resize calculated: {original_width}x{original_height} -> {new_width}x{new_height} (scale={scale_factor:.3f})")
        
        return new_width, new_height, scale_factor
    
    def resize_image_for_ocr(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Resize image for OCR processing while maintaining aspect ratio.
        
        Args:
            image: Input image as numpy array (BGR format from cv2.imread)
            
        Returns:
            Tuple of (resized_image, scale_factor)
            - resized_image: Resized image maintaining aspect ratio
            - scale_factor: Factor used for resizing (original_size * scale_factor = new_size)
        """
        if image is None:
            raise ValueError("Input image is None")
        
        original_height, original_width = image.shape[:2]
        new_width, new_height, scale_factor = self.calculate_resize_params(original_width, original_height)
        
        if scale_factor == 1.0:
            # No resizing needed
            logger.info("No resizing needed - image within target size")
            return image, 1.0
        
        # Resize using high-quality interpolation
        resized_image = cv2.resize(
            image, 
            (new_width, new_height), 
            interpolation=cv2.INTER_LANCZOS4
        )
        
        logger.info(f"Image resized from {original_width}x{original_height} to {new_width}x{new_height}")
        
        return resized_image, scale_factor
    
    def resize_image_from_path(self, image_path: str) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Load and resize image from file path.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (original_image, resized_image, scale_factor)
        """
        # Load original image
        original_image = cv2.imread(image_path)
        if original_image is None:
            raise ValueError(f"Cannot load image from path: {image_path}")
        
        # Resize for OCR
        resized_image, scale_factor = self.resize_image_for_ocr(original_image)
        
        return original_image, resized_image, scale_factor


class CoordinateScaler:
    """Handles coordinate scaling between original and resized images."""
    
    @staticmethod
    def scale_coordinates_to_original(
        coordinates: list, 
        scale_factor: float
    ) -> list:
        """
        Scale coordinates from resized image back to original image dimensions.
        
        Args:
            coordinates: List of coordinate points [[x1, y1], [x2, y2], ...]
            scale_factor: Scale factor used during resizing (resized = original * scale_factor)
            
        Returns:
            Scaled coordinates in original image space
        """
        if scale_factor == 1.0:
            return coordinates
        
        # Scale back to original size (inverse of scale_factor)
        inverse_scale = 1.0 / scale_factor
        
        scaled_coords = []
        for coord in coordinates:
            scaled_x = coord[0] * inverse_scale
            scaled_y = coord[1] * inverse_scale
            scaled_coords.append([scaled_x, scaled_y])
        
        return scaled_coords
    
    @staticmethod
    def scale_bounding_box_to_original(
        x: float, y: float, width: float, height: float, 
        scale_factor: float
    ) -> Tuple[float, float, float, float]:
        """
        Scale bounding box coordinates from resized image to original image.
        
        Args:
            x, y, width, height: Bounding box in resized image
            scale_factor: Scale factor used during resizing
            
        Returns:
            Tuple of (scaled_x, scaled_y, scaled_width, scaled_height)
        """
        if scale_factor == 1.0:
            return x, y, width, height
        
        # Scale back to original size
        inverse_scale = 1.0 / scale_factor
        
        scaled_x = x * inverse_scale
        scaled_y = y * inverse_scale
        scaled_width = width * inverse_scale
        scaled_height = height * inverse_scale
        
        return scaled_x, scaled_y, scaled_width, scaled_height