"""Clean PaddleOCR service implementation following official best practices."""
import os
from typing import List
import cv2
import numpy as np
from loguru import logger

try:
    from paddleocr import PaddleOCR
except ImportError as e:
    logger.error(f"Failed to import PaddleOCR: {e}")
    raise

from app.domain.entities.text_region import TextRegion
from app.domain.value_objects.rectangle import Rectangle
from app.domain.value_objects.point import Point
from app.infrastructure.image_processing.image_resizer import ImageResizer, CoordinateScaler
from app.infrastructure.image_processing.document_detector import DocumentDetector
from app.infrastructure.ocr.ocr_config import OCRConfigManager


class PaddleOCRService:
    """Simplified PaddleOCR service following official best practices."""
    
    def __init__(self):
        """Initialize PaddleOCR service with smart document detection."""
        self._initialization_failed = False
        self._image_resizer = ImageResizer(target_size=1280)  # Balanced size for quality and performance
        self._document_detector = DocumentDetector()  # Smart document type detection
        logger.info("PaddleOCR service initialized with smart document detection")
    
    def _get_adaptive_padding(self, text_width: float, text_height: float, confidence: float, scale_factor: float, image_height: int) -> float:
        """Calculate adaptive padding based on text size relative to image."""
        
        # Calculate text height ratio relative to image height
        text_height_ratio = text_height / image_height
        
        # Simple rule: small text uses small padding, large text uses large padding
        if text_height_ratio < 0.05:  # Text height < 5% of image height (small text like documents)
            base_padding = 1.0
            logger.debug(f"Small text (height ratio {text_height_ratio:.3f}) -> 1px padding")
        else:  # Text height >= 5% of image height (large text like UI screenshots)
            base_padding = 5.0
            logger.debug(f"Large text (height ratio {text_height_ratio:.3f}) -> 5px base padding")
        
        # Fine-tune based on confidence: lower confidence needs slightly more padding
        confidence_factor = 1.0 if confidence > 0.8 else 1.2
        
        # Calculate final padding
        final_padding = base_padding * confidence_factor
        final_padding = max(1.0, min(8.0, final_padding))  # Limit between 1-8 pixels
        
        return final_padding / scale_factor if scale_factor != 1.0 else final_padding
    
    def _get_ocr_for_image(self, image_path: str):
        """Get appropriate OCR instance based on image type detection."""
        try:
            # Detect image type
            is_document = self._document_detector.is_document_image(image_path)
            
            # Get appropriate configuration
            if is_document:
                config = OCRConfigManager.get_document_config()
            else:
                config = OCRConfigManager.get_natural_image_config()
            
            # Log configuration choice
            OCRConfigManager.log_config_choice(image_path, is_document, config)
            
            # Get OCR instance for this configuration
            from app.infrastructure.ocr.global_ocr import get_ocr_for_config
            return get_ocr_for_config(config)
            
        except Exception as e:
            logger.error(f"Failed to get OCR instance for {image_path}: {e}")
            raise
    
    async def detect_text_regions(self, image_path: str) -> List[TextRegion]:
        """
        Detect text regions using PaddleOCR with official best practices.
        
        Args:
            image_path: Path to the image file to process.
            
        Returns:
            List of TextRegion objects with accurate coordinates.
            
        Raises:
            FileNotFoundError: If the image file doesn't exist.
            ValueError: If the image cannot be processed.
        """
        # Validate input
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        if self._initialization_failed:
            raise RuntimeError("PaddleOCR service initialization failed")
        
        try:
            # Load and resize image if necessary
            original_image, resized_image, scale_factor = self._image_resizer.resize_image_from_path(image_path)
            
            original_height, original_width = original_image.shape[:2]
            resized_height, resized_width = resized_image.shape[:2]
            
            logger.info(f"Processing image: {original_width}x{original_height} -> {resized_width}x{resized_height} (scale={scale_factor:.3f})")
            
            # Detect image type for adaptive padding
            is_document = self._document_detector.is_document_image(image_path)
            
            # Get appropriate OCR instance based on image type
            ocr_instance = self._get_ocr_for_image(image_path)
            
            # Convert BGR to RGB (PaddleOCR expects RGB)
            image_rgb = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
            
            # Run OCR on resized image
            logger.info("Starting OCR detection with smart configuration...")
            start_time = __import__('time').time()
            
            results = ocr_instance.ocr(image_rgb)
            
            end_time = __import__('time').time()
            logger.info(f"OCR detection completed in {end_time - start_time:.2f} seconds")
            
            # Convert results to TextRegion objects with coordinate scaling
            text_regions = self._convert_results_to_text_regions(
                results, original_width, original_height, scale_factor
            )
            
            logger.info(f"Detected {len(text_regions)} text regions")
            return text_regions
            
        except Exception as e:
            logger.error(f"OCR detection failed for {image_path}: {e}")
            raise
    
    def _convert_results_to_text_regions(
        self, 
        ocr_results, 
        original_width: int, 
        original_height: int,
        scale_factor: float
    ) -> List[TextRegion]:
        """Convert PaddleOCR 3.1+ results to TextRegion objects."""
        text_regions = []
        
        if not ocr_results:
            logger.info("No OCR results")
            return text_regions
        
        # Handle PaddleOCR 3.1+ new format (dict-based results)
        if isinstance(ocr_results, list) and len(ocr_results) > 0:
            result_dict = ocr_results[0]
            
            if isinstance(result_dict, dict):
                # Extract text data from the new format
                rec_texts = result_dict.get('rec_texts', [])
                rec_scores = result_dict.get('rec_scores', [])
                rec_polys = result_dict.get('rec_polys', [])
                
                logger.info(f"Found {len(rec_texts)} text regions in PaddleOCR 3.1+ format")
                
                # Process each detected text region
                for i, (text, confidence, poly) in enumerate(zip(rec_texts, rec_scores, rec_polys)):
                    try:
                        # Skip low-confidence detections
                        if confidence < 0.1:
                            continue
                        
                        # Skip empty text
                        if not text or not text.strip():
                            continue
                        
                        # Convert numpy array coordinates to list
                        if hasattr(poly, 'tolist'):
                            coordinates = poly.tolist()
                        else:
                            coordinates = poly
                        
                        # Scale coordinates back to original image size
                        scaled_coordinates = CoordinateScaler.scale_coordinates_to_original(
                            coordinates, scale_factor
                        )
                        
                        # Convert scaled coordinates to Points
                        corners = [Point(float(coord[0]), float(coord[1])) for coord in scaled_coordinates]
                        
                        # Create axis-aligned bounding box from scaled coordinates
                        x_coords = [coord[0] for coord in scaled_coordinates]
                        y_coords = [coord[1] for coord in scaled_coordinates]
                        
                        min_x, max_x = min(x_coords), max(x_coords)
                        min_y, max_y = min(y_coords), max(y_coords)
                        
                        # Calculate adaptive padding based on text size relative to image
                        text_width = max_x - min_x
                        text_height = max_y - min_y
                        padding = self._get_adaptive_padding(text_width, text_height, confidence, scale_factor, original_height)
                        
                        # Ensure bounding box is within image bounds
                        bbox_x = max(0, min_x - padding)
                        bbox_y = max(0, min_y - padding) 
                        bbox_width = min(max_x - min_x + 2 * padding, original_width - bbox_x)
                        bbox_height = min(max_y - min_y + 2 * padding, original_height - bbox_y)
                        
                        bounding_box = Rectangle(
                            x=bbox_x,
                            y=bbox_y,
                            width=bbox_width,
                            height=bbox_height
                        )
                        
                        # Create TextRegion
                        text_region = TextRegion.create_from_detection(
                            bounding_box=bounding_box,
                            confidence=float(confidence),
                            corners=corners,
                            original_text=text.strip()
                        )
                        
                        text_regions.append(text_region)
                        
                    except Exception as e:
                        logger.warning(f"Failed to process text region {i}: {e}")
                        continue
            else:
                # Fallback to old format processing
                logger.info("Using legacy OCR result format")
                return self._convert_legacy_results_to_text_regions(
                    ocr_results, original_width, original_height, scale_factor
                )
        
        # Sort by confidence (highest first)
        text_regions.sort(key=lambda r: r.confidence, reverse=True)
        
        return text_regions
    
    def _convert_legacy_results_to_text_regions(
        self, 
        ocr_results, 
        original_width: int, 
        original_height: int,
        scale_factor: float
    ) -> List[TextRegion]:
        """Convert legacy PaddleOCR results to TextRegion objects."""
        text_regions = []
        
        if not ocr_results or not ocr_results[0]:
            logger.info("No text detected in legacy format")
            return text_regions
        
        logger.info(f"Converting {len(ocr_results[0])} legacy OCR results to text regions")
        
        for i, result in enumerate(ocr_results[0]):
            try:
                # Handle different PaddleOCR result formats
                if len(result) == 2:
                    # Standard format: [coordinates, (text, confidence)]
                    coordinates, text_conf = result
                    if isinstance(text_conf, (list, tuple)) and len(text_conf) == 2:
                        text, confidence = text_conf
                    else:
                        logger.warning(f"Unexpected text_conf format: {text_conf}")
                        continue
                elif len(result) == 3:
                    # Alternative format: [coordinates, text, confidence]
                    coordinates, text, confidence = result
                else:
                    logger.warning(f"Unexpected result format for region {i}: {result}")
                    continue
                
                # Skip low-confidence detections
                if confidence < 0.1:
                    continue
                
                # Skip empty text
                if not text or not text.strip():
                    continue
                
                # Scale coordinates back to original image size
                scaled_coordinates = CoordinateScaler.scale_coordinates_to_original(
                    coordinates, scale_factor
                )
                
                # Convert scaled coordinates to Points
                corners = [Point(float(coord[0]), float(coord[1])) for coord in scaled_coordinates]
                
                # Create axis-aligned bounding box from scaled coordinates
                x_coords = [coord[0] for coord in scaled_coordinates]
                y_coords = [coord[1] for coord in scaled_coordinates]
                
                min_x, max_x = min(x_coords), max(x_coords)
                min_y, max_y = min(y_coords), max(y_coords)
                
                # Calculate adaptive padding based on text size relative to image
                text_width = max_x - min_x
                text_height = max_y - min_y
                padding = self._get_adaptive_padding(text_width, text_height, confidence, scale_factor, original_height)
                bounding_box = Rectangle(
                    x=max(0, min_x - padding),
                    y=max(0, min_y - padding),
                    width=max_x - min_x + 2 * padding,
                    height=max_y - min_y + 2 * padding
                )
                
                # Create TextRegion
                text_region = TextRegion.create_from_detection(
                    bounding_box=bounding_box,
                    confidence=float(confidence),
                    corners=corners,
                    original_text=text.strip() if text.strip() else None
                )
                
                text_regions.append(text_region)
                
            except Exception as e:
                logger.warning(f"Failed to process text region {i}: {e}")
                continue
        
        # Sort by confidence (highest first)
        text_regions.sort(key=lambda r: r.confidence, reverse=True)
        
        return text_regions
    
    def get_device_info(self) -> dict:
        """Get information about the smart OCR service."""
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            cuda_device_count = torch.cuda.device_count() if cuda_available else 0
        except ImportError:
            cuda_available = False
            cuda_device_count = 0
        
        # Test if we can create an OCR instance to check initialization
        ocr_initialized = True
        try:
            from app.infrastructure.ocr.ocr_config import OCRConfigManager
            from app.infrastructure.ocr.global_ocr import get_ocr_for_config
            
            # Try to get a natural image OCR instance
            config = OCRConfigManager.get_natural_image_config()
            ocr_instance = get_ocr_for_config(config)
            ocr_initialized = ocr_instance is not None
        except Exception:
            ocr_initialized = False
            
        return {
            'device': 'cpu',  # Default device for PaddleOCR
            'cuda_available': cuda_available,
            'cuda_device_count': cuda_device_count,
            'ocr_initialized': ocr_initialized,
            'initialization_failed': self._initialization_failed,  
            'service_type': 'Smart PaddleOCR with Document Detection',
            'version': '3.1.0',
            'features': {
                'document_detection': True,
                'smart_config_selection': True,
                'coordinate_accuracy_fix': True
            }
        }