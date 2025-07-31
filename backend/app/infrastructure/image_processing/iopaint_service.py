"""IOPaint service for advanced text inpainting and removal."""
import os
import uuid
import asyncio
import subprocess
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


class IOPaintService(InpaintingServicePort):
    """Service for text inpainting using IOPaint with LaMa model."""
    
    def __init__(self, port: int = None, model: str = None, device: str = None):
        """Initialize IOPaint service."""
        self.port = port or settings.iopaint_port
        self.model = model or settings.iopaint_model
        self.device = device or settings.iopaint_device
        self.base_url = f"http://localhost:{self.port}"
        self.process = None
        self._service_ready = False
        
        
        logger.info(f"🎨 Initializing IOPaint service on port {self.port}")
    
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_service()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_service()
    
    async def start_service(self):
        """Start IOPaint service as background process."""
        if self._service_ready:
            logger.info("IOPaint service already running")
            return
        
        try:
            # Build startup command
            cmd = ["iopaint", "start", f"--model={self.model}"]
            logger.info(f"🚀 Starting IOPaint service with model: {self.model}")
            
            # Add additional parameters
            cmd.extend([
                f"--device={self.device}",
                f"--port={self.port}",
                "--host=127.0.0.1",
                "--no-inbrowser",  # Don't open browser
                "--low-mem",  # Use low memory mode
                "--cpu-offload"  # Offload to CPU to save memory
            ])
            
            logger.info(f"🔧 IOPaint command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr to stdout
                universal_newlines=True,   # Text mode
                bufsize=1,                 # Line buffered
                start_new_session=True
            )
            
            # Wait for service to be ready with progress monitoring
            await self._wait_for_service_ready_with_progress()
            
            logger.info("✅ IOPaint service started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start IOPaint service: {e}")
            await self.stop_service()
            raise
    
    async def stop_service(self):
        """Stop IOPaint service."""
        if self.process:
            try:
                logger.info("🛑 Stopping IOPaint service")
                self.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(
                        asyncio.create_task(self._wait_for_process_end()),
                        timeout=10.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Process didn't terminate gracefully, force killing")
                    self.process.kill()
                
                self.process = None
                self._service_ready = False
                logger.info("✅ IOPaint service stopped")
                
            except Exception as e:
                logger.error(f"❌ Error stopping IOPaint service: {e}")
    
    async def _wait_for_process_end(self):
        """Wait for process to end."""
        while self.process and self.process.poll() is None:
            await asyncio.sleep(0.1)
    
    async def _wait_for_service_ready(self, timeout: int = 180):
        """Wait for IOPaint service to be ready."""
        start_time = time.time()
        last_log_time = start_time
        
        logger.info(f"⏳ Waiting for IOPaint service to be ready (timeout: {timeout}s)...")
        
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/api/v1/model") as response:
                        if response.status == 200:
                            self._service_ready = True
                            logger.info("🎯 IOPaint service is ready")
                            return
            except Exception:
                pass
            
            # Log progress every 15 seconds
            current_time = time.time()
            if current_time - last_log_time >= 15:
                elapsed = int(current_time - start_time)
                logger.info(f"⏳ Still waiting for IOPaint service... ({elapsed}s elapsed)")
                last_log_time = current_time
            
            await asyncio.sleep(2)
        
        raise TimeoutError(f"IOPaint service failed to start within {timeout} seconds")
    
    async def _wait_for_service_ready_with_progress(self, timeout: int = 300):
        """Wait for IOPaint service to be ready with progress monitoring."""
        start_time = time.time()
        last_log_time = start_time
        
        logger.info(f"🚀 Starting IOPaint service with progress monitoring (timeout: {timeout}s)...")
        
        # Create task to monitor process output
        output_task = asyncio.create_task(self._monitor_process_output())
        
        try:
            while time.time() - start_time < timeout:
                # Check if process is still running
                if self.process and self.process.poll() is not None:
                    # Process has terminated
                    stdout, stderr = self.process.communicate()
                    logger.error(f"❌ IOPaint process terminated unexpectedly")
                    if stdout:
                        logger.error(f"stdout: {stdout}")
                    if stderr:
                        logger.error(f"stderr: {stderr}")
                    raise RuntimeError("IOPaint process terminated unexpectedly")
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{self.base_url}/api/v1/model", timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                self._service_ready = True
                                output_task.cancel()
                                logger.info("🎯 IOPaint service is ready!")
                                return
                except Exception:
                    pass
                
                # Log progress every 30 seconds
                current_time = time.time()
                if current_time - last_log_time >= 30:
                    elapsed = int(current_time - start_time)
                    logger.info(f"⏳ Still waiting for IOPaint service... ({elapsed}s elapsed)")
                    last_log_time = current_time
                
                await asyncio.sleep(3)
            
            output_task.cancel()
            raise TimeoutError(f"IOPaint service failed to start within {timeout} seconds")
            
        except asyncio.CancelledError:
            output_task.cancel()
            raise
    
    async def _monitor_process_output(self):
        """Monitor IOPaint process output and log progress."""
        if not self.process or not self.process.stdout:
            return
            
        try:
            while True:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, self.process.stdout.readline
                )
                if not line:
                    break
                    
                line = line.strip()
                if line:
                    # Filter and log important messages
                    if any(keyword in line.lower() for keyword in [
                        'downloading', 'loading', 'model', 'progress', 'error', 'fail'
                    ]):
                        logger.info(f"📥 IOPaint: {line}")
                    elif 'server started' in line.lower() or 'running on' in line.lower():
                        logger.info(f"🚀 IOPaint: {line}")
                        
        except Exception as e:
            logger.warning(f"Error monitoring IOPaint output: {e}")
    
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
        Remove text regions from image using IOPaint.
        
        Args:
            image_path: Path to the input image
            text_regions: List of text regions to remove
            output_dir: Directory to save the processed image
            
        Returns:
            Path to the processed image
        """
        if not self._service_ready:
            await self.start_service()
        
        try:
            # Load the image
            image = Image.open(image_path).convert("RGB")
            image_np = np.array(image)
            
            logger.info(f"🖼️ Processing image: {image_path}")
            logger.info(f"📐 Image shape: {image_np.shape}")
            logger.info(f"🎯 Text regions to remove: {len(text_regions)}")
            
            # Create mask from text regions
            mask = self.create_mask_from_regions(image_np.shape, text_regions)
            
            # Check if there are any regions to inpaint
            if np.sum(mask) == 0:
                logger.warning("⚠️ No text regions to inpaint, returning original image")
                return image_path
            
            # Save mask temporarily
            mask_pil = Image.fromarray(mask, mode='L')
            temp_mask_path = f"/tmp/mask_{uuid.uuid4().hex[:8]}.png"
            mask_pil.save(temp_mask_path)
            
            # Generate output filename
            input_filename = Path(image_path).stem
            output_filename = f"{input_filename}_iopaint_{uuid.uuid4().hex[:8]}.png"
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)
            
            # Call IOPaint API
            logger.info("🎨 Starting text inpainting with IOPaint...")
            
            await self._call_inpaint_api(image_path, temp_mask_path, output_path)
            
            # Clean up temporary mask file
            try:
                os.remove(temp_mask_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp mask file: {e}")
            
            logger.info(f"✅ Text removal completed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error during text removal: {e}")
            raise
    
    async def _call_inpaint_api(self, image_path: str, mask_path: str, output_path: str):
        """Call IOPaint API for inpainting."""
        import base64
        
        try:
            # Read and encode image and mask as base64
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()
                image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            async with aiofiles.open(mask_path, 'rb') as f:
                mask_data = await f.read()
                mask_b64 = base64.b64encode(mask_data).decode('utf-8')
            
            # Prepare JSON payload
            payload = {
                "image": image_b64,
                "mask": mask_b64,
                "sd_seed": -1,  # Random seed
                "sd_steps": 25,
                "sd_strength": 1.0,
                "sd_guidance_scale": 7.5,
                "sd_sampler": "ddim",
                "hd_strategy": "Original",
                "hd_strategy_crop_trigger_size": 1280,
                "hd_strategy_crop_margin": 32,
                "prompt": "",  # Empty prompt for simple inpainting
                "negative_prompt": ""
            }
            
            async with aiohttp.ClientSession() as session:
                # Send JSON request to IOPaint API
                async with session.post(
                    f"{self.base_url}/api/v1/inpaint",
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        # Save the result image
                        async with aiofiles.open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        logger.info("✅ Successfully received and saved inpainted image")
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
                        raise Exception(f"IOPaint API error: {response.status} - {error_text}")
        
        except Exception as e:
            logger.error(f"❌ IOPaint API call failed: {e}")
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
        """Get information about the current model."""
        if not self._service_ready:
            return {
                "model_name": self.model,
                "device": self.device,
                "status": "not_started",
                "port": self.port
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v1/model") as response:
                    if response.status == 200:
                        model_info = await response.json()
                        return {
                            "model_name": model_info.get("name", self.model),
                            "device": self.device,
                            "status": "ready",
                            "port": self.port,
                            "model_info": model_info
                        }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
        
        return {
            "model_name": self.model,
            "device": self.device,
            "status": "error",
            "port": self.port
        }