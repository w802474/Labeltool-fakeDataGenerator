"""Pydantic models for API request/response validation."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import UploadFile

from app.application.dto.session_dto import (
    LabelSessionDTO,
    TextRegionDTO,
    ProcessingProgressResponse,
    ErrorResponse,
    ValidationErrorResponse,
    UpdateTextRegionsRequest,
    RestoreSessionRequest
)


# Request Models
class UploadImageRequest(BaseModel):
    """Request model for image upload (file handled separately)."""
    pass


class UpdateRegionRequest(BaseModel):
    """Request to update a single text region."""
    region: TextRegionDTO = Field(..., description="Updated text region data")


class DeleteRegionRequest(BaseModel):
    """Request to delete a text region."""
    region_id: str = Field(..., description="ID of region to delete")


# Response Models
class SessionCreatedResponse(BaseModel):
    """Response for successful session creation."""
    session_id: str = Field(..., description="Unique session identifier")
    status: str = Field(..., description="Current session status")
    message: str = Field(..., description="Success message")


class SessionDetailResponse(BaseModel):
    """Response containing full session details."""
    session: LabelSessionDTO = Field(..., description="Complete session data")


class TextRegionsResponse(BaseModel):
    """Response containing text regions data."""
    session_id: str = Field(..., description="Session identifier")
    regions: List[TextRegionDTO] = Field(..., description="List of text regions")
    total_count: int = Field(..., description="Total number of regions")


class ProcessingStatusResponse(BaseModel):
    """Response for processing status queries."""
    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="Current processing status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress percentage")
    message: str = Field(..., description="Current processing message")
    estimated_time_remaining: Optional[int] = Field(
        None, description="Estimated seconds remaining"
    )
    started_at: Optional[datetime] = Field(None, description="Processing start time")


class ProcessingResultResponse(BaseModel):
    """Response for completed processing results."""
    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="Processing status")
    processed_image_url: Optional[str] = Field(
        None, description="URL to download processed image"
    )
    processing_summary: dict = Field(..., description="Summary of processing results")




class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    services: dict = Field(..., description="Status of dependent services")


class ServiceInfoResponse(BaseModel):
    """Service information response."""
    ocr_device: str = Field(..., description="OCR processing device")
    supported_formats: List[str] = Field(..., description="Supported image formats")
    max_file_size: int = Field(..., description="Maximum file size in bytes")
    storage_info: dict = Field(..., description="Storage directory information")


# Error Models
class FileUploadError(ErrorResponse):
    """File upload error response."""
    error: str = Field(default="file_upload_error")
    supported_formats: List[str] = Field(..., description="List of supported formats")
    max_size_mb: int = Field(..., description="Maximum file size in MB")


class SessionNotFoundError(ErrorResponse):
    """Session not found error response."""
    error: str = Field(default="session_not_found")
    session_id: str = Field(..., description="Requested session ID")


class ProcessingError(ErrorResponse):
    """Processing error response."""
    error: str = Field(default="processing_error")
    session_id: str = Field(..., description="Session ID that failed")
    stage: str = Field(..., description="Processing stage where error occurred")


class OCRError(ErrorResponse):
    """OCR processing error response."""
    error: str = Field(default="ocr_error")
    device_info: Optional[dict] = Field(None, description="OCR device information")


# Validation Models
class RegionValidationResponse(BaseModel):
    """Response for region validation."""
    valid: bool = Field(..., description="Whether regions are valid")
    issues: List[str] = Field(default_factory=list, description="Validation issues")
    warnings: List[str] = Field(default_factory=list, description="Warnings")
    region_count: int = Field(..., description="Number of regions validated")


class SessionValidationResponse(BaseModel):
    """Response for session validation."""
    ready_for_processing: bool = Field(..., description="Whether session can be processed")
    status: str = Field(..., description="Current session status")
    issues: List[str] = Field(default_factory=list, description="Issues preventing processing")
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations for improvement"
    )


# Async Processing Models
class ProcessTextRemovalAsyncRequest(BaseModel):
    """Request model for async text removal processing."""
    task_id: Optional[str] = Field(
        None, description="Unified task ID from frontend (if not provided, backend will generate one)"
    )
    regions: Optional[List[TextRegionDTO]] = Field(
        None, description="Updated regions to process (optional, uses session regions if not provided)"
    )
    inpainting_method: str = Field(
        default="iopaint", description="IOPaint inpainting method to use"
    )
    custom_radius: Optional[int] = Field(
        None, ge=1, le=50, description="Custom inpainting radius (1-50 pixels)"
    )
    websocket_url: Optional[str] = Field(
        None, description="WebSocket URL for progress updates (auto-generated if not provided)"
    )


class ProcessTextRemovalAsyncResponse(BaseModel):
    """Response for async text removal processing."""
    task_id: str = Field(..., description="Unique task identifier for tracking progress")
    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="Initial task status")
    message: str = Field(..., description="Processing status message")
    websocket_url: str = Field(..., description="WebSocket URL for real-time progress updates")
    estimated_duration: Optional[int] = Field(
        None, description="Estimated processing duration in seconds"
    )


class TaskStatusResponse(BaseModel):
    """Response for task status queries."""
    task_id: str = Field(..., description="Task identifier")
    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="Current task status")
    stage: str = Field(..., description="Current processing stage")
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage (0-100)")
    message: str = Field(..., description="Current status message")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    error_message: Optional[str] = Field(None, description="Error message if task failed")
    result: Optional[dict] = Field(None, description="Task result if completed")


class TaskCancelResponse(BaseModel):
    """Response for task cancellation."""
    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Cancellation status")
    message: str = Field(..., description="Cancellation message")


# Statistics and Metrics Models
class ProcessingStatsResponse(BaseModel):
    """Response with processing statistics."""
    total_sessions: int = Field(..., description="Total number of sessions")
    completed_sessions: int = Field(..., description="Number of completed sessions")
    failed_sessions: int = Field(..., description="Number of failed sessions")
    average_regions_per_session: float = Field(
        ..., description="Average number of regions per session"
    )
    average_processing_time: float = Field(
        ..., description="Average processing time in seconds"
    )


class SessionSummaryResponse(BaseModel):
    """Response with session summary information."""
    session_id: str = Field(..., description="Session identifier")
    created_at: datetime = Field(..., description="Session creation time")
    status: str = Field(..., description="Current status")
    region_count: int = Field(..., description="Number of text regions")
    user_modified_count: int = Field(..., description="Number of user-modified regions")
    image_info: dict = Field(..., description="Original image information")
    processing_info: Optional[dict] = Field(None, description="Processing information")


# Batch Operation Models
class BatchProcessRequest(BaseModel):
    """Request for batch processing multiple sessions."""
    session_ids: List[str] = Field(..., min_length=1, description="List of session IDs")
    inpainting_method: str = Field(default="telea", description="Inpainting method to use")


class BatchProcessResponse(BaseModel):
    """Response for batch processing request."""
    batch_id: str = Field(..., description="Unique batch identifier")
    session_count: int = Field(..., description="Number of sessions in batch")
    estimated_time: int = Field(..., description="Estimated total processing time")
    status: str = Field(..., description="Batch processing status")


# Download Models
class DownloadRequest(BaseModel):
    """Request for file download."""
    session_id: str = Field(..., description="Session identifier")
    file_type: str = Field(..., description="Type of file to download")


class DownloadResponse(BaseModel):
    """Response with download information."""
    download_url: str = Field(..., description="URL for file download")
    filename: str = Field(..., description="Suggested filename")
    file_size: int = Field(..., description="File size in bytes")
    expires_at: datetime = Field(..., description="Download link expiration")


# Text Generation Models
class RegionTextInput(BaseModel):
    """Individual region text input for generation."""
    region_id: str = Field(..., description="ID of the text region")
    user_text: str = Field(..., description="User-provided text to render")


class GenerateTextRequest(BaseModel):
    """Request for generating text in regions."""
    regions_with_text: List[RegionTextInput] = Field(
        ..., 
        description="List of regions with user-provided text"
    )


class TextPreviewInfo(BaseModel):
    """Preview information for text rendering."""
    text_width: int = Field(..., description="Rendered text width in pixels")
    text_height: int = Field(..., description="Rendered text height in pixels")
    position: dict = Field(..., description="Text position coordinates")
    font_properties: dict = Field(..., description="Estimated font properties")
    fits_horizontally: bool = Field(..., description="Whether text fits horizontally")
    fits_vertically: bool = Field(..., description="Whether text fits vertically")
    fits_completely: bool = Field(..., description="Whether text fits completely")


class RegionPreviewResult(BaseModel):
    """Preview result for a single region."""
    text: str = Field(..., description="Text to be rendered")
    preview: TextPreviewInfo = Field(..., description="Preview information")
    region_bounds: dict = Field(..., description="Region boundary information")


class GenerateTextPreviewResponse(BaseModel):
    """Response for text generation preview."""
    status: str = Field(..., description="Preview status")
    previews: dict = Field(..., description="Preview results by region ID")
    total_regions: int = Field(..., description="Total number of regions with text")


class GenerateTextResponse(BaseModel):
    """Response for successful text generation."""
    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="Generation status")
    processed_image_url: str = Field(..., description="URL to the generated image")
    regions_processed: int = Field(..., description="Number of regions processed")
    message: str = Field(..., description="Success message")


class TextGenerationError(ErrorResponse):
    """Text generation error response."""
    error: str = Field(default="text_generation_error")
    session_id: str = Field(..., description="Session ID that failed")
    failed_regions: List[str] = Field(
        default_factory=list, 
        description="IDs of regions that failed to process"
    )