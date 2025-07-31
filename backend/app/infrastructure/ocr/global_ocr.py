"""
Global OCR service to avoid repeated initialization with dynamic configuration support
"""
import threading
from typing import Optional, Dict, Any
from loguru import logger
from paddleocr import PaddleOCR

# Global OCR instances for different configurations
_natural_image_ocr: Optional[PaddleOCR] = None
_document_ocr: Optional[PaddleOCR] = None
_ocr_lock = threading.Lock()

def reset_global_ocr():
    """Reset all global OCR instances to force reinitialization"""
    global _natural_image_ocr, _document_ocr
    with _ocr_lock:
        if _natural_image_ocr is not None:
            logger.info("Resetting global natural image OCR instance")
            _natural_image_ocr = None
        if _document_ocr is not None:
            logger.info("Resetting global document OCR instance")
            _document_ocr = None

def get_ocr_for_config(config: Dict[str, Any]) -> PaddleOCR:
    """
    Get or create OCR instance for the specified configuration.
    
    Args:
        config: OCR configuration dictionary
        
    Returns:
        PaddleOCR instance configured for the specified parameters
    """
    global _natural_image_ocr, _document_ocr
    
    # Determine if this is a document configuration
    is_document_config = config.get('use_doc_orientation_classify', False)
    
    if is_document_config:
        # Document configuration
        if _document_ocr is None:
            with _ocr_lock:
                if _document_ocr is None:
                    logger.info("Initializing global document OCR instance")
                    try:
                        logger.info(f"Document OCR config: {config}")
                        _document_ocr = PaddleOCR(**config)
                        logger.info("Global document OCR instance created successfully")
                    except Exception as e:
                        logger.error(f"Failed to create document OCR instance: {e}")
                        # Fallback to minimal config
                        fallback_config = {'lang': 'en'}
                        _document_ocr = PaddleOCR(**fallback_config)
                        logger.info("Document OCR instance created with fallback config")
        return _document_ocr
    
    else:
        # Natural image configuration
        if _natural_image_ocr is None:
            with _ocr_lock:
                if _natural_image_ocr is None:
                    logger.info("Initializing global natural image OCR instance")
                    try:
                        logger.info(f"Natural image OCR config: {config}")
                        _natural_image_ocr = PaddleOCR(**config)
                        logger.info("Global natural image OCR instance created successfully")
                    except Exception as e:
                        logger.error(f"Failed to create natural image OCR instance: {e}")
                        # Fallback to minimal config
                        fallback_config = {'lang': 'en'}
                        _natural_image_ocr = PaddleOCR(**fallback_config)
                        logger.info("Natural image OCR instance created with fallback config")
        return _natural_image_ocr

def get_global_ocr() -> PaddleOCR:
    """
    Legacy function for backward compatibility.
    Returns natural image OCR configuration by default.
    """
    from app.infrastructure.ocr.ocr_config import OCRConfigManager
    config = OCRConfigManager.get_natural_image_config()
    return get_ocr_for_config(config)