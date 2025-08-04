"""Image scaling service for handling large images."""
import base64
import io
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image
import numpy as np
from loguru import logger

from app.models.schemas import TextRegionSchema


class ImageScaler:
    """Service for scaling images and adjusting text regions accordingly."""
    
    def __init__(self, max_dimension: int = 1024, region_expand_ratio: float = 0.1):
        """
        Initialize image scaler.
        
        Args:
            max_dimension: Maximum allowed dimension for image processing
            region_expand_ratio: Ratio to expand regions (0.1 = 10% expansion)
        """
        self.max_dimension = max_dimension
        self.region_expand_ratio = region_expand_ratio
        logger.info(f"ImageScaler initialized with max dimension: {max_dimension}, "
                   f"region expand ratio: {region_expand_ratio}")
    
    def calculate_scale_factor(self, width: int, height: int) -> float:
        """
        Calculate scale factor to fit image within max dimension.
        
        Args:
            width: Original image width
            height: Original image height
            
        Returns:
            Scale factor (1.0 if no scaling needed, <1.0 if scaling down)
        """
        max_current = max(width, height)
        
        if max_current <= self.max_dimension:
            return 1.0
        
        scale_factor = self.max_dimension / max_current
        logger.info(f"Calculated scale factor: {scale_factor:.3f} for image {width}x{height}")
        return scale_factor
    
    def scale_image_base64(self, image_b64: str) -> Tuple[str, float, Tuple[int, int], Tuple[int, int]]:
        """
        Scale base64 encoded image if needed.
        
        Args:
            image_b64: Base64 encoded image
            
        Returns:
            Tuple of (scaled_image_b64, scale_factor, original_size, new_size)
        """
        try:
            # Decode image
            image_data = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            original_size = image.size  # (width, height)
            
            # Calculate scale factor
            scale_factor = self.calculate_scale_factor(original_size[0], original_size[1])
            
            if scale_factor == 1.0:
                logger.info(f"Image {original_size} is within limits, no scaling needed")
                return image_b64, scale_factor, original_size, original_size
            
            # Calculate new dimensions
            new_width = int(original_size[0] * scale_factor)
            new_height = int(original_size[1] * scale_factor)
            new_size = (new_width, new_height)
            
            logger.info(f"Scaling image from {original_size} to {new_size} (scale: {scale_factor:.3f})")
            
            # Scale image using high-quality resampling
            scaled_image = image.resize(new_size, Image.LANCZOS)
            
            # Convert back to base64
            buffer = io.BytesIO()
            scaled_image.save(buffer, format='PNG', optimize=True)
            scaled_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            logger.info(f"Image scaled successfully: {original_size} -> {new_size}")
            return scaled_b64, scale_factor, original_size, new_size
            
        except Exception as e:
            logger.error(f"Failed to scale image: {e}")
            raise Exception(f"Image scaling failed: {e}")
    
    def scale_regions(self, regions: List[TextRegionSchema], scale_factor: float, 
                     image_size: Optional[Tuple[int, int]] = None, 
                     expand_regions: bool = True) -> List[TextRegionSchema]:
        """
        Scale text regions coordinates according to scale factor and optionally expand them.
        
        Args:
            regions: List of text regions to scale
            scale_factor: Scale factor to apply
            image_size: Scaled image size (width, height) for boundary checking
            expand_regions: Whether to expand regions after scaling
            
        Returns:
            List of scaled and optionally expanded text regions
        """
        if scale_factor == 1.0 and not expand_regions:
            logger.info("Scale factor is 1.0 and no expansion needed, returning original regions")
            return regions
        
        scaled_regions = []
        expanded_count = 0
        
        for region in regions:
            try:
                # Handle both dict and object formats
                if isinstance(region, dict):
                    # Dict format - first apply scaling
                    scaled_x = int(region["x"] * scale_factor)
                    scaled_y = int(region["y"] * scale_factor)
                    scaled_width = max(1, int(region["width"] * scale_factor))
                    scaled_height = max(1, int(region["height"] * scale_factor))
                    
                    # Apply expansion if enabled and we have scaling
                    if expand_regions and scale_factor < 1.0:
                        expand_w = int(scaled_width * self.region_expand_ratio)
                        expand_h = int(scaled_height * self.region_expand_ratio)
                        
                        # Expand region while keeping it within image bounds
                        new_x = max(0, scaled_x - expand_w // 2)
                        new_y = max(0, scaled_y - expand_h // 2)
                        new_width = scaled_width + expand_w
                        new_height = scaled_height + expand_h
                        
                        # Ensure we don't exceed image boundaries
                        if image_size:
                            img_width, img_height = image_size
                            new_width = min(new_width, img_width - new_x)
                            new_height = min(new_height, img_height - new_y)
                        
                        scaled_region = {
                            "x": new_x,
                            "y": new_y,
                            "width": max(1, new_width),
                            "height": max(1, new_height)
                        }
                        expanded_count += 1
                    else:
                        scaled_region = {
                            "x": scaled_x,
                            "y": scaled_y,
                            "width": scaled_width,
                            "height": scaled_height
                        }
                    
                    # Copy other fields if they exist
                    for key in region:
                        if key not in ["x", "y", "width", "height"]:
                            scaled_region[key] = region[key]
                else:
                    # Object format - first apply scaling
                    scaled_x = int(region.x * scale_factor)
                    scaled_y = int(region.y * scale_factor)
                    scaled_width = max(1, int(region.width * scale_factor))
                    scaled_height = max(1, int(region.height * scale_factor))
                    
                    # Apply expansion if enabled and we have scaling
                    if expand_regions and scale_factor < 1.0:
                        expand_w = int(scaled_width * self.region_expand_ratio)
                        expand_h = int(scaled_height * self.region_expand_ratio)
                        
                        # Expand region while keeping it within image bounds
                        new_x = max(0, scaled_x - expand_w // 2)
                        new_y = max(0, scaled_y - expand_h // 2)
                        new_width = scaled_width + expand_w
                        new_height = scaled_height + expand_h
                        
                        # Ensure we don't exceed image boundaries
                        if image_size:
                            img_width, img_height = image_size
                            new_width = min(new_width, img_width - new_x)
                            new_height = min(new_height, img_height - new_y)
                        
                        region_dict = region.dict() if hasattr(region, 'dict') else region.__dict__
                        region_dict.update({
                            'x': new_x,
                            'y': new_y,
                            'width': max(1, new_width),
                            'height': max(1, new_height)
                        })
                        expanded_count += 1
                    else:
                        region_dict = region.dict() if hasattr(region, 'dict') else region.__dict__
                        region_dict.update({
                            'x': scaled_x,
                            'y': scaled_y,
                            'width': scaled_width,
                            'height': scaled_height
                        })
                    
                    scaled_region = TextRegionSchema(**region_dict)
                
                scaled_regions.append(scaled_region)
                
                # Get values for debugging
                orig_x = region.get('x') if isinstance(region, dict) else getattr(region, 'x', 0)
                orig_y = region.get('y') if isinstance(region, dict) else getattr(region, 'y', 0)
                orig_w = region.get('width') if isinstance(region, dict) else getattr(region, 'width', 0)
                orig_h = region.get('height') if isinstance(region, dict) else getattr(region, 'height', 0)
                
                final_x = scaled_region.get('x') if isinstance(scaled_region, dict) else getattr(scaled_region, 'x', 0)
                final_y = scaled_region.get('y') if isinstance(scaled_region, dict) else getattr(scaled_region, 'y', 0)
                final_w = scaled_region.get('width') if isinstance(scaled_region, dict) else getattr(scaled_region, 'width', 0)
                final_h = scaled_region.get('height') if isinstance(scaled_region, dict) else getattr(scaled_region, 'height', 0)
                
                logger.debug(f"Processed region: ({orig_x}, {orig_y}, {orig_w}, {orig_h}) -> "
                           f"({final_x}, {final_y}, {final_w}, {final_h})")
                
            except Exception as e:
                logger.error(f"Failed to process region {region}: {e}")
                # Keep original region if processing fails
                scaled_regions.append(region)
        
        if scale_factor < 1.0:
            logger.info(f"Scaled {len(regions)} regions with factor {scale_factor:.3f}")
        if expanded_count > 0:
            logger.info(f"Expanded {expanded_count} regions by {self.region_expand_ratio:.1%} "
                       f"for better text coverage")
        
        return scaled_regions
    
    def scale_result_back(self, result_bytes: bytes, original_size: Tuple[int, int], 
                         scaled_size: Tuple[int, int]) -> bytes:
        """
        Scale processed result image back to original size.
        
        Args:
            result_bytes: Processed image bytes from IOPaint
            original_size: Original image size (width, height)
            scaled_size: Scaled image size (width, height)
            
        Returns:
            Result image bytes scaled back to original size
        """
        try:
            if original_size == scaled_size:
                logger.info("Original and scaled sizes are the same, no upscaling needed")
                return result_bytes
            
            # Load processed image
            result_image = Image.open(io.BytesIO(result_bytes)).convert("RGB")
            
            logger.info(f"Scaling result image back from {scaled_size} to {original_size}")
            
            # Scale back to original size using high-quality resampling
            upscaled_image = result_image.resize(original_size, Image.LANCZOS)
            
            # Convert back to bytes
            buffer = io.BytesIO()
            upscaled_image.save(buffer, format='PNG', optimize=True)
            upscaled_bytes = buffer.getvalue()
            
            logger.info(f"Result image upscaled successfully: {scaled_size} -> {original_size}")
            return upscaled_bytes
            
        except Exception as e:
            logger.error(f"Failed to scale result image back: {e}")
            # Return original result if upscaling fails
            logger.warning("Returning processed image at scaled size due to upscaling failure")
            return result_bytes
    
    def get_scaling_info(self, image_b64: str) -> Dict[str, Any]:
        """
        Get scaling information for an image without actually scaling it.
        
        Args:
            image_b64: Base64 encoded image
            
        Returns:
            Dictionary with scaling information
        """
        try:
            # Decode image to get dimensions
            image_data = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            original_size = image.size  # (width, height)
            
            # Calculate scale factor
            scale_factor = self.calculate_scale_factor(original_size[0], original_size[1])
            
            # Calculate new dimensions if scaling would be applied
            new_width = int(original_size[0] * scale_factor)
            new_height = int(original_size[1] * scale_factor)
            new_size = (new_width, new_height)
            
            scaling_needed = scale_factor < 1.0
            
            return {
                "original_size": original_size,
                "new_size": new_size if scaling_needed else original_size,
                "scale_factor": scale_factor,
                "scaling_needed": scaling_needed,
                "max_dimension": self.max_dimension,
                "current_max_dimension": max(original_size),
                "megapixels": (original_size[0] * original_size[1]) / 1000000
            }
            
        except Exception as e:
            logger.error(f"Failed to get scaling info: {e}")
            raise Exception(f"Failed to analyze image for scaling: {e}")


# Global image scaler instance
image_scaler = ImageScaler(max_dimension=1024, region_expand_ratio=0.1)