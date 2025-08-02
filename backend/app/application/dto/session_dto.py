"""Data transfer objects for session management."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.domain.value_objects.session_status import SessionStatus


class PointDTO(BaseModel):
    """Point data transfer object."""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")


class RectangleDTO(BaseModel):
    """Rectangle data transfer object."""
    x: float = Field(..., ge=0, description="X coordinate of top-left corner")
    y: float = Field(..., ge=0, description="Y coordinate of top-left corner") 
    width: float = Field(..., gt=0, description="Width of rectangle")
    height: float = Field(..., gt=0, description="Height of rectangle")


class DimensionsDTO(BaseModel):
    """Image dimensions data transfer object."""
    width: int = Field(..., gt=0, description="Image width in pixels")
    height: int = Field(..., gt=0, description="Image height in pixels")


class ImageFileDTO(BaseModel):
    """Image file data transfer object."""
    id: str = Field(..., description="Unique image identifier")
    filename: str = Field(..., description="Original filename")
    path: str = Field(..., description="File path on server")
    mime_type: str = Field(..., description="MIME type of image")
    size: int = Field(..., gt=0, description="File size in bytes")
    dimensions: DimensionsDTO = Field(..., description="Image dimensions")


class TextRegionDTO(BaseModel):
    """Text region data transfer object."""
    id: str = Field(..., description="Unique region identifier")
    bounding_box: RectangleDTO = Field(..., description="Bounding box coordinates")
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR confidence score")
    corners: List[PointDTO] = Field(..., min_length=4, max_length=4, description="Four corner points")
    is_selected: bool = Field(default=False, description="Whether region is selected")
    is_user_modified: bool = Field(default=False, description="Whether region was modified by user")
    original_text: Optional[str] = Field(None, description="Original detected text")
    edited_text: Optional[str] = Field(None, description="User-edited text")
    user_input_text: Optional[str] = Field(None, description="User-provided text for text generation")
    font_properties: Optional[dict] = Field(None, description="Estimated font properties for text rendering")
    original_box_size: Optional[RectangleDTO] = Field(None, description="Original bounding box size for scaling calculations")
    is_size_modified: bool = Field(default=False, description="Whether the user has modified the box size")
    text_category: Optional[str] = Field(None, description="Text classification category")
    category_config: Optional[dict] = Field(None, description="Category color and display configuration")


class LabelSessionDTO(BaseModel):
    """Label session data transfer object."""
    id: str = Field(..., description="Unique session identifier")
    original_image: ImageFileDTO = Field(..., description="Original uploaded image")
    text_regions: List[TextRegionDTO] = Field(default_factory=list, description="OCR detected text regions")
    processed_text_regions: Optional[List[TextRegionDTO]] = Field(None, description="User-modified regions for processed image")
    processed_image: Optional[ImageFileDTO] = Field(None, description="Processed image after text removal")
    status: SessionStatus = Field(..., description="Current session status")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    error_message: Optional[str] = Field(None, description="Error message if any")


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""
    # File will be handled separately through multipart upload
    pass


class UpdateTextRegionsRequest(BaseModel):
    """Request to update text regions."""
    regions: List[TextRegionDTO] = Field(..., description="Updated text regions")
    mode: Optional[str] = Field(default="auto", description="Update mode: 'ocr', 'processed', or 'auto'")
    export_csv: Optional[bool] = Field(default=True, description="Whether to export regions to CSV file")




class RestoreSessionRequest(BaseModel):
    """Request to restore session state (for undo operations)."""
    processed_image: Optional[ImageFileDTO] = Field(None, description="Processed image to restore")
    processed_text_regions: List[TextRegionDTO] = Field(default_factory=list, description="Processed text regions to restore")


class SessionResponse(BaseModel):
    """Response containing session data."""
    session: LabelSessionDTO = Field(..., description="Session data")
    
    
class ProcessingProgressResponse(BaseModel):
    """Response for processing progress updates."""
    session_id: str = Field(..., description="Session identifier")
    status: SessionStatus = Field(..., description="Current processing status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress percentage (0.0 to 1.0)")
    message: str = Field(..., description="Progress message")
    estimated_time_remaining: Optional[int] = Field(
        None, 
        description="Estimated time remaining in seconds"
    )


class ErrorResponse(BaseModel):
    """Error response format."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")


class ValidationErrorResponse(BaseModel):
    """Validation error response format."""
    error: str = Field(default="validation_error", description="Error type")
    message: str = Field(..., description="Validation error message")
    field_errors: Optional[dict] = Field(None, description="Field-specific validation errors")