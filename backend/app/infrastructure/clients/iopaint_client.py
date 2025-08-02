"""IOPaint service client for text inpainting and removal."""
import base64
import uuid
import asyncio
import time
from typing import List, Optional
from pathlib import Path
import aiohttp
import aiofiles
from PIL import Image
import numpy as np
from loguru import logger

from app.domain.entities.text_region import TextRegion
from app.application.interfaces.image_service import InpaintingServicePort
from app.config.settings import settings


class IOPaintClient(InpaintingServicePort):
    """Client for IOPaint microservice."""
    
    def __init__(self, base_url: str = None, timeout: int = None):
        """Initialize IOPaint client."""
        self.base_url = base_url or f"http://iopaint-service:{settings.iopaint_port}"
        self.timeout = timeout or 300  # 5 minutes default
        
        logger.info(f"Initializing IOPaint client with URL: {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.health_check()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
    
    async def start_service(self):
        """
        Start service - for IOPaint client, this just performs a health check.
        The actual IOPaint service is managed by Docker.
        """
        await self.health_check()
        logger.info("IOPaint service is ready")
    
    async def stop_service(self):
        """
        Stop service - for IOPaint client, this is a no-op.
        The actual IOPaint service is managed by Docker.
        """
        logger.info("IOPaint client shutdown (service managed by Docker)")
    
    async def health_check(self, max_retries: int = 30) -> dict:
        """
        Check if IOPaint service is healthy and ready.
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            Health status dictionary
        """
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/api/v1/health",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            if health_data.get("status") == "healthy":
                                logger.info("IOPaint service is healthy")
                                return health_data
                        
                        logger.warning(f"IOPaint service not ready (status: {response.status})")
                        
            except Exception as e:
                logger.warning(f"Health check attempt {attempt + 1}/{max_retries} failed: {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2)  # Wait 2 seconds between retries
        
        error_msg = f"IOPaint service not available after {max_retries} attempts"
        logger.error(error_msg)
        raise ConnectionError(error_msg)
    
    def create_mask_from_regions(
        self, 
        image_shape: tuple, 
        text_regions: List[TextRegion]
    ) -> np.ndarray:
        """
        Create binary mask from text regions.
        
        Args:
            image_shape: (height, width, channels) of the original image
            text_regions: List of text regions to mask
            
        Returns:
            Binary mask as numpy array
        """
        height, width = image_shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        
        for region in text_regions:
            bbox = region.bounding_box
            
            # Convert coordinates to integers
            x = int(bbox.x)
            y = int(bbox.y)
            w = int(bbox.width)
            h = int(bbox.height)
            
            # Ensure coordinates are within image bounds
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = max(1, min(w, width - x))
            h = max(1, min(h, height - y))
            
            # Fill the region with 255 (white) to indicate inpainting area
            mask[y:y+h, x:x+w] = 255
            
            logger.debug(f"Added mask region: ({x}, {y}, {w}, {h})")
        
        return mask
    
    async def remove_text_regions(
        self,
        image_path: str,
        text_regions: List[TextRegion],
        output_dir: str = "processed"
    ) -> str:
        """
        Remove text regions from image using IOPaint service.
        
        Args:
            image_path: Path to the input image
            text_regions: List of text regions to remove
            output_dir: Directory to save the processed image
            
        Returns:
            Path to the processed image
        """
        start_time = time.time()
        
        try:
            # Load and encode the image
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()
                image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Convert text regions to API format
            regions_data = []
            for region in text_regions:
                bbox = region.bounding_box
                regions_data.append({
                    "x": bbox.x,
                    "y": bbox.y,
                    "width": bbox.width,
                    "height": bbox.height
                })
            
            logger.info(f"Processing image: {image_path}")
            logger.info(f"Text regions to remove: {len(text_regions)}")
            
            # Prepare request payload
            payload = {
                "image": image_b64,
                "regions": regions_data,
                "sd_seed": -1,
                "sd_steps": 25,
                "sd_strength": 1.0,
                "sd_guidance_scale": 7.5,
                "sd_sampler": "ddim",
                "hd_strategy": "Original",
                "hd_strategy_crop_trigger_size": 1280,
                "hd_strategy_crop_margin": 32,
                "prompt": "",
                "negative_prompt": ""
            }
            
            # Call IOPaint service
            logger.info("Starting text inpainting with IOPaint service...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v1/inpaint-regions",
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        # Generate output filename
                        input_filename = Path(image_path).stem
                        output_filename = f"{input_filename}_iopaint_{uuid.uuid4().hex[:8]}.png"
                        
                        # Ensure output directory exists
                        import os
                        os.makedirs(output_dir, exist_ok=True)
                        output_path = os.path.join(output_dir, output_filename)
                        
                        # Save the result image
                        async with aiofiles.open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        processing_time = time.time() - start_time
                        logger.info(f"Text removal completed in {processing_time:.2f}s: {output_path}")
                        
                        return output_path
                    else:
                        # Handle errors
                        try:
                            error_data = await response.json()
                            error_text = error_data.get('detail', 'Unknown error')
                        except Exception:
                            try:
                                error_text = await response.text()
                            except UnicodeDecodeError:
                                error_text = f"Binary response content (status: {response.status})"
                        raise Exception(f"IOPaint service error: {response.status} - {error_text}")
            
        except Exception as e:
            logger.error(f"Error during text removal: {e}")
            raise
    
    def validate_regions_for_inpainting(self, regions: List[TextRegion]) -> dict:
        """
        Validate regions and provide recommendations for inpainting.
        
        Args:
            regions: List of text regions to validate
            
        Returns:
            Dictionary with validation results and recommendations
        """
        issues = []
        recommendations = []
        warnings = []
        
        if not regions:
            issues.append("No text regions provided")
            return {
                'valid': False,
                'issues': issues,
                'recommendations': recommendations,
                'warnings': warnings
            }
        
        # Validate each region
        for i, region in enumerate(regions):
            # Check region area
            area = region.get_area()
            if area < 10:
                issues.append(f"Region {i+1} is too small (area: {area})")
            elif area > 1000000:
                warnings.append(f"Region {i+1} is very large (area: {area}) - may affect quality")
            
            # Check bounding box validity
            bbox = region.bounding_box
            if bbox.width <= 0 or bbox.height <= 0:
                issues.append(f"Region {i+1} has invalid dimensions: {bbox.width}x{bbox.height}")
            
            # Check confidence for automatic detections
            if not region.is_user_modified and region.confidence < 0.3:
                warnings.append(f"Region {i+1} has low confidence ({region.confidence:.2f})")
        
        # Check for overlapping regions
        overlapping_pairs = self._find_overlapping_regions(regions)
        if overlapping_pairs:
            recommendations.append(f"Found {len(overlapping_pairs)} overlapping region pairs - consider merging")
        
        # Provide recommendations based on region count
        if len(regions) > 20:
            recommendations.append("Many regions detected - processing may take longer")
        elif len(regions) > 50:
            warnings.append("Very high number of regions - consider filtering low-confidence detections")
        
        # Check region distribution
        user_modified_count = sum(1 for r in regions if r.is_user_modified)
        if user_modified_count > 0:
            recommendations.append(f"{user_modified_count} user-modified regions will be prioritized")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'recommendations': recommendations,
            'warnings': warnings,
            'stats': {
                'total_regions': len(regions),
                'user_modified': user_modified_count,
                'avg_confidence': sum(r.confidence for r in regions) / len(regions),
                'total_area': sum(r.get_area() for r in regions),
                'overlapping_pairs': len(overlapping_pairs)
            }
        }
    
    def _find_overlapping_regions(self, regions: List[TextRegion]) -> List[tuple]:
        """Find overlapping region pairs."""
        overlapping = []
        
        for i, region1 in enumerate(regions):
            for j, region2 in enumerate(regions[i+1:], i+1):
                if self._regions_overlap(region1, region2):
                    overlapping.append((i, j))
        
        return overlapping
    
    def _regions_overlap(self, region1: TextRegion, region2: TextRegion) -> bool:
        """Check if two regions overlap."""
        bbox1 = region1.bounding_box
        bbox2 = region2.bounding_box
        
        # Check if rectangles overlap
        return not (
            bbox1.x + bbox1.width < bbox2.x or
            bbox2.x + bbox2.width < bbox1.x or
            bbox1.y + bbox1.height < bbox2.y or
            bbox2.y + bbox2.height < bbox1.y
        )
    
    async def get_model_info(self) -> dict:
        """Get information about the current model from IOPaint service."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v1/model",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        model_info = await response.json()
                        return {
                            "model_name": model_info.get("name", "unknown"),
                            "device": model_info.get("device", "unknown"),
                            "status": model_info.get("status", "unknown"),
                            "model_info": model_info
                        }
        except Exception as e:
            logger.error(f"Failed to get model info from IOPaint service: {e}")
        
        return {
            "model_name": "unknown",
            "device": "unknown", 
            "status": "error"
        }
    
    async def inpaint_regions_async(
        self,
        image_path: str,
        text_regions: List[dict],
        inpainting_method: str = "iopaint",
        custom_radius: Optional[int] = None,
        task_id: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Start async text removal processing with IOPaint service.
        
        Args:
            image_path: Path to the image file
            text_regions: List of text region dictionaries
            inpainting_method: IOPaint method to use
            custom_radius: Custom inpainting radius
            
        Returns:
            Response from IOPaint service containing IOPaint-generated task_id
        """
        try:
            # Use provided task_id or generate new one
            unified_task_id = task_id or str(uuid.uuid4())
            
            # Convert image to base64
            image_b64 = await self._image_to_base64(image_path)
            
            # Convert text regions to IOPaint region format
            regions = []
            for region in text_regions:
                regions.append({
                    "x": region["bounding_box"]["x"],
                    "y": region["bounding_box"]["y"],
                    "width": region["bounding_box"]["width"],
                    "height": region["bounding_box"]["height"]
                })
            
            # Prepare request data according to AsyncInpaintRequest schema
            request_data = {
                "image": image_b64,
                "regions": regions,
                "enable_progress": True,
                "progress_interval": 1.0,
                "callback_url": f"http://backend:8000/api/v1/iopaint/callback/{unified_task_id}",
                "task_id": unified_task_id  # Pass unified task_id to IOPaint
            }
            
            # IOPaint parameters
            if inpainting_method == "iopaint":
                request_data.update({
                    "sd_seed": -1,
                    "sd_steps": 25,
                    "sd_strength": 1.0,
                    "sd_guidance_scale": 7.5,
                    "sd_sampler": "ddim",
                    "hd_strategy": "Original",
                    "hd_strategy_crop_trigger_size": 1280,
                    "hd_strategy_crop_margin": 32,
                    "prompt": "",
                    "negative_prompt": ""
                })
            
            logger.info(f"Starting async IOPaint processing")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v1/inpaint-regions-async",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status in [200, 202]:  # OK or Accepted
                        result = await response.json()
                        returned_task_id = result.get('task_id')
                        logger.info(f"IOPaint async processing started - Unified task_id: {unified_task_id}, Returned task_id: {returned_task_id}")
                        
                        # Return unified task information
                        return {
                            "status": result.get("status"),
                            "message": result.get("message"),
                            "task_id": unified_task_id,  # Use unified task_id consistently
                            "websocket_url": result.get("websocket_url")
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"IOPaint async request failed: {response.status} - {error_text}")
                        return {
                            "status": "error",
                            "message": f"IOPaint service error: {response.status}",
                            "details": error_text
                        }
                        
        except Exception as e:
            logger.error(f"Failed to start async IOPaint processing: {e}")
            return {
                "status": "error",
                "message": f"Failed to start async processing: {str(e)}"
            }
    
    async def get_task_status(self, task_id: str) -> dict:
        """
        Get status of an async processing task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status information
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v1/task-status/{task_id}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return result
                    elif response.status == 404:
                        return {
                            "status": "not_found",
                            "message": f"Task {task_id} not found"
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get task status: {response.status} - {error_text}")
                        return {
                            "status": "error",
                            "message": f"Failed to get task status: {response.status}"
                        }
                        
        except Exception as e:
            logger.error(f"Failed to get task status for {task_id}: {e}")
            return {
                "status": "error",
                "message": f"Failed to get task status: {str(e)}"
            }
    
    async def cancel_task(self, task_id: str) -> dict:
        """
        Cancel an async processing task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Cancellation result
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v1/cancel-task/{task_id}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Task {task_id} cancellation requested")
                        return result
                    elif response.status == 404:
                        return {
                            "status": "not_found",
                            "message": f"Task {task_id} not found"
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to cancel task: {response.status} - {error_text}")
                        return {
                            "status": "error",
                            "message": f"Failed to cancel task: {response.status}"
                        }
                        
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return {
                "status": "error",
                "message": f"Failed to cancel task: {str(e)}"
            }
    
    async def _image_to_base64(self, image_path: str) -> str:
        """
        Convert image file to base64 string.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        try:
            async with aiofiles.open(image_path, 'rb') as image_file:
                image_data = await image_file.read()
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                logger.debug(f"Converted image to base64: {len(image_b64)} characters")
                return image_b64
                
        except Exception as e:
            logger.error(f"Failed to convert image to base64: {e}")
            raise ValueError(f"Failed to read image file: {image_path}")