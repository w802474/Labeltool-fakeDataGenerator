"""FastAPI routes for LabelTool API."""
import os
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger

# Import infrastructure services
from app.infrastructure.ocr.paddle_ocr_service import PaddleOCRService
from app.infrastructure.image_processing.iopaint_service import IOPaintService
from app.infrastructure.storage.file_storage import FileStorageService

# Import application use cases
from app.application.use_cases.detect_text_regions import DetectTextRegionsUseCase
from app.application.use_cases.update_text_regions import UpdateTextRegionsUseCase
from app.application.use_cases.process_text_removal import ProcessTextRemovalUseCase
from app.application.use_cases.generate_text_in_regions import GenerateTextInRegionsUseCase

# Import API models
from app.infrastructure.api.models import (
    SessionCreatedResponse,
    SessionDetailResponse,
    TextRegionsResponse,
    ProcessingStatusResponse,
    ProcessingResultResponse,
    EstimateResponse,
    HealthCheckResponse,
    ServiceInfoResponse,
    ErrorResponse,
    ValidationErrorResponse,
    FileUploadError,
    SessionNotFoundError,
    ProcessingError,
    UpdateTextRegionsRequest,
    ProcessTextRemovalRequest,
    RestoreSessionRequest,
    GenerateTextRequest,
    GenerateTextResponse,
    GenerateTextPreviewResponse,
    TextGenerationError
)

# Import DTOs
from app.application.dto.session_dto import LabelSessionDTO, TextRegionDTO

# Domain imports
from app.domain.entities.label_session import LabelSession
from app.domain.value_objects.session_status import SessionStatus


# Global session storage (in production, use Redis or database)
_sessions: Dict[str, LabelSession] = {}

# Global OCR service instance (singleton)
_ocr_service: Optional[PaddleOCRService] = None


def get_ocr_service() -> PaddleOCRService:
    """Dependency to get OCR service instance using official best practices."""
    logger.info("Creating OCR service instance with official configuration")
    return PaddleOCRService()


def get_inpainting_service() -> IOPaintService:
    """Dependency to get IOPaint inpainting service instance."""
    from app.config.settings import settings
    return IOPaintService(
        port=getattr(settings, 'iopaint_port', 8081),
        model=getattr(settings, 'iopaint_model', 'lama'),
        device=getattr(settings, 'iopaint_device', 'cpu')
    )


def get_file_service() -> FileStorageService:
    """Dependency to get file storage service instance."""
    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    processed_dir = os.getenv("PROCESSED_DIR", "processed")
    return FileStorageService(upload_dir=upload_dir, processed_dir=processed_dir)


def get_detect_use_case(
    ocr_service: PaddleOCRService = Depends(get_ocr_service),
    file_service: FileStorageService = Depends(get_file_service)
) -> DetectTextRegionsUseCase:
    """Dependency to get detect text regions use case."""
    return DetectTextRegionsUseCase(ocr_service, file_service)


def get_update_use_case() -> UpdateTextRegionsUseCase:
    """Dependency to get update text regions use case."""
    return UpdateTextRegionsUseCase()


def get_process_use_case(
    inpainting_service: IOPaintService = Depends(get_inpainting_service),
    file_service: FileStorageService = Depends(get_file_service)
) -> ProcessTextRemovalUseCase:
    """Dependency to get process text removal use case."""
    return ProcessTextRemovalUseCase(inpainting_service, file_service)


