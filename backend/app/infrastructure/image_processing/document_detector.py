"""
Simple document type detection for automatic OCR configuration.
"""
import cv2
import numpy as np
from typing import Tuple
from loguru import logger


class DocumentDetector:
    """Lightweight document type detector using simple computer vision techniques."""
    
    def __init__(self):
        """Initialize the document detector."""
        self.logger = logger
    
    def is_document_image(self, image_path: str) -> bool:
        """
        Determine if an image is likely a document vs natural image/screenshot.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if likely a document, False otherwise
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"Cannot load image for document detection: {image_path}")
                return False
            
            height, width = image.shape[:2]
            
            # Calculate features
            aspect_ratio = self._calculate_aspect_ratio(width, height)
            edge_density = self._calculate_edge_density(image)
            color_variance = self._calculate_color_variance(image)
            
            # Log detection features for debugging
            logger.debug(f"Document detection features for {image_path}:")
            logger.debug(f"  Size: {width}x{height}")
            logger.debug(f"  Aspect ratio: {aspect_ratio:.3f}")
            logger.debug(f"  Edge density: {edge_density:.3f}")
            logger.debug(f"  Color variance: {color_variance:.3f}")
            
            # Apply heuristic rules
            is_document = self._apply_detection_rules(
                width, height, aspect_ratio, edge_density, color_variance
            )
            
            logger.info(f"Document detection: {image_path} -> {'DOCUMENT' if is_document else 'NATURAL IMAGE'}")
            
            return is_document
            
        except Exception as e:
            logger.error(f"Document detection failed for {image_path}: {e}")
            # Default to natural image (no preprocessing) to avoid coordinate issues
            return False
    
    def _calculate_aspect_ratio(self, width: int, height: int) -> float:
        """Calculate aspect ratio (always >= 1.0)."""
        return max(width, height) / min(width, height)
    
    def _calculate_edge_density(self, image: np.ndarray) -> float:
        """
        Calculate edge density using Canny edge detection.
        Documents typically have higher edge density due to text and structured layout.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Canny edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Calculate edge pixel ratio
        total_pixels = edges.shape[0] * edges.shape[1]
        edge_pixels = np.sum(edges > 0)
        
        return edge_pixels / total_pixels
    
    def _calculate_color_variance(self, image: np.ndarray) -> float:
        """
        Calculate color variance. Documents typically have lower color variance
        (more black text on white background) compared to natural images.
        """
        # Convert to LAB color space for better perceptual analysis
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Calculate standard deviation for each channel
        l_std = np.std(lab[:, :, 0])  # Lightness
        a_std = np.std(lab[:, :, 1])  # Green-Red
        b_std = np.std(lab[:, :, 2])  # Blue-Yellow
        
        # Return average standard deviation
        return (l_std + a_std + b_std) / 3.0
    
    def _apply_detection_rules(
        self, 
        width: int, 
        height: int, 
        aspect_ratio: float,
        edge_density: float,
        color_variance: float
    ) -> bool:
        """
        Apply simple heuristic rules to determine if image is a document.
        
        These rules are designed to be conservative - when in doubt, treat as
        natural image to avoid coordinate offset issues.
        """
        # Rule 1: Standard document aspect ratios
        # A4: ~1.414, Letter: ~1.29, Legal: ~1.65
        if 1.2 <= aspect_ratio <= 1.8:
            logger.debug("  Rule 1: Standard document aspect ratio")
            
            # Sub-rule: Large enough to be a scanned document
            if width >= 600 and height >= 400:
                logger.debug("  Sub-rule 1a: Large enough for scanned document")
                return True
        
        # Rule 2: Very rectangular (likely forms, tables, receipts)
        if aspect_ratio >= 2.0:
            logger.debug("  Rule 2: Very rectangular shape")
            
            # Must be reasonably sized
            if min(width, height) >= 200:
                logger.debug("  Sub-rule 2a: Reasonably sized rectangular document")
                return True
        
        # Rule 3: High edge density + low color variance (text-heavy documents)
        if edge_density > 0.15 and color_variance < 30:
            logger.debug("  Rule 3: High edge density + low color variance")
            
            # Must be reasonably sized
            if width >= 400 and height >= 300:
                logger.debug("  Sub-rule 3a: Text-heavy document")
                return True
        
        # Rule 4: Very large images are often scanned documents
        if width >= 1200 and height >= 900:
            logger.debug("  Rule 4: Very large image")
            
            # Additional check: not too colorful (exclude photos)
            if color_variance < 50:
                logger.debug("  Sub-rule 4a: Large but not too colorful")
                return True
        
        # Default: treat as natural image to avoid coordinate issues
        logger.debug("  Default: Treating as natural image")
        return False
    
    def get_detection_summary(self, image_path: str) -> dict:
        """
        Get detailed detection information for debugging.
        
        Returns:
            Dictionary with detection features and decision
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {"error": "Cannot load image"}
            
            height, width = image.shape[:2]
            aspect_ratio = self._calculate_aspect_ratio(width, height)
            edge_density = self._calculate_edge_density(image)
            color_variance = self._calculate_color_variance(image)
            is_document = self.is_document_image(image_path)
            
            return {
                "image_path": image_path,
                "dimensions": (width, height),
                "aspect_ratio": aspect_ratio,
                "edge_density": edge_density,
                "color_variance": color_variance,
                "is_document": is_document,
                "recommended_config": "document" if is_document else "natural"
            }
            
        except Exception as e:
            return {"error": str(e)}