"""Simple font analysis module for estimating font properties from text regions."""
import cv2
import numpy as np
from typing import Dict, Optional, List
from PIL import Image, ImageFont
from pathlib import Path
from loguru import logger

from app.domain.entities.text_region import TextRegion


class FontProperties:
    """Font properties data class."""
    
    def __init__(
        self, 
        size: int, 
        type: str = "proportional", 
        color: str = "black",
        family: str = "Arial",
        style: str = "normal"
    ):
        self.size = size
        self.type = type  # "monospace" or "proportional"
        self.color = color
        self.family = family
        self.style = style  # "normal", "bold", "italic"
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'size': self.size,
            'type': self.type,
            'color': self.color,
            'family': self.family,
            'style': self.style
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FontProperties':
        """Create from dictionary."""
        return cls(
            size=data.get('size', 12),
            type=data.get('type', 'proportional'),
            color=data.get('color', 'black'),
            family=data.get('family', 'Arial'),
            style=data.get('style', 'normal')
        )
    
    def scale_for_box_size(self, original_box: Dict, new_box: Dict) -> 'FontProperties':
        """Scale font properties based on box size changes."""
        if not original_box or not new_box:
            return self
        
        # Calculate scaling factors
        scale_x = new_box.get('width', 1) / original_box.get('width', 1)
        scale_y = new_box.get('height', 1) / original_box.get('height', 1)
        
        # Use average scaling to maintain aspect ratio
        avg_scale = (scale_x + scale_y) / 2
        
        # Apply scaling to font size
        # Allow smaller fonts for intentional downsizing, but prevent extremely small fonts
        scaled_size = max(4, int(self.size * avg_scale))
        
        return FontProperties(
            size=scaled_size,
            type=self.type,
            color=self.color,
            family=self.family,
            style=self.style
        )


