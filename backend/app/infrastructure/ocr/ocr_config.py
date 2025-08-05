"""
OCR configuration management for different image types.
"""
from typing import Dict, Any
from loguru import logger


class OCRConfigManager:
    """Manages OCR configurations for different image types."""
    
    @staticmethod
    def get_natural_image_config() -> Dict[str, Any]:
        """
        Configuration for natural images (screenshots, photos, etc.).
        Optimized for coordinate accuracy by disabling document preprocessing.
        """
        return {
            'lang': 'japan',
            'det_limit_side_len': 1280,
            'det_limit_type': 'max',
            # CRITICAL: Disable all document preprocessing to prevent coordinate offset
            'use_doc_orientation_classify': False,
            'use_doc_unwarping': False,
            'use_textline_orientation': False
            # Note: Removed unsupported parameters like det_db_thresh, unclip_ratio, box_thresh
            # These are not valid parameters for PaddleOCR 3.1 constructor
        }
    
    @staticmethod
    def get_document_config() -> Dict[str, Any]:
        """
        Configuration for document images (scans, forms, tables, etc.).
        Enables minimal preprocessing for better text recognition while
        minimizing coordinate distortion.
        """
        return {
            'lang': 'japan',
            'det_limit_side_len': 1280,
            'det_limit_type': 'max',
            # Enable minimal document preprocessing
            'use_doc_orientation_classify': True,   # Only orientation correction
            'use_doc_unwarping': False,            # Skip geometric correction to preserve coordinates
            'use_textline_orientation': False     # Skip text line orientation
            # Note: Removed unsupported parameters like det_db_thresh, unclip_ratio, box_thresh
            # These are not valid parameters for PaddleOCR 3.1 constructor
        }
    
    @staticmethod
    def get_config_name(config: Dict[str, Any]) -> str:
        """Get a human-readable name for a configuration."""
        if config.get('use_doc_orientation_classify', False):
            return "Document Config"
        else:
            return "Natural Image Config"
    
    @staticmethod
    def log_config_choice(image_path: str, is_document: bool, config: Dict[str, Any]):
        """Log the configuration choice for debugging."""
        config_name = OCRConfigManager.get_config_name(config)
        image_type = "DOCUMENT" if is_document else "NATURAL IMAGE"
        
        logger.info(f"OCR Config Selection:")
        logger.info(f"  Image: {image_path}")
        logger.info(f"  Detected type: {image_type}")
        logger.info(f"  Using config: {config_name}")
        logger.info(f"  Preprocessing enabled: {config.get('use_doc_orientation_classify', False)}")