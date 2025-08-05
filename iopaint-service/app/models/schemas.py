"""IOPaint service data models and schemas."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TextRegionSchema(BaseModel):
    """Text region schema for inpainting requests."""
    x: float = Field(..., description="X coordinate of the region")
    y: float = Field(..., description="Y coordinate of the region") 
    width: float = Field(..., description="Width of the region")
    height: float = Field(..., description="Height of the region")


class InpaintRequest(BaseModel):
    """Request model for text inpainting."""
    image: str = Field(..., description="Base64 encoded image data")
    mask: str = Field(..., description="Base64 encoded mask data")
    
    # IOPaint parameters
    sd_seed: int = Field(default=-1, description="Random seed (-1 for random)")
    sd_steps: int = Field(default=25, description="Number of diffusion steps")
    sd_strength: float = Field(default=1.0, description="Denoising strength")
    sd_guidance_scale: float = Field(default=7.5, description="Guidance scale")
    sd_sampler: str = Field(default="ddim", description="Sampling method")
    hd_strategy: str = Field(default="Original", description="HD strategy")
    hd_strategy_crop_trigger_size: int = Field(default=1280, description="HD crop trigger size")
    hd_strategy_crop_margin: int = Field(default=32, description="HD crop margin")
    prompt: str = Field(default="", description="Text prompt for generation")
    negative_prompt: str = Field(default="", description="Negative text prompt")


class InpaintRegionsRequest(BaseModel):
    """Request model for inpainting with text regions."""
    image: str = Field(..., description="Base64 encoded image data")
    regions: List[TextRegionSchema] = Field(..., description="Text regions to remove")
    
    # IOPaint parameters
    sd_seed: int = Field(default=-1, description="Random seed (-1 for random)")
    sd_steps: int = Field(default=25, description="Number of diffusion steps")
    sd_strength: float = Field(default=1.0, description="Denoising strength")
    sd_guidance_scale: float = Field(default=7.5, description="Guidance scale")
    sd_sampler: str = Field(default="ddim", description="Sampling method")
    hd_strategy: str = Field(default="Original", description="HD strategy")
    hd_strategy_crop_trigger_size: int = Field(default=1280, description="HD crop trigger size")
    hd_strategy_crop_margin: int = Field(default=32, description="HD crop margin")
    prompt: str = Field(default="", description="Text prompt for generation")
    negative_prompt: str = Field(default="", description="Negative text prompt")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    timestamp: str = Field(..., description="Response timestamp")
    version: str = Field(..., description="Service version")


class ModelInfo(BaseModel):
    """Model information response."""
    name: str = Field(..., description="Model name")
    device: str = Field(..., description="Device being used")
    status: str = Field(..., description="Model status")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Model parameters")


class ServiceInfo(BaseModel):
    """Service information response."""
    name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    model: ModelInfo = Field(..., description="Current model info")
    capabilities: List[str] = Field(..., description="Service capabilities")
    limits: Dict[str, Any] = Field(..., description="Service limits")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="Error timestamp")


class ProcessingStats(BaseModel):
    """Processing statistics model."""
    regions_processed: int = Field(..., description="Number of regions processed")
    total_area: int = Field(..., description="Total area processed")
    processing_time: float = Field(..., description="Processing time in seconds")
    image_dimensions: Dict[str, int] = Field(..., description="Image dimensions")


class AsyncInpaintRequest(BaseModel):
    """Request to start async inpainting task."""
    image: str = Field(description="Base64 encoded image")
    regions: List[dict] = Field(description="List of text regions to inpaint (x, y, width, height)")
    # IOPaint parameters
    sd_seed: int = -1
    sd_steps: int = 25
    sd_strength: float = 1.0
    sd_guidance_scale: float = 7.5
    sd_sampler: str = "ddim"
    hd_strategy: str = "Original"
    hd_strategy_crop_trigger_size: int = 1280
    hd_strategy_crop_margin: int = 32
    prompt: str = ""
    negative_prompt: str = ""
    
    # Progress tracking options
    enable_progress: bool = True
    progress_interval: float = 1.0  # Progress update interval in seconds
    
    # Callback options
    callback_url: Optional[str] = Field(default=None, description="URL to callback when processing completes")
    
    # Unified task ID
    task_id: Optional[str] = Field(default=None, description="Unified task ID from frontend/backend")


class AsyncInpaintResponse(BaseModel):
    """Response from async inpainting request."""
    task_id: str
    status: str
    message: str
    estimated_time: Optional[float] = None
    websocket_url: Optional[str] = None


class InpaintResponse(BaseModel):
    """Inpainting response model (for JSON responses)."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    processing_stats: Optional[ProcessingStats] = Field(None, description="Processing statistics")
    timestamp: str = Field(..., description="Response timestamp")