def convert_session_to_dto(session: LabelSession) -> LabelSessionDTO:
    """Convert domain LabelSession to DTO."""
    from app.application.dto.session_dto import (
        LabelSessionDTO, ImageFileDTO, TextRegionDTO, DimensionsDTO,
        RectangleDTO, PointDTO
    )
    
    # Convert original image
    original_image_dto = ImageFileDTO(
        id=session.original_image.id,
        filename=session.original_image.filename,
        path=session.original_image.path,
        mime_type=session.original_image.mime_type,
        size=session.original_image.size,
        dimensions=DimensionsDTO(
            width=session.original_image.dimensions.width,
            height=session.original_image.dimensions.height
        )
    )
    
    # Convert processed image if exists
    processed_image_dto = None
    if session.processed_image:
        processed_image_dto = ImageFileDTO(
            id=session.processed_image.id,
            filename=session.processed_image.filename,
            path=session.processed_image.path,
            mime_type=session.processed_image.mime_type,
            size=session.processed_image.size,
            dimensions=DimensionsDTO(
                width=session.processed_image.dimensions.width,
                height=session.processed_image.dimensions.height
            )
        )
    
    # Convert text regions (OCR regions)
    text_regions_dto = []
    for region in session.text_regions:
        # Convert original_box_size if it exists
        original_box_size_dto = None
        if hasattr(region, 'original_box_size') and region.original_box_size:
            original_box_size_dto = RectangleDTO(
                x=region.original_box_size.x,
                y=region.original_box_size.y,
                width=region.original_box_size.width,
                height=region.original_box_size.height
            )
        
        region_dto = TextRegionDTO(
            id=region.id,
            bounding_box=RectangleDTO(
                x=region.bounding_box.x,
                y=region.bounding_box.y,
                width=region.bounding_box.width,
                height=region.bounding_box.height
            ),
            confidence=region.confidence,
            corners=[
                PointDTO(x=point.x, y=point.y) for point in region.corners
            ],
            is_selected=region.is_selected,
            is_user_modified=region.is_user_modified,
            original_text=region.original_text,
            edited_text=region.edited_text,
            user_input_text=getattr(region, 'user_input_text', None),
            font_properties=getattr(region, 'font_properties', None),
            original_box_size=original_box_size_dto,
            is_size_modified=getattr(region, 'is_size_modified', False)
        )
        text_regions_dto.append(region_dto)
    
    # Convert processed text regions if they exist
    processed_text_regions_dto = None
    if session.processed_text_regions:
        processed_text_regions_dto = []
        for region in session.processed_text_regions:
            # Convert original_box_size if it exists
            original_box_size_dto = None
            if hasattr(region, 'original_box_size') and region.original_box_size:
                original_box_size_dto = RectangleDTO(
                    x=region.original_box_size.x,
                    y=region.original_box_size.y,
                    width=region.original_box_size.width,
                    height=region.original_box_size.height
                )
            
            region_dto = TextRegionDTO(
                id=region.id,
                bounding_box=RectangleDTO(
                    x=region.bounding_box.x,
                    y=region.bounding_box.y,
                    width=region.bounding_box.width,
                    height=region.bounding_box.height
                ),
                confidence=region.confidence,
                corners=[
                    PointDTO(x=point.x, y=point.y) for point in region.corners
                ],
                is_selected=region.is_selected,
                is_user_modified=region.is_user_modified,
                original_text=region.original_text,
                edited_text=region.edited_text,
                user_input_text=getattr(region, 'user_input_text', None),
                font_properties=getattr(region, 'font_properties', None),
                original_box_size=original_box_size_dto,
                is_size_modified=getattr(region, 'is_size_modified', False)
            )
            processed_text_regions_dto.append(region_dto)
    
    return LabelSessionDTO(
        id=session.id,
        original_image=original_image_dto,
        text_regions=text_regions_dto,
        processed_text_regions=processed_text_regions_dto,
        processed_image=processed_image_dto,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        error_message=session.error_message
    )


def get_session_or_404(session_id: str) -> LabelSession:
    """Get session by ID or raise 404."""
    if session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    return _sessions[session_id]


# Create router
router = APIRouter(prefix="/api/v1", tags=["labeltool"])