class SimpleFontAnalyzer:
    """Simple font analyzer using traditional computer vision methods."""
    
    def __init__(self):
        """Initialize font analyzer."""
        self.default_fonts = ['Arial', 'Times New Roman', 'Courier New', 'Helvetica']
        logger.info("SimpleFontAnalyzer initialized")
    
    def estimate_font_properties(self, text_region: TextRegion, image_path: Optional[str] = None) -> FontProperties:
        """
        Estimate font properties from text region using lightweight methods.
        
        Args:
            text_region: TextRegion with bounding box information
            image_path: Optional path to original image for advanced analysis
            
        Returns:
            FontProperties with estimated font characteristics
        """
        try:
            bbox = text_region.bounding_box
            original_text = text_region.original_text or "Sample"
            
            # Basic font size estimation from bounding box height
            # Font size ≈ bounding box height × 0.75 (empirical ratio)
            # Allow smaller font sizes for small text regions
            estimated_size = max(6, int(bbox.height * 0.75))
            
            # Font type estimation based on width-to-height ratio
            if len(original_text) > 0:
                char_width = bbox.width / len(original_text)
                width_height_ratio = char_width / bbox.height
                
                # Monospace fonts typically have width/height ratio > 0.6
                font_type = "monospace" if width_height_ratio > 0.6 else "proportional"
            else:
                font_type = "proportional"
            
            # Advanced analysis if image is provided
            if image_path and Path(image_path).exists():
                advanced_props = self._analyze_from_image(text_region, image_path)
                if advanced_props:
                    estimated_size = advanced_props.get('size', estimated_size)
                    font_type = advanced_props.get('type', font_type)
            
            # Create font properties
            font_props = FontProperties(
                size=estimated_size,
                type=font_type,
                color="black",  # Default color
                family=self._suggest_font_family(font_type),
                style="normal"  # Default style
            )
            
            logger.info(
                f"Estimated font properties for region {text_region.id}: "
                f"size={font_props.size}, type={font_props.type}, family={font_props.family}"
            )
            
            return font_props
            
        except Exception as e:
            logger.warning(f"Font analysis failed for region {text_region.id}: {e}")
            # Return default properties
            return FontProperties(size=12, type="proportional")
    
    def _analyze_from_image(self, text_region: TextRegion, image_path: str) -> Optional[Dict]:
        """
        Advanced font analysis using image processing.
        
        Args:
            text_region: TextRegion to analyze
            image_path: Path to the source image
            
        Returns:
            Dictionary with refined font properties or None if analysis fails
        """
        try:
            # Load image and extract region
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            bbox = text_region.bounding_box
            x, y = int(bbox.x), int(bbox.y)
            w, h = int(bbox.width), int(bbox.height)
            
            # Ensure coordinates are within image bounds
            img_h, img_w = image.shape[:2]
            x = max(0, min(x, img_w - 1))
            y = max(0, min(y, img_h - 1))
            w = max(1, min(w, img_w - x))
            h = max(1, min(h, img_h - y))
            
            # Extract region of interest
            roi = image[y:y+h, x:x+w]
            
            # Convert to grayscale
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Binary threshold
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            # Find contours to analyze individual characters
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Analyze character dimensions
                char_heights = []
                char_widths = []
                
                for contour in contours:
                    x_c, y_c, w_c, h_c = cv2.boundingRect(contour)
                    if w_c > 2 and h_c > 2:  # Filter out noise
                        char_heights.append(h_c)
                        char_widths.append(w_c)
                
                if char_heights:
                    avg_char_height = sum(char_heights) / len(char_heights)
                    avg_char_width = sum(char_widths) / len(char_widths)
                    
                    # More accurate font size estimation
                    refined_size = max(6, int(avg_char_height * 0.8))
                    
                    # Refined font type analysis
                    width_variance = np.var(char_widths) if len(char_widths) > 1 else 0
                    is_monospace = width_variance < (avg_char_width * 0.1)  # Low variance = monospace
                    
                    return {
                        'size': refined_size,
                        'type': 'monospace' if is_monospace else 'proportional'
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"Advanced image analysis failed: {e}")
            return None
    
    def _suggest_font_family(self, font_type: str) -> str:
        """
        Suggest appropriate font family based on font type.
        
        Args:
            font_type: "monospace" or "proportional"
            
        Returns:
            Suggested font family name
        """
        if font_type == "monospace":
            return "Courier New"
        else:
            return "Arial"
    
    def validate_font_size_for_region(self, font_size: int, region: TextRegion, text: str) -> bool:
        """
        Validate if the estimated font size will fit in the region.
        
        Args:
            font_size: Proposed font size
            region: Target text region
            text: Text to be rendered
            
        Returns: 
            True if font size is appropriate for the region
        """
        try:
            # Use PIL to measure text dimensions
            font = ImageFont.truetype("arial.ttf", font_size)
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Check if text fits with some padding (90% of region size)
            fits_width = text_width <= (region.bounding_box.width * 0.9)
            fits_height = text_height <= (region.bounding_box.height * 0.9)
            
            return fits_width and fits_height
            
        except Exception as e:
            logger.debug(f"Font validation failed: {e}")
            # Conservative approach: assume it fits if we can't validate
            return True
    
    def auto_adjust_font_size(self, region: TextRegion, text: str, max_size: int = 72) -> int:
        """
        Automatically find the best font size that fits in the region.
        
        Args:
            region: Target text region
            text: Text to be rendered
            max_size: Maximum font size to try
            
        Returns:
            Optimal font size
        """
        # Start with estimated size
        estimated_props = self.estimate_font_properties(region)
        start_size = min(estimated_props.size, max_size)
        
        # Binary search for optimal size
        min_size = 8
        max_test_size = min(max_size, int(region.bounding_box.height))
        
        best_size = min_size
        
        for size in range(start_size, min_size - 1, -1):
            if self.validate_font_size_for_region(size, region, text):
                best_size = size
                break
        
        # If starting size was too small, try increasing
        if best_size == min_size:
            for size in range(start_size, max_test_size + 1):
                if self.validate_font_size_for_region(size, region, text):
                    best_size = size
                else:
                    break
        
        logger.info(f"Auto-adjusted font size for region {region.id}: {best_size}")
        return best_size