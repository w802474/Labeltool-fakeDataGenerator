"""IOPaint core service implementation."""
import base64
import io
import time
import uuid
import asyncio
import subprocess
from typing import List, Optional, Dict, Any, Callable, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
import aiohttp
from loguru import logger
import json

from app.config.settings import settings
from app.models.schemas import TextRegionSchema, ProcessingStats
from app.websocket.task_manager import task_manager, TaskStatus
from app.websocket.progress_tracker import ProgressTracker
from app.services.diagnostics import iopaint_diagnostics, ResourceMonitor
from app.services.resource_monitor import resource_monitor
from app.services.preprocessing_validator import preprocessing_validator, RiskLevel
from app.services.retry_manager import retry_manager
from app.services.image_scaler import image_scaler


class IOPaintCore:
    """Core IOPaint service for text inpainting and removal."""
    
    def __init__(self):
        """Initialize IOPaint core service."""
        self.model = settings.model
        self.device = settings.device
        self.iopaint_port = settings.port + 1  # Use port 8082 for internal IOPaint process
        self.base_url = f"http://localhost:{self.iopaint_port}"
        self.process = None
        self._service_ready = False
        
        logger.info(f"Initializing IOPaint core with model: {self.model}, device: {self.device}")
    
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
            logger.info(f"Starting IOPaint service with model: {self.model}")
            
            # Add additional parameters
            cmd.extend([
                f"--device={self.device}",
                f"--port={self.iopaint_port}",
                f"--host=127.0.0.1",  # Only bind to localhost for internal use
            ])
            
            if settings.no_gui:
                cmd.append("--no-inbrowser")
            if settings.low_mem:
                cmd.append("--low-mem")
            if settings.cpu_offload:
                cmd.append("--cpu-offload")
            
            logger.info(f"IOPaint command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                start_new_session=True
            )
            
            # Wait for service to be ready with progress monitoring
            await self._wait_for_service_ready(timeout=300)
            
            logger.info("IOPaint service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start IOPaint service: {e}")
            await self.stop_service()
            raise
    
    async def stop_service(self):
        """Stop IOPaint service."""
        if self.process:
            try:
                logger.info("Stopping IOPaint service")
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
                logger.info("IOPaint service stopped")
                
            except Exception as e:
                logger.error(f"Error stopping IOPaint service: {e}")
    
    async def _wait_for_process_end(self):
        """Wait for process to end."""
        while self.process and self.process.poll() is None:
            await asyncio.sleep(0.1)
    
    async def _wait_for_service_ready(self, timeout: int = 300):
        """Wait for IOPaint service to be ready."""
        start_time = time.time()
        last_log_time = start_time
        
        logger.info(f"Waiting for IOPaint service to be ready (timeout: {timeout}s)...")
        
        # Create task to monitor process output
        output_task = asyncio.create_task(self._monitor_process_output())
        
        try:
            while time.time() - start_time < timeout:
                # Check if process is still running
                if self.process and self.process.poll() is not None:
                    # Process has terminated
                    logger.error("IOPaint process terminated unexpectedly")
                    raise RuntimeError("IOPaint process terminated unexpectedly")
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{self.base_url}/api/v1/model", 
                            timeout=aiohttp.ClientTimeout(total=5)
                        ) as response:
                            if response.status == 200:
                                self._service_ready = True
                                output_task.cancel()
                                logger.info("IOPaint service is ready!")
                                return
                except Exception:
                    pass
                
                # Log progress every 30 seconds
                current_time = time.time()
                if current_time - last_log_time >= 30:
                    elapsed = int(current_time - start_time)
                    logger.info(f"Still waiting for IOPaint service... ({elapsed}s elapsed)")
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
                        logger.info(f"IOPaint: {line}")
                    elif 'server started' in line.lower() or 'running on' in line.lower():
                        logger.info(f"IOPaint: {line}")
                        
        except Exception as e:
            logger.warning(f"Error monitoring IOPaint output: {e}")
    
    def create_mask_from_regions(self, image_shape: tuple, regions) -> np.ndarray:
        """
        Create binary mask from text regions.
        
        Args:
            image_shape: (height, width, channels) of the original image
            regions: List of text regions to mask (can be TextRegionSchema objects or dicts)
            
        Returns:
            Binary mask as numpy array
        """
        height, width = image_shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        
        for region in regions:
            # Handle both dict and object formats
            if isinstance(region, dict):
                x = int(region['x'])
                y = int(region['y'])
                w = int(region['width'])
                h = int(region['height'])
            else:
                # Object with attributes
                x = int(region.x)
                y = int(region.y)
                w = int(region.width)
                h = int(region.height)
            
            # Ensure coordinates are within image bounds
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = max(1, min(w, width - x))
            h = max(1, min(h, height - y))
            
            # Fill the region with 255 (white) to indicate inpainting area
            mask[y:y+h, x:x+w] = 255
            
            logger.debug(f"Added mask region: ({x}, {y}, {w}, {h})")
        
        return mask
    
    async def inpaint_image_with_retry(
        self,
        image_b64: str,
        mask_b64: str,
        image_size: Optional[Tuple[int, int, int]] = None,
        region_count: Optional[int] = None,
        task_id: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """
        Perform inpainting with intelligent retry logic.
        
        Args:
            image_b64: Base64 encoded image
            mask_b64: Base64 encoded mask
            image_size: Optional tuple of (height, width, channels) for diagnostics
            region_count: Number of regions being processed for diagnostics
            task_id: Optional task ID for tracking
            **kwargs: Additional IOPaint parameters
            
        Returns:
            Processed image as bytes
        """
        # Define the core operation to retry
        async def core_operation(**params):
            return await self.inpaint_image(
                image_b64, mask_b64, image_size, region_count, **params
            )
        
        # Try without retry first
        try:
            return await core_operation(**kwargs)
        except Exception as e:
            # Analyze the error
            processing_duration = 0.0  # Will be calculated properly in diagnosis
            diagnosis = await iopaint_diagnostics.diagnose_disconnection(
                error=e,
                image_size=image_size,
                region_count=region_count,
                processing_duration=processing_duration
            )
            
            # Check if retry is recommended
            if not diagnosis.retry_recommended:
                logger.error(f"Retry not recommended for {diagnosis.reason.value}")
                raise e
            
            # Prepare context for retry manager
            context = {
                "image_size": image_size,
                "region_count": region_count,
                "task_id": task_id or "unknown"
            }
            
            # Execute with intelligent retry
            logger.info(f"Attempting intelligent retry for error: {diagnosis.reason.value}")
            success, result, attempts = await retry_manager.execute_with_retry(
                task_id=task_id or "unknown",
                operation=core_operation,
                diagnosis=diagnosis,
                original_params=kwargs,
                context=context
            )
            
            if success:
                logger.info(f"Retry successful after {len(attempts)} attempts")
                return result
            else:
                # Log all retry attempts
                logger.error(f"All retry attempts failed for {diagnosis.reason.value}")
                for i, attempt in enumerate(attempts, 1):
                    logger.error(f"Attempt {i}: {attempt.strategy.value} - {attempt.error}")
                
                # Raise the original error
                raise e

    async def inpaint_image(
        self,
        image_b64: str,
        mask_b64: str,
        image_size: Optional[Tuple[int, int, int]] = None,
        region_count: Optional[int] = None,
        **kwargs
    ) -> bytes:
        """
        Perform inpainting on image with mask using IOPaint API.
        
        Args:
            image_b64: Base64 encoded image
            mask_b64: Base64 encoded mask
            image_size: Optional tuple of (height, width, channels) for diagnostics
            region_count: Number of regions being processed for diagnostics
            **kwargs: Additional IOPaint parameters
            
        Returns:
            Processed image as bytes
        """
        if not self._service_ready:
            await self.start_service()
        
        start_time = time.time()
        
        try:
            # Prepare JSON payload
            payload = {
                "image": image_b64,
                "mask": mask_b64,
                "sd_seed": kwargs.get("sd_seed", -1),
                "sd_steps": kwargs.get("sd_steps", 25),
                "sd_strength": kwargs.get("sd_strength", 1.0),
                "sd_guidance_scale": kwargs.get("sd_guidance_scale", 7.5),
                "sd_sampler": kwargs.get("sd_sampler", "ddim"),
                "hd_strategy": kwargs.get("hd_strategy", "Original"),
                "hd_strategy_crop_trigger_size": kwargs.get("hd_strategy_crop_trigger_size", 1280),
                "hd_strategy_crop_margin": kwargs.get("hd_strategy_crop_margin", 32),
                "prompt": kwargs.get("prompt", ""),
                "negative_prompt": kwargs.get("negative_prompt", "")
            }
            
            # Log processing context for diagnostics
            if image_size:
                megapixels = (image_size[0] * image_size[1]) / 1000000
                logger.info(f"Starting IOPaint processing: {megapixels:.1f}MP image, {region_count or 0} regions")
            
            async with aiohttp.ClientSession() as session:
                # Send JSON request to IOPaint API
                async with session.post(
                    f"{self.base_url}/api/v1/inpaint",
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=settings.request_timeout)
                ) as response:
                    if response.status == 200:
                        # Return the result image bytes
                        image_bytes = await response.read()
                        processing_time = time.time() - start_time
                        logger.info(f"Successfully received inpainted image ({processing_time:.2f}s)")
                        return image_bytes
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
            processing_duration = time.time() - start_time
            
            # Perform detailed diagnostic analysis
            try:
                diagnosis = await iopaint_diagnostics.diagnose_disconnection(
                    error=e,
                    image_size=image_size,
                    region_count=region_count,
                    processing_duration=processing_duration
                )
                
                # Log detailed diagnostic information
                logger.error(f"IOPaint disconnection diagnosed: {diagnosis.reason.value}")
                logger.error(f"Category: {diagnosis.category.value}, Confidence: {diagnosis.confidence:.2f}")
                logger.error(f"Description: {diagnosis.description}")
                
                for suggestion in diagnosis.suggestions:
                    logger.warning(f"Suggestion: {suggestion}")
                
                # Include technical details in debug log
                logger.debug(f"Technical details: {diagnosis.technical_details}")
                
                # Create enhanced error message
                enhanced_error = f"{diagnosis.description} (Reason: {diagnosis.reason.value})"
                
                # Add retry recommendations to error
                if diagnosis.retry_recommended:
                    if diagnosis.retry_with_reduced_params:
                        enhanced_error += " | Retry recommended with reduced parameters"
                    else:
                        enhanced_error += " | Retry recommended"
                else:
                    enhanced_error += " | Manual intervention required"
                
                # Raise enhanced error
                raise Exception(enhanced_error)
                
            except Exception as diag_error:
                logger.error(f"Diagnostic analysis failed: {diag_error}")
                # Fall back to original error
                logger.error(f"Original IOPaint API call failed: {e}")
                raise e
    
    async def inpaint_regions(
        self,
        image_b64: str,
        regions: List[TextRegionSchema],
        **kwargs
    ) -> bytes:
        """
        Remove text regions from image using IOPaint with automatic scaling.
        
        Args:
            image_b64: Base64 encoded image
            regions: List of text regions to remove
            **kwargs: Additional IOPaint parameters
            
        Returns:
            Processed image as bytes (scaled back to original size if needed)
        """
        start_time = time.time()
        
        try:
            # Get scaling info first
            scaling_info = image_scaler.get_scaling_info(image_b64)
            logger.info(f"Original image: {scaling_info['original_size']}, "
                       f"Megapixels: {scaling_info['megapixels']:.1f}MP")
            
            # Scale image and regions if needed
            if scaling_info['scaling_needed']:
                logger.info(f"Large image detected, scaling down by factor {scaling_info['scale_factor']:.3f}")
                scaled_image_b64, scale_factor, original_size, new_size = image_scaler.scale_image_base64(image_b64)
                scaled_regions = image_scaler.scale_regions(regions, scale_factor, 
                                                          image_size=new_size, expand_regions=True)
                
                # Use scaled data for processing
                processing_image_b64 = scaled_image_b64
                processing_regions = scaled_regions
            else:
                logger.info("Image size is within limits, no scaling needed")
                processing_image_b64 = image_b64
                processing_regions = regions
                original_size = scaling_info['original_size']
                new_size = scaling_info['new_size']
            
            # Decode scaled/original image to get dimensions for mask creation
            image_data = base64.b64decode(processing_image_b64)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            image_np = np.array(image)
            
            logger.info(f"Processing image: {image_np.shape}")
            logger.info(f"Text regions to remove: {len(processing_regions)}")
            
            # Create mask from processed regions
            mask = self.create_mask_from_regions(image_np.shape, processing_regions)
            
            # Check if there are any regions to inpaint
            if np.sum(mask) == 0:
                logger.warning("No text regions to inpaint, returning original image")
                # If we scaled down, we need to return the original image
                if scaling_info['scaling_needed']:
                    return base64.b64decode(image_b64)
                return image_data
            
            # Convert mask to base64
            mask_pil = Image.fromarray(mask, mode='L')
            mask_buffer = io.BytesIO()
            mask_pil.save(mask_buffer, format='PNG')
            mask_b64 = base64.b64encode(mask_buffer.getvalue()).decode('utf-8')
            
            # Call IOPaint API with scaled image and mask
            logger.info("Starting text inpainting with IOPaint...")
            result_bytes = await self.inpaint_image(
                processing_image_b64, 
                mask_b64, 
                image_size=image_np.shape,
                region_count=len(processing_regions),
                **kwargs
            )
            
            # Scale result back to original size if we scaled down
            if scaling_info['scaling_needed']:
                logger.info("Scaling result image back to original size...")
                final_result_bytes = image_scaler.scale_result_back(
                    result_bytes, original_size, new_size
                )
            else:
                final_result_bytes = result_bytes
            
            processing_time = time.time() - start_time
            logger.info(f"Text removal completed in {processing_time:.2f}s")
            
            return final_result_bytes
            
        except Exception as e:
            logger.error(f"Error during text removal: {e}")
            raise
    
    async def get_model_info(self) -> dict:
        """Get information about the current model."""
        if not self._service_ready:
            return {
                "name": self.model,
                "device": self.device,
                "status": "not_started"
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v1/model") as response:
                    if response.status == 200:
                        model_info = await response.json()
                        return {
                            "name": model_info.get("name", self.model),
                            "device": self.device,
                            "status": "ready",
                            "parameters": model_info
                        }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
        
        return {
            "name": self.model,
            "device": self.device,
            "status": "error"
        }
    
    async def health_check(self) -> dict:
        """Perform health check."""
        try:
            if not self._service_ready:
                return {
                    "status": "unhealthy",
                    "message": "IOPaint service not ready"
                }
            
            # Check if IOPaint API is responding
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v1/model",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": "IOPaint service is running"
                        }
                    else:
                        return {
                            "status": "unhealthy", 
                            "message": f"IOPaint API returned status {response.status}"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}"
            }
    
    async def inpaint_regions_async(
        self,
        image_b64: str,
        regions: List[TextRegionSchema],
        task_id: Optional[str] = None,
        callback_url: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Remove text regions from image using IOPaint with progress tracking.
        
        Args:
            image_b64: Base64 encoded image
            regions: List of text regions to remove
            task_id: Optional task ID for progress tracking
            **kwargs: Additional IOPaint parameters
            
        Returns:
            Task ID for tracking progress
        """
        # Use provided task_id or create new one
        if not task_id:
            task_id = task_manager.create_task(
                total_regions=len(regions),
                metadata={
                    "image_size": len(image_b64),
                    "region_count": len(regions)
                }
            )
        else:
            # Register existing task_id with task manager
            task_manager.register_task(
                task_id=task_id,
                total_regions=len(regions),
                metadata={
                    "image_size": len(image_b64),
                    "region_count": len(regions)
                }
            )
        
        # Start processing task
        asyncio.create_task(self._process_with_progress(task_id, image_b64, regions, callback_url, **kwargs))
        
        return task_id
    
    async def _process_with_progress(
        self,
        task_id: str,
        image_b64: str,
        regions: List[TextRegionSchema],
        callback_url: Optional[str] = None,
        **kwargs
    ):
        """
        Process image with detailed progress tracking.
        
        Args:
            task_id: Task ID for progress tracking
            image_b64: Base64 encoded image
            regions: List of text regions to remove
            callback_url: URL to callback when processing completes
            **kwargs: Additional IOPaint parameters
        """
        tracker = ProgressTracker(task_id, len(regions))
        
        # Start resource monitoring
        monitoring_metrics = resource_monitor.start_monitoring(task_id)
        
        try:
            # Start task
            await task_manager.start_task(task_id)
            
            # Perform preprocessing validation
            logger.info(f"Task {task_id}: Running preprocessing validation...")
            logger.debug(f"Task {task_id}: Regions type: {type(regions)}, First region type: {type(regions[0]) if regions else 'None'}")
            
            # Convert regions to dict format for validation
            regions_dict = []
            for region in regions:
                # Handle both dict and object formats
                if isinstance(region, dict):
                    # Already in dict format, use directly
                    if "bounding_box" in region:
                        regions_dict.append(region)
                    else:
                        # Convert flat dict format to nested format
                        regions_dict.append({
                            "bounding_box": {
                                "x": region.get("x", 0),
                                "y": region.get("y", 0),
                                "width": region.get("width", 0),
                                "height": region.get("height", 0)
                            }
                        })
                else:
                    # Object format, extract attributes
                    regions_dict.append({
                        "bounding_box": {
                            "x": getattr(region, 'x', 0),
                            "y": getattr(region, 'y', 0),
                            "width": getattr(region, 'width', 0),
                            "height": getattr(region, 'height', 0)
                        }
                    })
            
            validation_report = await preprocessing_validator.validate_processing_request(
                image_b64, regions_dict, kwargs
            )
            
            # Log validation results
            logger.info(f"Task {task_id}: Validation complete - Risk: {validation_report.overall_risk.value}, "
                       f"Score: {validation_report.total_score:.1f}")
            
            if validation_report.warnings:
                for warning in validation_report.warnings:
                    logger.warning(f"Task {task_id}: Validation warning - {warning}")
            
            if validation_report.processing_recommendations:
                for rec in validation_report.processing_recommendations:
                    logger.info(f"Task {task_id}: Recommendation - {rec}")
            
            # Apply parameter adjustments if suggested
            if validation_report.parameter_adjustments:
                logger.info(f"Task {task_id}: Applying parameter adjustments: {validation_report.parameter_adjustments}")
                kwargs.update(validation_report.parameter_adjustments)
            
            # Check if processing should proceed
            if not validation_report.should_proceed:
                error_msg = f"Preprocessing validation failed - Risk: {validation_report.overall_risk.value}, Score: {validation_report.total_score:.1f}"
                logger.error(f"Task {task_id}: {error_msg}")
                raise ValueError(error_msg)
            
            # Stage 1: Prepare image (0-5%)
            resource_monitor.mark_processing_phase("image_preparation")
            await tracker.prepare_image(0)
            
            # Get scaling info and scale if needed
            scaling_info = image_scaler.get_scaling_info(image_b64)
            logger.info(f"Task {task_id}: Original image: {scaling_info['original_size']}, "
                       f"Megapixels: {scaling_info['megapixels']:.1f}MP")
            
            if scaling_info['scaling_needed']:
                logger.info(f"Task {task_id}: Large image detected, scaling down by factor {scaling_info['scale_factor']:.3f}")
                scaled_image_b64, scale_factor, original_size, new_size = image_scaler.scale_image_base64(image_b64)
                scaled_regions = image_scaler.scale_regions(regions, scale_factor, 
                                                          image_size=new_size, expand_regions=True)
                
                # Use scaled data for processing
                processing_image_b64 = scaled_image_b64
                processing_regions = scaled_regions
                logger.info(f"Task {task_id}: Scaled to {new_size}, {len(processing_regions)} regions adjusted")
            else:
                logger.info(f"Task {task_id}: Image size is within limits, no scaling needed")
                processing_image_b64 = image_b64
                processing_regions = regions
                original_size = scaling_info['original_size']
                new_size = scaling_info['new_size']
            
            # Decode processed image to get dimensions
            image_data = base64.b64decode(processing_image_b64)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            image_np = np.array(image)
            
            await tracker.prepare_image(50)
            logger.info(f"Task {task_id}: Processing image {image_np.shape}")
            
            await tracker.prepare_regions(80)
            logger.info(f"Task {task_id}: Processing {len(processing_regions)} text regions")
            
            await tracker.prepare_image(100)
            resource_monitor.end_processing_phase("image_preparation")
            
            # Stage 2: Generate mask (5-15%)
            resource_monitor.mark_processing_phase("mask_generation")
            await tracker.start_masking()
            
            # Create mask from processed regions (scaled if needed)
            mask = self.create_mask_from_regions(image_np.shape, processing_regions)
            
            await tracker.update_masking_progress(50)
            
            # Check if there are any regions to inpaint
            if np.sum(mask) == 0:
                logger.warning(f"Task {task_id}: No text regions to inpaint, returning original image")
                # Save original image as result (use original size image if scaled)
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    if scaling_info['scaling_needed']:
                        # Return original unscaled image
                        original_image_data = base64.b64decode(image_b64)
                        tmp_file.write(original_image_data)
                    else:
                        tmp_file.write(image_data)
                    result_path = tmp_file.name
                
                await tracker.complete(result_path)
                return
            
            # Convert mask to base64
            mask_pil = Image.fromarray(mask, mode='L')
            mask_buffer = io.BytesIO()
            mask_pil.save(mask_buffer, format='PNG')
            mask_b64 = base64.b64encode(mask_buffer.getvalue()).decode('utf-8')
            
            await tracker.update_masking_progress(100)
            resource_monitor.end_processing_phase("mask_generation")
            
            # Stage 3: AI Inpainting (15-90%)
            resource_monitor.mark_processing_phase("ai_inpainting")
            await tracker.start_inpainting()
            
            # Start real IOPaint processing immediately
            logger.info(f"Task {task_id}: Starting text inpainting with IOPaint...")
            real_processing_task = asyncio.create_task(
                self.inpaint_image_with_retry(
                    processing_image_b64, 
                    mask_b64, 
                    image_size=image_np.shape,
                    region_count=len(processing_regions),
                    task_id=task_id,
                    **kwargs
                )
            )
            
            # Simulate progress while real processing happens
            async def progress_simulation():
                for i, region in enumerate(processing_regions, 1):
                    await tracker.update_inpainting_progress(i, 0)
                    await asyncio.sleep(0.03)  # Simulate processing time per region
                    await tracker.update_inpainting_progress(i, 50)
                    await asyncio.sleep(0.03)
                    await tracker.update_inpainting_progress(i, 100)
            
            # Run progress simulation to 90%
            progress_task = asyncio.create_task(progress_simulation())
            await progress_task
            
            # At 90%, synchronize with real processing
            if real_processing_task.done():
                # Processing finished quickly, add natural delay
                logger.info(f"Task {task_id}: IOPaint processing completed quickly, adding natural delay...")
                await asyncio.sleep(0.5)  # Natural feeling delay
                try:
                    result_bytes = real_processing_task.result()
                except Exception as e:
                    # Re-raise the exception from the real processing task
                    raise e
            else:
                # Processing is still running, wait for completion
                logger.info(f"Task {task_id}: Waiting for IOPaint processing to complete...")
                result_bytes = await real_processing_task
            resource_monitor.end_processing_phase("ai_inpainting")
            
            # Stage 4: Finalization (90-100%)
            resource_monitor.mark_processing_phase("finalization")
            await tracker.start_finalizing()
            
            await tracker.update_finalizing_progress(30, "Saving processed image...")
            
            # Scale result back to original size if we scaled down
            if scaling_info['scaling_needed']:
                logger.info(f"Task {task_id}: Scaling result image back to original size...")
                await tracker.update_finalizing_progress(50, "Upscaling result to original size...")
                
                final_result_bytes = image_scaler.scale_result_back(
                    result_bytes, original_size, new_size
                )
            else:
                final_result_bytes = result_bytes
            
            # Save result to temporary file
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(final_result_bytes)
                result_path = tmp_file.name
            
            await tracker.update_finalizing_progress(80, "Finalizing result...")
            
            # Complete task
            resource_monitor.end_processing_phase("finalization")
            await tracker.complete(result_path)
            
            # Send HTTP callback if URL provided
            if callback_url:
                await self._send_completion_callback(callback_url, task_id, final_result_bytes)
            
            # Stop resource monitoring and log final metrics
            final_metrics = await resource_monitor.stop_monitoring()
            
            # Log comprehensive processing summary
            logger.info(f"Task {task_id}: Processing completed successfully")
            logger.info(f"Task {task_id}: Peak memory usage: {final_metrics.peak_memory_mb:.0f}MB")
            logger.info(f"Task {task_id}: Average CPU usage: {final_metrics.avg_cpu_percent:.1f}%")
            logger.info(f"Task {task_id}: Memory efficiency score: {final_metrics.memory_efficiency_score:.1f}")
            
            # Log any resource warnings
            if final_metrics.warnings:
                for warning in final_metrics.warnings:
                    logger.warning(f"Task {task_id}: Resource warning - {warning}")
            
            # Log processing recommendations
            recommendations = resource_monitor.get_processing_recommendations()
            if recommendations:
                logger.info(f"Task {task_id}: Processing recommendations:")
                for rec in recommendations:
                    logger.info(f"  - {rec}")
            
        except Exception as e:
            # Stop resource monitoring and include metrics in error analysis
            final_metrics = await resource_monitor.stop_monitoring()
            
            # Log resource state at time of failure
            logger.error(f"Task {task_id}: Processing failed - {e}")
            logger.error(f"Task {task_id}: Resource state at failure:")
            logger.error(f"  - Memory usage: {final_metrics.peak_memory_mb:.0f}MB peak")
            logger.error(f"  - CPU usage: {final_metrics.avg_cpu_percent:.1f}% average")
            logger.error(f"  - Processing duration: {final_metrics.duration_seconds:.2f}s")
            
            if final_metrics.warnings:
                logger.error(f"  - Warnings: {', '.join(final_metrics.warnings)}")
            
            await tracker.fail(str(e))
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a processing task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status dictionary or None if not found
        """
        task = task_manager.get_task(task_id)
        if not task:
            return None
        
        return {
            "task_id": task_id,
            "status": task.status.value,
            "stage": task.stage.value,
            "overall_progress": task.overall_progress,
            "stage_progress": task.stage_progress,
            "current_region": task.current_region,
            "total_regions": task.total_regions,
            "message": task.message,
            "elapsed_time": task.elapsed_time,
            "estimated_remaining": task.estimated_remaining,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a processing task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if task was cancelled, False if not found
        """
        task = task_manager.get_task(task_id)
        if not task:
            return False
        
        await task_manager.cancel_task(task_id)
        return True
    
    async def _send_completion_callback(
        self,
        callback_url: str,
        task_id: str,
        result_bytes: bytes
    ):
        """
        Send HTTP callback when processing completes.
        
        Args:
            callback_url: URL to send callback to
            task_id: Task ID
            result_bytes: Processed image bytes
        """
        try:
            # Convert result to base64
            result_b64 = base64.b64encode(result_bytes).decode('utf-8')
            
            # Prepare callback data
            callback_data = {
                "task_id": task_id,
                "status": "completed",
                "image_data": result_b64,
                "timestamp": time.time()
            }
            
            logger.info(f"Sending completion callback for task {task_id} to {callback_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    callback_url,
                    json=callback_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Callback sent successfully for task {task_id}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Callback failed for task {task_id}: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to send callback for task {task_id}: {e}")


# Global IOPaint core instance
iopaint_core = IOPaintCore()