@router.post(
    "/sessions",
    response_model=SessionCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new labeling session",
    description="Upload an image and create a new labeling session with automatic text detection"
)
async def create_session(
    file: UploadFile = File(..., description="Image file to process"),
    detect_use_case: DetectTextRegionsUseCase = Depends(get_detect_use_case)
):
    """Create a new labeling session with uploaded image."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Read file data
        file_data = await file.read()
        
        # Validate input
        validation = detect_use_case.validate_input(file_data, file.filename)
        if not validation['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File validation failed: {validation['issues']}"
            )
        
        # Execute text detection
        session = await detect_use_case.execute(file_data, file.filename)
        
        # Store session
        _sessions[session.id] = session
        
        logger.info(f"Created session {session.id} with {len(session.text_regions)} regions")
        
        return SessionCreatedResponse(
            session_id=session.id,
            status=session.status.value,
            message=f"Session created successfully with {len(session.text_regions)} text regions detected"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get session details",
    description="Retrieve complete session information including text regions"
)
async def get_session(session_id: str):
    """Get session details by ID."""
    try:
        session = get_session_or_404(session_id)
        session_dto = convert_session_to_dto(session)
        
        return SessionDetailResponse(session=session_dto)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.put(
    "/sessions/{session_id}/regions",
    response_model=SessionDetailResponse,
    summary="Update text regions",
    description="Update text regions with manual adjustments"
)
async def update_text_regions(
    session_id: str,
    request: UpdateTextRegionsRequest,
    update_use_case: UpdateTextRegionsUseCase = Depends(get_update_use_case)
):
    """Update text regions for a session."""
    try:
        session = get_session_or_404(session_id)
        
        # Execute update with mode and CSV export control
        updated_session = await update_use_case.execute(session, request.regions, request.mode, request.export_csv)
        
        # Update stored session
        _sessions[session_id] = updated_session
        
        logger.info(f"Updated {len(request.regions)} regions for session {session_id} (mode: {request.mode})")
        
        # Convert to DTO and return full session
        session_dto = convert_session_to_dto(updated_session)
        return SessionDetailResponse(session=session_dto)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update regions for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update regions: {str(e)}"
        )


@router.post(
    "/sessions/{session_id}/process",
    response_model=SessionDetailResponse,
    summary="Process text removal",
    description="Start text removal processing for the session"
)
async def process_text_removal(
    session_id: str,
    request: ProcessTextRemovalRequest = ProcessTextRemovalRequest(),
    process_use_case: ProcessTextRemovalUseCase = Depends(get_process_use_case)
):
    """Process text removal for a session."""
    try:
        session = get_session_or_404(session_id)
        
        # CRITICAL: Always use regions from request if provided to avoid coordinate duplication
        if request.regions:
            logger.info(f"🔄 REPLACING session {session_id} regions with {len(request.regions)} regions from request")
            
            # DETECT DUPLICATE REGIONS: Check for regions with same bounding box or overlapping areas
            region_positions = {}
            duplicate_positions = []
            
            for i, region_dto in enumerate(request.regions):
                bbox_key = f"{region_dto.bounding_box.x:.1f},{region_dto.bounding_box.y:.1f},{region_dto.bounding_box.width:.1f}x{region_dto.bounding_box.height:.1f}"
                
                if bbox_key in region_positions:
                    duplicate_positions.append({
                        'position': bbox_key,
                        'first_region_id': region_positions[bbox_key]['id'], 
                        'first_user_modified': region_positions[bbox_key]['user_modified'],
                        'duplicate_region_id': region_dto.id,
                        'duplicate_user_modified': region_dto.is_user_modified,
                        'index1': region_positions[bbox_key]['index'],
                        'index2': i + 1
                    })
                else:
                    region_positions[bbox_key] = {
                        'id': region_dto.id,
                        'user_modified': region_dto.is_user_modified,
                        'index': i + 1
                    }
            
            if duplicate_positions:
                logger.warning(f"⚠️ FOUND {len(duplicate_positions)} DUPLICATE POSITIONS:")
                for dup in duplicate_positions:
                    logger.warning(
                        f"  Position {dup['position']}: "
                        f"Region{dup['index1']}(id={dup['first_region_id'][:8]}, modified={dup['first_user_modified']}) "
                        f"vs Region{dup['index2']}(id={dup['duplicate_region_id'][:8]}, modified={dup['duplicate_user_modified']})"
                    )
            else:
                logger.info("✅ No duplicate positions detected in request")
            # Convert DTOs to domain objects and update session
            from app.domain.entities.text_region import TextRegion
            from app.domain.value_objects.rectangle import Rectangle
            from app.domain.value_objects.point import Point
            
            # Log region count for comparison
            logger.info(f"📋 Original session had {len(session.text_regions)} regions")
            
            updated_regions = []
            for i, region_dto in enumerate(request.regions):
                
                corners = [Point(p.x, p.y) for p in region_dto.corners]
                bounding_box = Rectangle(
                    region_dto.bounding_box.x,
                    region_dto.bounding_box.y,
                    region_dto.bounding_box.width,
                    region_dto.bounding_box.height
                )
                
                region = TextRegion(
                    id=region_dto.id,
                    bounding_box=bounding_box,
                    confidence=region_dto.confidence,
                    corners=corners,
                    is_selected=region_dto.is_selected,
                    is_user_modified=region_dto.is_user_modified,
                    original_text=region_dto.original_text,
                    edited_text=region_dto.edited_text
                )
                updated_regions.append(region)
            
            # CRITICAL: Completely replace session regions, do not merge
            session.text_regions = updated_regions
            logger.info(f"🔥 Session {session_id} regions COMPLETELY REPLACED with {len(updated_regions)} new regions")
            
            # CRITICAL: Immediately update session in global storage
            _sessions[session_id] = session
            logger.info(f"✅ Session {session_id} updated in global storage")
            
            # VERIFY: Check what was actually stored
            stored_session = _sessions[session_id]
            logger.info(f"🔍 VERIFICATION: Stored session has {len(stored_session.text_regions)} regions")
            
            # Check specifically for user-modified regions
            user_modified_count = sum(1 for r in stored_session.text_regions if r.is_user_modified)
            logger.info(f"🔍 VERIFICATION: Found {user_modified_count} user-modified regions in stored session")
        else:
            logger.warning(f"⚠️ No regions provided in request, using existing {len(session.text_regions)} regions from session")
        
        # CRITICAL: Ensure we use the updated session from storage, not the original one
        updated_session = _sessions[session_id]  # Get the updated session
        logger.info(f"🎯 FINAL: Updated session {session_id} will process {len(updated_session.text_regions)} regions")
        
        # Show ALL user-modified regions in final session
        final_user_modified = [r for r in updated_session.text_regions if r.is_user_modified]
        if final_user_modified:
            logger.info(f"🎯 FINAL: Found {len(final_user_modified)} user-modified regions")
        
        # Replace the original session variable with the updated one
        session = updated_session
        
        # Validate session is ready for processing
        validation = process_use_case.validate_processing_request(session, request.inpainting_method)
        if not validation['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session not ready for processing: {validation['issues']}"
            )
        
        # Start IOPaint service if needed
        if hasattr(process_use_case.inpainting_service, 'start_service'):
            await process_use_case.inpainting_service.start_service()
        
        try:
            # Execute processing
            processed_session = await process_use_case.execute(
                session,
                inpainting_method=request.inpainting_method,
                custom_radius=request.custom_radius
            )
        finally:
            # Clean up IOPaint service if needed
            if hasattr(process_use_case.inpainting_service, 'stop_service'):
                await process_use_case.inpainting_service.stop_service()
        
        # Update stored session
        _sessions[session_id] = processed_session
        
        logger.info(f"Completed text removal processing for session {session_id}")
        
        return SessionDetailResponse(
            session=convert_session_to_dto(processed_session)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process text removal for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process text removal: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}/image",
    response_class=FileResponse,
    summary="Get original image",
    description="Get the original uploaded image for display"
)
async def get_original_image(session_id: str):
    """Get the original uploaded image."""
    try:
        session = get_session_or_404(session_id)
        
        if not session.original_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original image not found"
            )
        
        if not os.path.exists(session.original_image.path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original image file not found on disk"
            )
        
        return FileResponse(
            path=session.original_image.path,
            media_type=session.original_image.mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get original image for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get original image: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}/result",
    response_class=FileResponse,
    summary="Download processed image",
    description="Download the processed image with text removed"
)
async def download_result(session_id: str):
    """Download the processed image result."""
    try:
        session = get_session_or_404(session_id)
        
        if session.status not in [SessionStatus.COMPLETED, SessionStatus.GENERATED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session processing not completed (status: {session.status.value})"
            )
        
        if not session.processed_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processed image not found"
            )
        
        if not os.path.exists(session.processed_image.path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processed image file not found on disk"
            )
        
        return FileResponse(
            path=session.processed_image.path,
            filename=session.processed_image.filename,
            media_type=session.processed_image.mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download result for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download result: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}/export/csv",
    response_class=FileResponse,
    summary="Download regions CSV",
    description="Download the exported text regions CSV file"
)
async def download_regions_csv(
    session_id: str,
    file_service: FileStorageService = Depends(get_file_service)
):
    """Download the exported text regions CSV file."""
    try:
        session = get_session_or_404(session_id)
        
        # Check if CSV file exists in exports directory
        csv_filename = f"{session.original_image.id}_regions.csv"  # Match naming convention
        csv_path = file_service.get_export_path(csv_filename)
        
        if not csv_path.exists():
            logger.warning(f"CSV file not found for session {session_id}: {csv_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Regions CSV file not found. Please save regions first."
            )
        
        logger.info(f"Downloading CSV file for session {session_id}: {csv_path}")
        
        return FileResponse(
            path=str(csv_path),
            filename=f"{session.original_image.filename}_regions.csv",
            media_type="text/csv"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download CSV for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download CSV: {str(e)}"
        )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete session",
    description="Delete a session and clean up associated files"
)
async def delete_session(
    session_id: str,
    file_service: FileStorageService = Depends(get_file_service)
):
    """Delete a session and clean up files."""
    try:
        session = get_session_or_404(session_id)
        
        # Clean up files
        files_to_delete = [session.original_image.path]
        if session.processed_image:
            files_to_delete.append(session.processed_image.path)
        
        for file_path in files_to_delete:
            if os.path.exists(file_path):
                file_service.delete_file(file_path)
        
        # Remove from session storage
        del _sessions[session_id]
        
        logger.info(f"Deleted session {session_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}/estimate",
    response_model=EstimateResponse,
    summary="Estimate processing time",
    description="Get processing time estimate for the session"
)
async def estimate_processing_time(
    session_id: str,
    process_use_case: ProcessTextRemovalUseCase = Depends(get_process_use_case)
):
    """Get processing time estimate for a session."""
    try:
        session = get_session_or_404(session_id)
        
        estimate = await process_use_case.estimate_processing_time(session)
        
        return EstimateResponse(**estimate)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to estimate processing time for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate processing time: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    description="Check API and service health status"
)
async def health_check(
    ocr_service: PaddleOCRService = Depends(get_ocr_service),
    file_service: FileStorageService = Depends(get_file_service)
):
    """Health check endpoint."""
    try:
        # Check services
        ocr_info = ocr_service.get_device_info()
        storage_info = file_service.get_storage_info()
        
        services = {
            "ocr": {
                "status": "healthy" if ocr_info['ocr_initialized'] else "unhealthy",
                "device": ocr_info['device'],
                "cuda_available": ocr_info['cuda_available']
            },
            "storage": {
                "status": "healthy",
                "upload_dir": storage_info['upload_dir']['exists'],
                "processed_dir": storage_info['processed_dir']['exists']
            }
        }
        
        overall_status = "healthy" if all(
            s['status'] == 'healthy' for s in services.values()
        ) else "unhealthy"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version="1.0.0",
            services=services
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version="1.0.0",
            services={"error": str(e)}
        )


@router.get(
    "/info",
    response_model=ServiceInfoResponse,
    summary="Service information",
    description="Get service configuration and capabilities"
)
async def service_info(
    ocr_service: PaddleOCRService = Depends(get_ocr_service),
    file_service: FileStorageService = Depends(get_file_service)
):
    """Get service information."""
    try:
        ocr_info = ocr_service.get_device_info()
        storage_info = file_service.get_storage_info()
        
        return ServiceInfoResponse(
            ocr_device=ocr_info['device'],
            supported_formats=list(storage_info['supported_types']),
            max_file_size=storage_info['max_file_size'],
            storage_info={
                "upload_dir": storage_info['upload_dir'],
                "processed_dir": storage_info['processed_dir']
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get service info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service info: {str(e)}"
        )


@router.post(
    "/sessions/{session_id}/generate-text",
    response_model=GenerateTextResponse,
    summary="Generate text in regions",
    description="Generate user-provided text in specified regions of the processed image"
)
async def generate_text_in_regions(
    session_id: str,
    request: GenerateTextRequest
):
    """Generate text in specified regions."""
    try:
        # Get session
        if session_id not in _sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        session = _sessions[session_id]
        
        # Validate session state
        if session.status not in [SessionStatus.DETECTED, SessionStatus.EDITING, SessionStatus.COMPLETED, SessionStatus.GENERATED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session {session_id} is not ready for text generation (status: {session.status.value})"
            )
        
        # Convert request to use case format
        regions_with_text = []
        for region_input in request.regions_with_text:
            regions_with_text.append({
                'region_id': region_input.region_id,
                'user_text': region_input.user_text
            })
        
        # Execute text generation
        text_generation_use_case = GenerateTextInRegionsUseCase()
        updated_session = await text_generation_use_case.execute(session, regions_with_text)
        
        # Update session in storage
        _sessions[session_id] = updated_session
        
        # Return response
        return GenerateTextResponse(
            session_id=session_id,
            status="completed",
            processed_image_url=f"/api/sessions/{session_id}/result",
            regions_processed=len([r for r in regions_with_text if r['user_text'].strip()]),
            message="Text generation completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text generation failed for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/sessions/{session_id}/preview-text",
    response_model=GenerateTextPreviewResponse,
    summary="Preview text generation",
    description="Preview how text will look in specified regions without actually generating the image"
)
async def preview_text_generation(
    session_id: str,
    request: GenerateTextRequest
):
    """Preview text generation without creating the actual image."""
    try:
        # Get session
        if session_id not in _sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        session = _sessions[session_id]
        
        # Convert request to use case format
        regions_with_text = []
        for region_input in request.regions_with_text:
            regions_with_text.append({
                'region_id': region_input.region_id,
                'user_text': region_input.user_text
            })
        
        # Execute preview
        text_generation_use_case = GenerateTextInRegionsUseCase()
        preview_result = text_generation_use_case.preview_text_generation(session, regions_with_text)
        
        return GenerateTextPreviewResponse(
            status=preview_result['status'],
            previews=preview_result.get('previews', {}),
            total_regions=preview_result.get('total_regions', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text preview failed for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put(
    "/sessions/{session_id}/restore",
    response_model=SessionDetailResponse,
    summary="Restore session state",
    description="Restore session to a previous state (for undo operations)"
)
async def restore_session_state(
    session_id: str,
    request: RestoreSessionRequest
):
    """Restore session state for undo operations."""
    try:
        # Get session
        if session_id not in _sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        session = _sessions[session_id]
        logger.info(f"Restoring session {session_id} state")
        
        # Update processed image if provided
        if request.processed_image:
            from app.domain.value_objects.image_file import ImageFile, Dimensions
            
            # Convert ImageFileDTO to domain ImageFile
            restored_image = ImageFile(
                id=request.processed_image.id,
                filename=request.processed_image.filename,
                path=request.processed_image.path,
                mime_type=request.processed_image.mime_type,
                size=request.processed_image.size,
                dimensions=Dimensions(
                    width=request.processed_image.dimensions.width,
                    height=request.processed_image.dimensions.height
                )
            )
            session.processed_image = restored_image
            logger.info(f"Restored processed_image to: {restored_image.path}")
        else:
            session.processed_image = None
            logger.info("Set processed_image to None")
        
        # Update processed text regions
        if request.processed_text_regions:
            from app.application.use_cases.update_text_regions import UpdateTextRegionsUseCase
            from app.infrastructure.ocr.paddle_ocr_service import PaddleOCRService
            
            # Convert DTOs to domain TextRegions
            update_use_case = UpdateTextRegionsUseCase(PaddleOCRService())
            converted_regions = []
            for region_dto in request.processed_text_regions:
                converted_region = update_use_case._convert_dto_to_domain(region_dto)
                converted_regions.append(converted_region)
            
            session.processed_text_regions = converted_regions
            logger.info(f"Restored {len(converted_regions)} processed text regions")
        else:
            session.processed_text_regions = []
            logger.info("Set processed_text_regions to empty")
        
        # Update session in storage
        _sessions[session_id] = session
        
        # Convert to DTO and return
        session_dto = convert_session_to_dto(session)
        
        logger.info(f"Session {session_id} state restored successfully")
        return SessionDetailResponse(session=session_dto)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session restore failed for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )