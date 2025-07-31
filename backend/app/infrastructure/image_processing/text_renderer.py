"""Text rendering module for generating text in specified regions."""
import os
import uuid
from typing import List, Optional, Dict, Tuple
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from loguru import logger

from app.domain.entities.text_region import TextRegion
from app.infrastructure.image_processing.font_analyzer import FontProperties, SimpleFontAnalyzer


class TextRenderer:
    """Text renderer using PIL for adding text to images."""
    
    def __init__(self):
        """Initialize text renderer."""
        self.font_analyzer = SimpleFontAnalyzer()
        self.font_cache = {}  # Cache loaded fonts for performance
        
        # Common font paths (system-dependent)
        self.system_fonts = self._discover_system_fonts()
        logger.info(f"TextRenderer initialized with {len(self.system_fonts)} system fonts")
        
        # Debug flag for text positioning
        self.debug_positioning = True
    
    def _discover_system_fonts(self) -> Dict[str, str]:
        """Discover available system fonts."""
        fonts = {}
        
        # Common font locations across systems
        font_paths = [
            "/System/Library/Fonts/",  # macOS
            "/usr/share/fonts/",       # Linux
            "C:/Windows/Fonts/",       # Windows
        ]
        
        # Common font files to look for
        font_files = {
            "Arial": ["Arial.ttf", "arial.ttf", "ArialMT.ttf"],
            "Times New Roman": ["Times.ttf", "times.ttf", "TimesNewRoman.ttf"],
            "Courier New": ["Courier.ttf", "courier.ttf", "CourierNew.ttf"],
            "Helvetica": ["Helvetica.ttf", "helvetica.ttf", "HelveticaNeue.ttf"]
        }
        
        for font_dir in font_paths:
            if not os.path.exists(font_dir):
                continue
                
            for font_name, file_variants in font_files.items():
                for file_name in file_variants:
                    font_path = os.path.join(font_dir, file_name)
                    if os.path.exists(font_path):
                        fonts[font_name] = font_path
                        break
        
        # Fallback: try to use PIL's default font
        if not fonts:
            try:
                default_font = ImageFont.load_default()
                fonts["Default"] = "default"
            except Exception:
                pass
        
        return fonts
    
    def _get_font(self, font_properties: FontProperties, text: str = "") -> ImageFont.ImageFont:
        """
        Get PIL font object from font properties.
        
        Args:
            font_properties: Font properties containing family, size, style
            text: Text to be rendered (for smart font selection)
            
        Returns:
            PIL ImageFont object
        """
        # If we have text, use language-aware font selection
        if text:
            try:
                return self._get_best_font_for_language(text, font_properties.size)
            except Exception:
                pass  # Fall through to original logic
        
        cache_key = f"{font_properties.family}_{font_properties.size}_{font_properties.style}"
        
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        try:
            # Try to find system font
            font_path = self.system_fonts.get(font_properties.family)
            
            if font_path and font_path != "default":
                font = ImageFont.truetype(font_path, font_properties.size)
            else:
                # Use Unicode-capable fallback font instead of load_default()
                font = self._get_unicode_fallback_font(font_properties.size)
            
            self.font_cache[cache_key] = font
            return font
            
        except Exception as e:
            logger.warning(f"Failed to load font {font_properties.family}: {e}")
            # Ultimate fallback to Unicode-capable font
            try:
                font = self._get_unicode_fallback_font(font_properties.size)
                self.font_cache[cache_key] = font
                return font
            except Exception:
                # If even fallback font fails, return None and handle gracefully
                return None
    
    def _get_unicode_fallback_font(self, size: int) -> ImageFont.ImageFont:
        """
        Get a Unicode-capable fallback font that can handle Chinese characters.
        
        Args:
            size: Font size
            
        Returns:
            PIL ImageFont object that supports Unicode
        """
        import platform
        
        # Common Unicode fonts by platform
        unicode_fonts = []
        
        system = platform.system().lower()
        if system == "darwin":  # macOS - comprehensive multilingual font list
            unicode_fonts = [
                # Chinese fonts (Simplified & Traditional)
                "/System/Library/Fonts/PingFang.ttc",  # Modern Chinese - best choice
                "/System/Library/Fonts/Hiragino Sans GB.ttc",  # Chinese Simplified
                "/System/Library/Fonts/Hiragino Sans CNS.ttc",  # Chinese Traditional
                "/System/Library/Fonts/STHeiti Light.ttc",  # Chinese legacy
                "/System/Library/Fonts/STSong.ttc",  # Chinese serif
                
                # Japanese fonts
                "/System/Library/Fonts/Hiragino Sans.ttc",  # Japanese
                "/System/Library/Fonts/Yu Gothic.ttc",  # Japanese modern
                
                # Korean fonts
                "/System/Library/Fonts/AppleSDGothicNeo.ttc",  # Korean
                
                # Universal Unicode fonts
                "/Library/Fonts/Arial Unicode MS.ttf",  # Comprehensive Unicode
                "/System/Library/Fonts/Apple Symbols.ttf",  # Symbols
                
                # Western fonts with good Unicode coverage
                "/System/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Times.ttc",
                "/System/Library/Fonts/Courier.ttc"
            ]
        elif system == "linux":  # Linux - comprehensive multilingual font list
            unicode_fonts = [
                # Noto fonts (Google's comprehensive Unicode font family)
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # CJK unified
                "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",  # Latin
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Alternative path
                
                # DejaVu fonts (good Unicode coverage)
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
                
                # Liberation fonts
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
                
                # Droid fonts (Android legacy, good CJK support)
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                
                # System fonts
                "/usr/share/fonts/TTF/arial.ttf",
                "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf"
            ]
        elif system == "windows":  # Windows - comprehensive multilingual font list
            unicode_fonts = [
                # Chinese fonts
                "C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei (Chinese Simplified)
                "C:/Windows/Fonts/msjh.ttc",  # Microsoft JhengHei (Chinese Traditional)
                "C:/Windows/Fonts/simsun.ttc",  # SimSun (Chinese legacy)
                "C:/Windows/Fonts/simhei.ttf",  # SimHei (Chinese bold)
                
                # Japanese fonts
                "C:/Windows/Fonts/msgothic.ttc",  # MS Gothic (Japanese)
                "C:/Windows/Fonts/msmincho.ttc",  # MS Mincho (Japanese)
                "C:/Windows/Fonts/YuGothR.ttc",  # Yu Gothic (Japanese modern)
                
                # Korean fonts
                "C:/Windows/Fonts/malgun.ttf",  # Malgun Gothic (Korean)
                "C:/Windows/Fonts/gulim.ttc",  # Gulim (Korean legacy)
                
                # Universal fonts
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf",
                "C:/Windows/Fonts/tahoma.ttf",  # Good Unicode coverage
                "C:/Windows/Fonts/times.ttf"
            ]
        
        # Try each font path
        for font_path in unicode_fonts:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, size)
                    logger.info(f"Using Unicode fallback font: {font_path}")
                    return font
            except Exception as e:
                logger.debug(f"Failed to load Unicode font {font_path}: {e}")
                continue
        
        # If no TrueType fonts work, create a simple Unicode-capable font
        # by using PIL's better default
        try:
            # Try to use the better default font with specified size
            font = ImageFont.load_default()
            # Convert to TrueType if possible to handle Unicode better
            return font
        except Exception:
            # Last resort: return a simple font that won't crash on Unicode
            logger.warning("No Unicode fonts available, text rendering may fail for non-ASCII characters")
            return ImageFont.load_default()
    
    def _detect_text_language(self, text: str) -> str:
        """
        Detect the primary language/script of the text to choose appropriate font.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code: 'cjk' (Chinese/Japanese/Korean), 'latin', 'mixed'
        """
        if not text:
            return 'latin'
            
        cjk_count = 0
        latin_count = 0
        
        for char in text:
            # Chinese characters (Simplified & Traditional)
            if '\u4e00' <= char <= '\u9fff':
                cjk_count += 1
            # Japanese Hiragana & Katakana
            elif '\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff':
                cjk_count += 1
            # Korean Hangul
            elif '\uac00' <= char <= '\ud7af' or '\u1100' <= char <= '\u11ff':
                cjk_count += 1
            # Latin characters
            elif char.isalpha() and ord(char) < 256:
                latin_count += 1
        
        if cjk_count > 0 and latin_count > 0:
            return 'mixed'
        elif cjk_count > 0:
            return 'cjk'
        else:
            return 'latin'
    
    def _get_best_font_for_language(self, text: str, size: int) -> ImageFont.ImageFont:
        """
        Get the best font for the given text based on language detection.
        
        Args:
            text: Text to render
            size: Font size
            
        Returns:
            Best available font for the text
        """
        language = self._detect_text_language(text)
        import platform
        system = platform.system().lower()
        
        # Priority fonts by language and platform
        priority_fonts = []
        
        if language == 'cjk' or language == 'mixed':
            if system == "darwin":  # macOS
                priority_fonts = [
                    "/System/Library/Fonts/PingFang.ttc",  # Best for Chinese
                    "/System/Library/Fonts/Hiragino Sans GB.ttc",  # Chinese Simplified
                    "/System/Library/Fonts/Hiragino Sans.ttc",  # Japanese
                    "/Library/Fonts/Arial Unicode MS.ttf"  # Universal fallback
                ]
            elif system == "linux":
                priority_fonts = [
                    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
                ]
            elif system == "windows":
                priority_fonts = [
                    "C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei
                    "C:/Windows/Fonts/simsun.ttc"  # SimSun
                ]
        
        # Try priority fonts first
        for font_path in priority_fonts:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, size)
                    # Test if font can render the text
                    try:
                        font.getbbox(text)
                        logger.info(f"Selected optimal font for {language} text: {font_path}")
                        return font
                    except Exception:
                        continue
            except Exception:
                continue
        
        # Fallback to general Unicode font selection
        return self._get_unicode_fallback_font(size)
    
    def _ensure_text_compatibility(self, text: str, font: ImageFont.ImageFont) -> str:
        """
        Ensure text is compatible with the given font to prevent encoding errors.
        
        Args:
            text: Original text to render
            font: PIL font object
            
        Returns:
            Text that's safe to render with the font
        """
        try:
            # Test if the font can handle the text by trying to get text size
            font.getbbox(text)
            return text
        except Exception as e:
            logger.warning(f"Font cannot render text '{text[:20]}...': {e}")
            
            # Try to filter out problematic characters
            safe_chars = []
            for char in text:
                try:
                    font.getbbox(char)
                    safe_chars.append(char)
                except Exception:
                    # Replace problematic characters with question marks
                    safe_chars.append('?')
            
            safe_text = ''.join(safe_chars)
            logger.info(f"Converted text to font-safe version: '{safe_text[:20]}...'")
            return safe_text
    
    def render_text_to_region(
        self, 
        image_path: str, 
        text_region: TextRegion, 
        text: str, 
        font_properties: Optional[FontProperties] = None,
        output_dir: str = "processed"
    ) -> str:
        """
        Render text to a specific region in an image.
        
        Args:
            image_path: Path to the source image
            text_region: TextRegion defining where to place the text
            text: Text content to render
            font_properties: Font properties (auto-estimated if None)
            output_dir: Directory to save the result
            
        Returns:
            Path to the image with rendered text
        """
        try:
            # Load source image
            image = Image.open(image_path).convert("RGB")
            
            # Auto-estimate font properties if not provided
            if font_properties is None:
                font_properties = self.font_analyzer.estimate_font_properties(text_region, image_path)
                # Auto-adjust font size to fit the region
                optimal_size = self.font_analyzer.auto_adjust_font_size(text_region, text)
                font_properties.size = optimal_size
            
            # Get font object
            font = self._get_font(font_properties)
            if font is None:
                raise ValueError("Could not load any font")
            
            # Create drawing context
            draw = ImageDraw.Draw(image)
            
            # Calculate center position of the region for PIL anchor
            bbox = text_region.bounding_box
            text_x = bbox.x + bbox.width // 2  # Center X
            text_y = bbox.y + bbox.height // 2  # Center Y
            
            # Parse color
            text_color = self._parse_color(font_properties.color)
            
            # Draw text with Unicode safety
            safe_text = self._ensure_text_compatibility(text, font)
            
            # Debug logging for PIL anchor positioning
            if self.debug_positioning:
                font_ascent, font_descent = font.getmetrics()
                logger.info(f"PIL anchor positioning debug for '{text[:10]}...':")
                logger.info(f"  Region: ({bbox.x}, {bbox.y}, {bbox.width}, {bbox.height})")
                logger.info(f"  Font metrics: ascent={font_ascent}, descent={font_descent}")
                logger.info(f"  Anchor position (mm): ({text_x}, {text_y})")
                logger.info(f"  Using PIL anchor='mm' for center alignment")
            
            # Use PIL's native middle-middle anchor for precise center alignment
            draw.text((text_x, text_y), safe_text, font=font, fill=text_color, anchor="mm")
            
            # Generate output path
            input_filename = Path(image_path).stem
            output_filename = f"{input_filename}_text_{uuid.uuid4().hex[:8]}.png"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)
            
            # Save result
            image.save(output_path, "PNG")
            
            logger.info(f"Text rendered successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Text rendering failed: {e}")
            raise
    
    def render_multiple_texts(
        self, 
        image_path: str, 
        text_regions_with_text: List[Tuple[TextRegion, str, Optional[FontProperties]]], 
        output_dir: str = "processed"
    ) -> str:
        """
        Render multiple texts to their respective regions in an image.
        
        Args:
            image_path: Path to the source image
            text_regions_with_text: List of (TextRegion, text, FontProperties) tuples
            output_dir: Directory to save the result
            
        Returns:
            Path to the image with all texts rendered
        """
        try:
            # Load source image
            image = Image.open(image_path).convert("RGB")
            draw = ImageDraw.Draw(image)
            
            # Render each text
            for text_region, text, font_properties in text_regions_with_text:
                if not text or not text.strip():
                    continue
                
                # Auto-estimate font properties if not provided
                if font_properties is None:
                    font_properties = self.font_analyzer.estimate_font_properties(text_region, image_path)
                    # Auto-adjust font size
                    optimal_size = self.font_analyzer.auto_adjust_font_size(text_region, text)
                    font_properties.size = optimal_size
                
                # Get font with text-aware selection and render text
                font = self._get_font(font_properties, text)
                if font is None:
                    logger.warning(f"Skipping text rendering for region {text_region.id}: no font available")
                    continue
                
                # Calculate center position of the region for PIL anchor
                bbox = text_region.bounding_box
                text_x = bbox.x + bbox.width // 2  # Center X
                text_y = bbox.y + bbox.height // 2  # Center Y
                
                # Parse color and draw with Unicode safety
                text_color = self._parse_color(font_properties.color)
                safe_text = self._ensure_text_compatibility(text, font)
                
                # Debug logging for PIL anchor positioning
                if self.debug_positioning:
                    font_ascent, font_descent = font.getmetrics()
                    logger.info(f"PIL anchor positioning debug for '{text[:10]}...':")
                    logger.info(f"  Region: ({bbox.x}, {bbox.y}, {bbox.width}, {bbox.height})")
                    logger.info(f"  Font metrics: ascent={font_ascent}, descent={font_descent}")
                    logger.info(f"  Anchor position (mm): ({text_x}, {text_y})")
                    logger.info(f"  Using PIL anchor='mm' for center alignment")
                
                # Use PIL's native middle-middle anchor for precise center alignment
            draw.text((text_x, text_y), safe_text, font=font, fill=text_color, anchor="mm")
                
            logger.info(f"Rendered text '{text[:20]}...' in region {text_region.id}")
            
            # Generate output path
            input_filename = Path(image_path).stem
            output_filename = f"{input_filename}_texts_{uuid.uuid4().hex[:8]}.png"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)
            
            # Save result
            image.save(output_path, "PNG")
            
            logger.info(f"Multiple texts rendered successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Multiple text rendering failed: {e}")
            raise
    
    
    def _parse_color(self, color_str: str) -> Tuple[int, int, int]:
        """
        Parse color string to RGB tuple.
        
        Args:
            color_str: Color string ("black", "white", "#FF0000", etc.)
            
        Returns:
            RGB tuple
        """
        color_map = {
            "black": (0, 0, 0),
            "white": (255, 255, 255),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "gray": (128, 128, 128),
            "grey": (128, 128, 128)
        }
        
        # Handle named colors
        if color_str.lower() in color_map:
            return color_map[color_str.lower()]
        
        # Handle hex colors
        if color_str.startswith("#") and len(color_str) == 7:
            try:
                r = int(color_str[1:3], 16)
                g = int(color_str[3:5], 16)
                b = int(color_str[5:7], 16)
                return (r, g, b)
            except ValueError:
                pass
        
        # Default to black
        return (0, 0, 0)
    
    def preview_text_in_region(
        self, 
        image_path: str, 
        text_region: TextRegion, 
        text: str,
        font_properties: Optional[FontProperties] = None
    ) -> Dict:
        """
        Preview how text will look in a region without actually rendering it.
        
        Args:
            image_path: Path to the source image
            text_region: TextRegion to preview text in
            text: Text to preview
            font_properties: Font properties
            
        Returns:
            Dictionary with preview information
        """
        try:
            # Auto-estimate font properties if not provided
            if font_properties is None:
                font_properties = self.font_analyzer.estimate_font_properties(text_region, image_path)
                optimal_size = self.font_analyzer.auto_adjust_font_size(text_region, text)
                font_properties.size = optimal_size
            
            # Get font with text-aware selection
            font = self._get_font(font_properties, text)
            if font is None:
                return {"error": "Could not load font"}
            
            # Calculate dimensions
            text_bbox = font.getbbox(text)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Calculate center position for PIL anchor
            bbox = text_region.bounding_box
            text_x = bbox.x + bbox.width // 2  # Center X
            text_y = bbox.y + bbox.height // 2  # Center Y
            
            # Check if text fits
            fits_horizontally = text_width <= bbox.width
            fits_vertically = text_height <= bbox.height
            
            return {
                "text_width": text_width,
                "text_height": text_height,
                "position": {"x": text_x, "y": text_y},
                "font_properties": font_properties.to_dict(),
                "fits_horizontally": fits_horizontally,
                "fits_vertically": fits_vertically,
                "fits_completely": fits_horizontally and fits_vertically
            }
            
        except Exception as e:
            logger.error(f"Text preview failed: {e}")
            return {"error": str(e)}