"""IOPaint service API routes."""
import time
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Response, WebSocket
from fastapi.responses import StreamingResponse
import io

from app.models.schemas import (
    InpaintRequest, 
    InpaintRegionsRequest, 
    HealthResponse, 
    ModelInfo, 
    ServiceInfo,
    ErrorResponse,
    ProcessingStats,
    InpaintResponse,
    AsyncInpaintRequest,
    AsyncInpaintResponse
)
from app.models.websocket_schemas import (
    TaskStatusEnum
)
from app.services.iopaint_core import iopaint_core
from app.websocket.task_manager import task_manager
from app.api.websocket_routes import websocket_endpoint
from app.config.settings import settings
from loguru import logger

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        health_status = await iopaint_core.health_check()
        
        return HealthResponse(
            status=health_status["status"],
            message=health_status["message"],
            timestamp=datetime.now().isoformat(),
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model", response_model=ModelInfo)
async def get_model_info():
    """Get current model information."""
    try:
        model_info = await iopaint_core.get_model_info()
        
        return ModelInfo(
            name=model_info["name"],
            device=model_info["device"],
            status=model_info["status"],
            parameters=model_info.get("parameters")
        )
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info", response_model=ServiceInfo)
async def get_service_info():
    """Get service information."""
    try:
        model_info = await iopaint_core.get_model_info()
        
        return ServiceInfo(
            name="IOPaint Text Removal Service",
            version="1.0.0",
            model=ModelInfo(
                name=model_info["name"],
                device=model_info["device"],
                status=model_info["status"],
                parameters=model_info.get("parameters")
            ),
            capabilities=[
                "text_inpainting",
                "mask_based_inpainting", 
                "region_based_inpainting",
                "multiple_models",
                "gpu_acceleration"
            ],
            limits={
                "max_image_size": settings.max_image_size,
                "max_file_size": settings.max_file_size,
                "request_timeout": settings.request_timeout,
                "supported_formats": ["JPEG", "PNG", "WebP"]
            }
        )
    except Exception as e:
        logger.error(f"Failed to get service info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inpaint")
async def inpaint_with_mask(request: InpaintRequest):
    """
    Perform inpainting with provided image and mask.
    Returns the processed image as binary data.
    """
    start_time = time.time()
    
    try:
        logger.info("Starting inpainting with mask")
        
        # Validate inputs
        if not request.image or not request.mask:
            raise HTTPException(status_code=400, detail="Image and mask are required")
        
        # Perform inpainting
        result_bytes = await iopaint_core.inpaint_image(
            image_b64=request.image,
            mask_b64=request.mask,
            sd_seed=request.sd_seed,
            sd_steps=request.sd_steps,
            sd_strength=request.sd_strength,
            sd_guidance_scale=request.sd_guidance_scale,
            sd_sampler=request.sd_sampler,
            hd_strategy=request.hd_strategy,
            hd_strategy_crop_trigger_size=request.hd_strategy_crop_trigger_size,
            hd_strategy_crop_margin=request.hd_strategy_crop_margin,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Inpainting completed in {processing_time:.2f}s")
        
        # Return image as binary stream
        return StreamingResponse(
            io.BytesIO(result_bytes),
            media_type="image/png",
            headers={
                "Content-Disposition": "inline; filename=inpainted.png",
                "X-Processing-Time": str(processing_time),
                "X-Timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Inpainting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inpaint-regions")
async def inpaint_with_regions(request: InpaintRegionsRequest):
    """
    Perform inpainting with text regions.
    Creates mask from regions and performs inpainting.
    Returns the processed image as binary data.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting inpainting with {len(request.regions)} regions")
        
        # Validate inputs
        if not request.image:
            raise HTTPException(status_code=400, detail="Image is required")
        
        if not request.regions:
            raise HTTPException(status_code=400, detail="At least one region is required")
        
        # Perform inpainting with regions
        result_bytes = await iopaint_core.inpaint_regions(
            image_b64=request.image,
            regions=request.regions,
            sd_seed=request.sd_seed,
            sd_steps=request.sd_steps,
            sd_strength=request.sd_strength,
            sd_guidance_scale=request.sd_guidance_scale,
            sd_sampler=request.sd_sampler,
            hd_strategy=request.hd_strategy,
            hd_strategy_crop_trigger_size=request.hd_strategy_crop_trigger_size,
            hd_strategy_crop_margin=request.hd_strategy_crop_margin,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt
        )
        
        processing_time = time.time() - start_time
        total_area = sum(r.width * r.height for r in request.regions)
        
        logger.info(
            f"Region inpainting completed in {processing_time:.2f}s, "
            f"processed {len(request.regions)} regions, total area: {total_area:.0f}px²"
        )
        
        # Return image as binary stream
        return StreamingResponse(
            io.BytesIO(result_bytes),
            media_type="image/png",
            headers={
                "Content-Disposition": "inline; filename=inpainted_regions.png",
                "X-Processing-Time": str(processing_time),
                "X-Regions-Count": str(len(request.regions)),
                "X-Total-Area": str(int(total_area)),
                "X-Timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Region inpainting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inpaint-regions-json", response_model=InpaintResponse) 
async def inpaint_with_regions_json(request: InpaintRegionsRequest):
    """
    Perform inpainting with text regions and return JSON response with stats.
    This endpoint returns metadata about the processing instead of the image binary.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting JSON inpainting with {len(request.regions)} regions")
        
        # Validate inputs
        if not request.image:
            raise HTTPException(status_code=400, detail="Image is required")
        
        if not request.regions:
            raise HTTPException(status_code=400, detail="At least one region is required")
        
        # Get image dimensions for stats
        import base64
        from PIL import Image
        image_data = base64.b64decode(request.image)
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size
        
        # Perform inpainting with regions
        result_bytes = await iopaint_core.inpaint_regions(
            image_b64=request.image,
            regions=request.regions,
            sd_seed=request.sd_seed,
            sd_steps=request.sd_steps,
            sd_strength=request.sd_strength,
            sd_guidance_scale=request.sd_guidance_scale,
            sd_sampler=request.sd_sampler,
            hd_strategy=request.hd_strategy,
            hd_strategy_crop_trigger_size=request.hd_strategy_crop_trigger_size,
            hd_strategy_crop_margin=request.hd_strategy_crop_margin,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt
        )
        
        processing_time = time.time() - start_time
        total_area = sum(r.width * r.height for r in request.regions)
        
        # Create processing stats
        processing_stats = ProcessingStats(
            regions_processed=len(request.regions),
            total_area=int(total_area),
            processing_time=processing_time,
            image_dimensions={"width": width, "height": height}
        )
        
        logger.info(
            f"JSON region inpainting completed in {processing_time:.2f}s, "
            f"processed {len(request.regions)} regions"
        )
        
        return InpaintResponse(
            success=True,
            message=f"Successfully processed {len(request.regions)} regions",
            processing_stats=processing_stats,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"JSON region inpainting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.on_event("startup")
async def startup_event():
    """Service startup event."""
    logger.info("IOPaint service starting up...")
    try:
        await iopaint_core.start_service()
        logger.info("IOPaint service startup complete")
    except Exception as e:
        logger.error(f"Failed to start IOPaint service: {e}")
        raise


@router.post("/inpaint-regions-async", response_model=AsyncInpaintResponse)
async def start_async_inpaint_regions(request: AsyncInpaintRequest):
    """
    Start async inpainting with text regions and return task ID for progress tracking.
    """
    try:
        logger.info(f"Starting async inpainting with {len(request.regions)} regions")
        
        # Validate inputs
        if not request.image:
            raise HTTPException(status_code=400, detail="Image is required")
        
        if not request.regions:
            raise HTTPException(status_code=400, detail="At least one region is required")
        
        # Start async processing with unified task_id
        task_id = await iopaint_core.inpaint_regions_async(
            image_b64=request.image,
            regions=request.regions,
            task_id=request.task_id,  # Pass unified task_id
            callback_url=request.callback_url,
            sd_seed=request.sd_seed,
            sd_steps=request.sd_steps,
            sd_strength=request.sd_strength,
            sd_guidance_scale=request.sd_guidance_scale,
            sd_sampler=request.sd_sampler,
            hd_strategy=request.hd_strategy,
            hd_strategy_crop_trigger_size=request.hd_strategy_crop_trigger_size,
            hd_strategy_crop_margin=request.hd_strategy_crop_margin,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt
        )
        
        # Build WebSocket URL
        websocket_url = f"ws://localhost:{settings.port}/api/v1/ws/progress/{task_id}" if request.enable_progress else None
        
        logger.info(f"Started async task {task_id} with WebSocket URL: {websocket_url}")
        
        return AsyncInpaintResponse(
            task_id=task_id,
            status=TaskStatusEnum.PENDING,
            message=f"Started processing {len(request.regions)} regions",
            websocket_url=websocket_url
        )
        
    except Exception as e:
        logger.error(f"Failed to start async inpainting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a processing task."""
    try:
        status = iopaint_core.get_task_status(task_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel-task/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a processing task."""
    try:
        success = await iopaint_core.cancel_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def get_task_stats():
    """Get task statistics."""
    try:
        stats = task_manager.get_task_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get task stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time progress updates
@router.websocket("/ws/progress/{task_id}")
async def websocket_progress_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for task-specific progress updates."""
    await websocket_endpoint(websocket, task_id)


@router.websocket("/ws/progress")
async def websocket_general_endpoint(websocket: WebSocket):
    """WebSocket endpoint for general progress updates."""
    await websocket_endpoint(websocket)


@router.on_event("startup")
async def startup_event():
    """Service startup event."""
    logger.info("IOPaint service starting up...")
    try:
        await iopaint_core.start_service()
        logger.info("IOPaint service startup complete")
    except Exception as e:
        logger.error(f"Failed to start IOPaint service: {e}")
        raise


@router.on_event("shutdown")
async def shutdown_event():
    """Service shutdown event."""
    logger.info("IOPaint service shutting down...")
    try:
        await iopaint_core.stop_service()
        logger.info("IOPaint service shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")