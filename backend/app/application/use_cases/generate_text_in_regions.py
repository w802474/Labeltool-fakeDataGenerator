"""Use case for generating text in specified regions."""
from typing import List, Dict, Any
from pathlib import Path
from loguru import logger
from PIL import Image

from app.domain.entities.label_session import LabelSession
from app.domain.entities.text_region import TextRegion
from app.domain.value_objects.session_status import SessionStatus
from app.domain.value_objects.image_file import ImageFile, Dimensions
from app.infrastructure.image_processing.font_analyzer import SimpleFontAnalyzer, FontProperties
from app.infrastructure.image_processing.text_renderer import TextRenderer


class GenerateTextInRegionsUseCase:
    """Use case for generating text in specified regions of an image."""
    
    def __init__(self):
        """Initialize the use case with required services."""
        self.font_analyzer = SimpleFontAnalyzer()
        self.text_renderer = TextRenderer()
        logger.info("GenerateTextInRegionsUseCase initialized")
    
    async def execute(self, session: LabelSession, regions_with_text: List[Dict[str, Any]]) -> LabelSession:
        """
        Generate text in specified regions and create new processed image.
        
        Args:
            session: Current label session
            regions_with_text: List of dictionaries containing region_id and user_text
            
        Returns:
            Updated LabelSession with new processed image
            
        Raises:
            ValueError: If session is not in a valid state for text generation
        """
        if session.status not in [SessionStatus.DETECTED, SessionStatus.EDITING, SessionStatus.COMPLETED, SessionStatus.GENERATED]:
            raise ValueError(f"Session {session.id} is not ready for text generation (status: {session.status.value})")
        
        logger.info(f"Starting text generation for session {session.id}")
        logger.info(f"Processing {len(regions_with_text)} regions with user text")
        
        try:
            # Find the base image to work with (where to render text)
            base_image_path = self._get_base_image_path(session)
            original_image_path = session.original_image.path
            
            logger.info(f"Text generation setup:")
            logger.info(f"  - Font analysis source: {original_image_path} (original OCR image)")
            logger.info(f"  - Text rendering target: {base_image_path} (processed/clean image)")
            
            # Prepare regions with user input text
            regions_to_render = []
            
            for region_text_data in regions_with_text:
                region_id = region_text_data.get('region_id')
                user_text = region_text_data.get('user_text', '').strip()
                
                if not user_text:
                    continue
                
                # Find the processed region (required for positioning)
                processed_region = self._find_region_by_id(
                    session.get_processed_regions_for_display(), region_id
                )
                
                if not processed_region:
                    logger.warning(f"Region {region_id} not found in processed regions")
                    continue
                
                # Try to find corresponding OCR region (optional for manually added regions)
                ocr_region = self._find_region_by_id(session.text_regions, region_id)
                
                # Update processed region with user input (for rendering position)
                processed_region.set_user_input_text(user_text)
                
                # Calculate font properties based on region modification state
                if (hasattr(processed_region, 'is_size_modified') and processed_region.is_size_modified and
                    hasattr(processed_region, 'original_box_size') and processed_region.original_box_size):
                    
                    # For modified regions, calculate font size based on original recorded size
                    logger.info(f"Region {region_id} - Using recorded original size for font calculation:")
                    logger.info(f"  - Original box: {processed_region.original_box_size.width:.1f}x{processed_region.original_box_size.height:.1f}")
                    logger.info(f"  - Current box: {processed_region.bounding_box.width:.1f}x{processed_region.bounding_box.height:.1f}")
                    
                    # Calculate base font size from the ORIGINAL recorded size
                    original_height = processed_region.original_box_size.height
                    base_font_size = max(6, int(original_height * 0.75))
                    
                    # Calculate scaling factor
                    scale_x = processed_region.bounding_box.width / processed_region.original_box_size.width
                    scale_y = processed_region.bounding_box.height / processed_region.original_box_size.height
                    avg_scale = (scale_x + scale_y) / 2
                    
                    # Apply scaling
                    scaled_font_size = max(4, int(base_font_size * avg_scale))
                    
                    logger.info(f"  - Base font size (from original): {base_font_size}px")
                    logger.info(f"  - Scale factors: X={scale_x:.2f}, Y={scale_y:.2f}, Avg={avg_scale:.2f}")
                    logger.info(f"  - Final scaled font size: {scaled_font_size}px")
                    
                    # Choose appropriate font family based on text content
                    font_family = self._select_font_for_text(user_text)
                    
                    # Create font properties with calculated size
                    font_properties = FontProperties(
                        size=scaled_font_size,
                        type="proportional",  # Default
                        color="black",
                        family=font_family,
                        style="normal"
                    )
                    
                    logger.info(f"  - Selected font family: {font_family} for text: '{user_text}'")
                    
                else:
                    # For unmodified regions, analyze from OCR region if available
                    if ocr_region:
                        logger.info(f"Region {region_id} - Using OCR analysis for unmodified region")
                        original_image_path = session.original_image.path
                        font_properties = self.font_analyzer.estimate_font_properties(ocr_region, original_image_path)
                        logger.info(f"  - OCR estimated font size: {font_properties.size}px")
                    else:
                        # For manually added regions without OCR data, use processed region for analysis
                        logger.info(f"Region {region_id} - Using processed region analysis for manually added region")
                        original_image_path = session.original_image.path
                        font_properties = self.font_analyzer.estimate_font_properties(processed_region, original_image_path)
                        logger.info(f"  - Estimated font size for manual region: {font_properties.size}px")
                
                processed_region.set_font_properties(font_properties.to_dict())
                
                if ocr_region:
                    logger.info(f"Region {region_id}: analyzing font from OCR region at ({ocr_region.bounding_box.x:.0f}, {ocr_region.bounding_box.y:.0f})")
                else:
                    logger.info(f"Region {region_id}: manually added region, no OCR reference")
                logger.info(f"Region {region_id}: will render at processed position ({processed_region.bounding_box.x:.0f}, {processed_region.bounding_box.y:.0f})")
                
                # Add to rendering list using processed region coordinates
                regions_to_render.append((processed_region, user_text, font_properties))
            
            if not regions_to_render:
                logger.warning("No valid regions with text to generate")
                return session
            
            # Render text to image
            logger.info(f"Rendering text to {len(regions_to_render)} regions")
            output_image_path = self.text_renderer.render_multiple_texts(
                image_path=base_image_path,
                text_regions_with_text=regions_to_render,
                output_dir="processed"
            )
            
            # Update session with new processed image
            # Get image dimensions
            with Image.open(output_image_path) as img:
                width, height = img.size
            
            # Create new ImageFile for processed result
            processed_image = ImageFile(
                id=f"processed_{session.id}",
                filename=Path(output_image_path).name,
                path=output_image_path,
                mime_type="image/png",
                size=Path(output_image_path).stat().st_size,
                dimensions=Dimensions(width=width, height=height)
            )
            
            # Update session with new processed image and save modified regions
            session.processed_image = processed_image
            
            # Save the modified regions back to session
            # Extract all processed regions with their updated user_input_text
            if session.processed_text_regions is None:
                session.initialize_processed_regions()
            
            # Update processed_text_regions with the modified regions from regions_to_render
            for processed_region, user_text, font_properties in regions_to_render:
                # Find and update the corresponding region in session.processed_text_regions
                for i, session_region in enumerate(session.processed_text_regions):
                    if session_region.id == processed_region.id:
                        # Update the session region with the modified data
                        session_region.set_user_input_text(user_text)
                        session_region.set_font_properties(font_properties.to_dict())
                        break
            
            session.transition_to_status(SessionStatus.GENERATED)
            
            logger.info(f"Text generation completed successfully: {output_image_path}")
            return session
            
        except Exception as e:
            logger.error(f"Text generation failed for session {session.id}: {e}")
            session.transition_to_status(SessionStatus.ERROR)
            raise
    
    def preview_text_generation(
        self, 
        session: LabelSession, 
        regions_with_text: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Preview text generation without actually creating the image.
        
        Args:
            session: Current label session
            regions_with_text: List of dictionaries containing region_id and user_text
            
        Returns:
            Dictionary with preview information for each region
        """
        try:
            base_image_path = self._get_base_image_path(session)
            preview_results = {}
            
            for region_text_data in regions_with_text:
                region_id = region_text_data.get('region_id')
                user_text = region_text_data.get('user_text', '').strip()
                
                if not user_text:
                    continue
                
                # Find the corresponding text region
                text_region = self._find_region_by_id(session.text_regions, region_id)
                if not text_region:
                    continue
                
                # Estimate font properties
                font_properties = self.font_analyzer.estimate_font_properties(text_region, base_image_path)
                
                # Get preview information
                preview_info = self.text_renderer.preview_text_in_region(
                    image_path=base_image_path,
                    text_region=text_region,
                    text=user_text,
                    font_properties=font_properties
                )
                
                preview_results[region_id] = {
                    'text': user_text,
                    'preview': preview_info,
                    'region_bounds': {
                        'x': text_region.bounding_box.x,
                        'y': text_region.bounding_box.y,
                        'width': text_region.bounding_box.width,
                        'height': text_region.bounding_box.height
                    }
                }
            
            return {
                'status': 'success',
                'previews': preview_results,
                'total_regions': len(preview_results)
            }
            
        except Exception as e:
            logger.error(f"Text preview failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_base_image_path(self, session: LabelSession) -> str:
        """
        Get the base image path to use for text generation.
        
        Args:
            session: Label session
            
        Returns:
            Path to the base image (processed image if available, otherwise original)
        """
        # Use processed image if it exists (for re-generation scenarios)
        if session.processed_image and Path(session.processed_image.path).exists():
            return session.processed_image.path
        
        # Otherwise use original image
        return session.original_image.path
    
    def _find_region_by_id(self, regions: List[TextRegion], region_id: str) -> TextRegion:
        """
        Find a text region by its ID.
        
        Args:
            regions: List of text regions
            region_id: ID to search for
            
        Returns:
            TextRegion if found, None otherwise
        """
        for region in regions:
            if region.id == region_id:
                return region
        return None
    
    def _select_font_for_text(self, text: str) -> str:
        """
        Select appropriate font family based on text content with platform-aware font detection.
        
        Args:
            text: The text to be rendered
            
        Returns:
            Font family name suitable for the text
        """
        import re
        import platform
        import os
        
        # Check if text contains CJK characters (Chinese, Japanese, Korean)
        has_chinese = re.search(r'[\u4e00-\u9fff]', text)
        has_japanese = re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text)  # Hiragana + Katakana
        has_korean = re.search(r'[\uac00-\ud7af]', text)
        
        if has_chinese or has_japanese or has_korean:
            # CJK text - use a font that supports CJK characters
            # Platform-aware font selection
            if os.path.exists("/usr/share/fonts"):
                # Linux environment (Docker container)
                if has_japanese:
                    # Japanese text priority
                    possible_fonts = [
                        "Noto Sans CJK JP",
                        "Source Han Sans JP", 
                        "WenQuanYi Zen Hei",  # Also supports Japanese
                        "DejaVu Sans"  # Fallback
                    ]
                elif has_chinese:
                    # Chinese text priority
                    possible_fonts = [
                        "WenQuanYi Zen Hei",
                        "WenQuanYi Micro Hei", 
                        "Noto Sans CJK SC",
                        "Source Han Sans SC",
                        "DejaVu Sans"  # Fallback
                    ]
                else:
                    # Korean or mixed CJK
                    possible_fonts = [
                        "Noto Sans CJK KR",
                        "Source Han Sans KR",
                        "WenQuanYi Zen Hei",
                        "DejaVu Sans"  # Fallback
                    ]
                # Return the first choice
                return possible_fonts[0]
            elif platform.system() == "Darwin":
                # macOS
                if has_japanese:
                    return "Hiragino Kaku Gothic ProN"  # Japanese
                elif has_chinese:
                    return "PingFang SC"  # Chinese Simplified
                else:
                    return "Apple SD Gothic Neo"  # Korean
            elif platform.system() == "Windows":
                # Windows
                if has_japanese:
                    return "Yu Gothic"  # Japanese
                elif has_chinese:
                    return "Microsoft YaHei"  # Chinese
                else:
                    return "Malgun Gothic"  # Korean
            else:
                # Fallback for unknown systems
                return "WenQuanYi Zen Hei"
        
        # Check if text is primarily numbers
        if re.match(r'^[\d\s\.\,\-\+\(\)%$€£¥]+$', text):
            # Numbers and common symbols - use a clean, readable font
            return "Helvetica"  # Clean, modern font for numbers
        
        # Check if text is English letters and basic punctuation
        if re.match(r'^[a-zA-Z\s\.\,\!\?\;\:\'\"\-\(\)]+$', text):
            # English text - use popular web fonts
            if len(text) > 20:  # Longer text, use readable font
                return "Times New Roman"
            else:  # Short text, use modern font
                return "Helvetica"
        
        # Mixed content or special characters - use Arial as fallback
        return "Arial"