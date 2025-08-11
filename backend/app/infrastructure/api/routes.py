"""FastAPI routes for LabelTool API."""
import base64
import os
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

# Import infrastructure services
from app.infrastructure.ocr.paddle_ocr_service import PaddleOCRService
from app.infrastructure.clients.iopaint_client import IOPaintClient
from app.infrastructure.storage.file_storage import FileStorageService
from app.infrastructure.database.config import get_db_session
from app.infrastructure.database.repositories import SessionRepository
from app.config.settings import settings

# Import application use cases
from app.application.use_cases.detect_text_regions import DetectTextRegionsUseCase
from app.application.use_cases.update_text_regions import UpdateTextRegionsUseCase
from app.application.use_cases.process_text_removal_async import ProcessTextRemovalAsyncUseCase
from app.application.use_cases.generate_text_in_regions import GenerateTextInRegionsUseCase
from app.application.use_cases.list_sessions import ListSessionsUseCase, SessionStatisticsUseCase

# Import API models
from app.infrastructure.api.models import (
    SessionCreatedResponse,
    SessionDetailResponse,
    TextRegionsResponse,
    ProcessingStatusResponse,
    ProcessingResultResponse,
    HealthCheckResponse,
    ServiceInfoResponse,
    ErrorResponse,
    ValidationErrorResponse,
    FileUploadError,
    SessionNotFoundError,
    ProcessingError,
    UpdateTextRegionsRequest,
    RestoreSessionRequest,
    GenerateTextRequest,
    GenerateTextResponse,
    GenerateTextPreviewResponse,
    TextGenerationError,
    ProcessTextRemovalAsyncRequest,
    ProcessTextRemovalAsyncResponse,
    TaskStatusResponse,
    TaskCancelResponse,
    BulkDeleteRequest,
    BulkDeleteResponse
)

# Import DTOs
from app.application.dto.session_dto import LabelSessionDTO, TextRegionDTO

# Domain imports
from app.domain.entities.label_session import LabelSession
from app.domain.value_objects.session_status import SessionStatus
from app.domain.value_objects.image_file import ImageFile



# Global OCR service instance (singleton)
_ocr_service: Optional[PaddleOCRService] = None

# Global async processing use case (singleton for task management)
_async_processor: Optional[ProcessTextRemovalAsyncUseCase] = None


def get_global_async_processor() -> ProcessTextRemovalAsyncUseCase:
    """Get or create global async processor instance."""
    global _async_processor
    if _async_processor is None:
        iopaint_client = get_inpainting_service()
        file_service = get_file_service()
        _async_processor = ProcessTextRemovalAsyncUseCase(iopaint_client, file_service)
    return _async_processor


def get_ocr_service() -> PaddleOCRService:
    """Dependency to get OCR service instance using official best practices."""
    logger.info("Creating OCR service instance with official configuration")
    return PaddleOCRService()


def get_inpainting_service() -> IOPaintClient:
    """Dependency to get IOPaint client instance."""
    from app.config.settings import settings
    base_url = f"http://iopaint-service:{getattr(settings, 'iopaint_port', 8081)}"
    return IOPaintClient(
        base_url=base_url,
        timeout=300  # 5 minutes timeout
    )


def get_file_service() -> FileStorageService:
    """Dependency to get file storage service instance."""
    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    processed_dir = os.getenv("PROCESSED_DIR", "processed")
    return FileStorageService(upload_dir=upload_dir, processed_dir=processed_dir)


def get_detect_use_case(
    ocr_service: PaddleOCRService = Depends(get_ocr_service),
    file_service: FileStorageService = Depends(get_file_service),
    db: AsyncSession = Depends(get_db_session)
) -> DetectTextRegionsUseCase:
    """Dependency to get detect text regions use case."""
    return DetectTextRegionsUseCase(ocr_service, file_service, db)


def get_update_use_case(
    db: AsyncSession = Depends(get_db_session),
    file_service: FileStorageService = Depends(get_file_service)
) -> UpdateTextRegionsUseCase:
    """Dependency to get update text regions use case."""
    return UpdateTextRegionsUseCase(file_service, db)


def get_async_process_use_case(
    inpainting_service: IOPaintClient = Depends(get_inpainting_service),
    file_service: FileStorageService = Depends(get_file_service)
) -> ProcessTextRemovalAsyncUseCase:
    """Dependency to get async process text removal use case."""
    return ProcessTextRemovalAsyncUseCase(inpainting_service, file_service)


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
            is_size_modified=getattr(region, 'is_size_modified', False),
            text_category=getattr(region, 'text_category', None),
            category_config=getattr(region, 'category_config', None)
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
                is_size_modified=getattr(region, 'is_size_modified', False),
                text_category=getattr(region, 'text_category', None),
                category_config=getattr(region, 'category_config', None)
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


async def get_session_or_404(session_id: str, db_session: AsyncSession) -> LabelSession:
    """Get session by ID from database or raise 404."""
    repository = SessionRepository(db_session)
    session = await repository.get_by_id(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    return session


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
        
        # Session is already stored in database by detect_use_case.execute
        
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
async def get_session(session_id: str, db_session: AsyncSession = Depends(get_db_session)):
    """Get session details by ID."""
    try:
        session = await get_session_or_404(session_id, db_session)
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
    update_use_case: UpdateTextRegionsUseCase = Depends(get_update_use_case),
    db_session: AsyncSession = Depends(get_db_session)
):
    """Update text regions for a session."""
    try:
        session = await get_session_or_404(session_id, db_session)
        
        # Execute update with mode and CSV export control
        updated_session = await update_use_case.execute(session, request.regions, request.mode, request.export_csv)
        
        # Session is already updated in database by update_use_case.execute
        
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


# Removed deprecated synchronous processing endpoint
# Use /process-async for better performance and real-time progress


@router.get(
    "/sessions/{session_id}/image",
    response_class=FileResponse,
    summary="Get original image",
    description="Get the original uploaded image for display"
)
async def get_original_image(session_id: str, db_session: AsyncSession = Depends(get_db_session)):
    """Get the original uploaded image."""
    try:
        session = await get_session_or_404(session_id, db_session)
        
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
async def download_result(session_id: str, db_session: AsyncSession = Depends(get_db_session)):
    """Download the processed image result."""
    try:
        session = await get_session_or_404(session_id, db_session)
        
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
    file_service: FileStorageService = Depends(get_file_service),
    db_session: AsyncSession = Depends(get_db_session)
):
    """Download the exported text regions CSV file."""
    try:
        session = await get_session_or_404(session_id, db_session)
        
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
    "/sessions/bulk",
    response_model=BulkDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk delete sessions",
    description="Delete multiple sessions and clean up associated files"
)
async def bulk_delete_sessions(
    request: BulkDeleteRequest,
    file_service: FileStorageService = Depends(get_file_service),
    db_session: AsyncSession = Depends(get_db_session)
):
    """Delete multiple sessions and clean up their files."""
    try:
        repository = SessionRepository(db_session)
        deleted_sessions = []
        failed_sessions = []
        
        logger.info(f"Starting bulk deletion of {len(request.session_ids)} sessions")
        
        for session_id in request.session_ids:
            try:
                # Get session
                session = await repository.get_by_id(session_id)
                if not session:
                    failed_sessions.append({
                        "session_id": session_id,
                        "error": "Session not found"
                    })
                    continue
                
                # Clean up files
                files_to_delete = [session.original_image.path]
                if session.processed_image:
                    files_to_delete.append(session.processed_image.path)
                
                # Delete files from disk
                for file_path in files_to_delete:
                    if os.path.exists(file_path):
                        try:
                            file_service.delete_file(file_path)
                        except Exception as file_error:
                            logger.warning(f"Failed to delete file {file_path}: {file_error}")
                
                # Delete CSV export file if exists
                try:
                    csv_filename = f"{session.original_image.id}_regions.csv"
                    csv_path = file_service.get_export_path(csv_filename)
                    if csv_path.exists():
                        csv_path.unlink()
                except Exception as csv_error:
                    logger.warning(f"Failed to delete CSV file for session {session_id}: {csv_error}")
                
                # Remove from database
                await repository.delete(session_id)
                deleted_sessions.append(session_id)
                
                logger.info(f"Successfully deleted session {session_id}")
                
            except Exception as session_error:
                logger.error(f"Failed to delete session {session_id}: {session_error}")
                failed_sessions.append({
                    "session_id": session_id,
                    "error": str(session_error)
                })
        
        # Prepare response
        total_deleted = len(deleted_sessions)
        total_requested = len(request.session_ids)
        
        if total_deleted == total_requested:
            message = f"Successfully deleted all {total_deleted} sessions"
        elif total_deleted > 0:
            message = f"Deleted {total_deleted} of {total_requested} sessions ({len(failed_sessions)} failed)"
        else:
            message = f"Failed to delete all {total_requested} sessions"
        
        logger.info(f"Bulk deletion completed: {total_deleted}/{total_requested} successful")
        
        return BulkDeleteResponse(
            deleted_sessions=deleted_sessions,
            failed_sessions=failed_sessions,
            total_requested=total_requested,
            total_deleted=total_deleted,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Bulk deletion operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk deletion failed: {str(e)}"
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
    request: GenerateTextRequest,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Generate text in specified regions."""
    try:
        # Get session from database
        session = await get_session_or_404(session_id, db_session)
        
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
        
        # Session is already updated in database by use case
        
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
    request: GenerateTextRequest,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Preview text generation without creating the actual image."""
    try:
        # Get session from database
        session = await get_session_or_404(session_id, db_session)
        
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
    request: RestoreSessionRequest,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Restore session state for undo operations."""
    try:
        # Get session from database
        session = await get_session_or_404(session_id, db_session)
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
        
        # Update session in database
        repository = SessionRepository(db_session)
        await repository.update(session)
        
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


# Async Processing Endpoints
@router.post(
    "/sessions/{session_id}/process-async",
    response_model=ProcessTextRemovalAsyncResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start async text removal processing",
    description="Start async text removal processing with real-time WebSocket progress updates"
)
async def process_text_removal_async(
    session_id: str,
    request: ProcessTextRemovalAsyncRequest = ProcessTextRemovalAsyncRequest(),
    db_session: AsyncSession = Depends(get_db_session)
):
    """Start async text removal processing for a session."""
    try:
        session = await get_session_or_404(session_id, db_session)
        async_processor = get_global_async_processor()
        
        # Update session regions if provided
        if request.regions:
            logger.info(f"Updating session {session_id} with {len(request.regions)} regions from request")
            
            # Convert DTOs to domain objects
            from app.domain.entities.text_region import TextRegion
            from app.domain.value_objects.rectangle import Rectangle
            from app.domain.value_objects.point import Point
            
            updated_regions = []
            for region_dto in request.regions:
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
                    edited_text=region_dto.edited_text,
                    user_input_text=getattr(region_dto, 'user_input_text', None),
                    font_properties=getattr(region_dto, 'font_properties', None),
                    text_category=getattr(region_dto, 'text_category', None),
                    category_config=getattr(region_dto, 'category_config', None)
                )
                updated_regions.append(region)
            
            session.text_regions = updated_regions
            # Update session in database
            repository = SessionRepository(db_session)
            await repository.update(session)
        
        # Validate session for async processing
        validation = async_processor.validate_async_processing_request(
            session, request.inpainting_method
        )
        if not validation['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session not ready for async processing: {validation['issues']}"
            )
        
        # Start async processing
        task_info = await async_processor.start_async_processing(
            session=session,
            regions=session.text_regions,
            inpainting_method=request.inpainting_method,
            custom_radius=request.custom_radius,
            task_id=request.task_id  # Pass unified task_id from frontend
        )
        
        # Generate WebSocket URL
        websocket_url = request.websocket_url or f"/api/v1/ws/progress/{task_info.task_id}"
        
        # Get processing estimate
        estimate = await async_processor.estimate_processing_time(session)
        
        logger.info(f"Started async processing task {task_info.task_id} for session {session_id}")
        
        return ProcessTextRemovalAsyncResponse(
            task_id=task_info.task_id,
            session_id=session_id,
            status=task_info.status,
            message=task_info.message,
            websocket_url=websocket_url,
            estimated_duration=estimate.get('estimated_seconds')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start async processing for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start async processing: {str(e)}"
        )


@router.get(
    "/tasks/{task_id}/status",
    response_model=TaskStatusResponse,
    summary="Get async task status",
    description="Get current status and progress of an async processing task"
)
async def get_task_status(task_id: str):
    """Get status of an async processing task."""
    try:
        async_processor = get_global_async_processor()
        task_info = async_processor.get_task_status(task_id)
        
        if not task_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        return TaskStatusResponse(
            task_id=task_info.task_id,
            session_id=task_info.session_id,
            status=task_info.status,
            stage=task_info.stage,
            progress=task_info.progress,
            message=task_info.message,
            started_at=task_info.started_at,
            completed_at=task_info.completed_at,
            error_message=task_info.error_message,
            result=task_info.result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=TaskCancelResponse,
    summary="Cancel async task",
    description="Cancel an async processing task"
)
async def cancel_task(task_id: str):
    """Cancel an async processing task."""
    try:
        async_processor = get_global_async_processor()
        
        cancelled = await async_processor.cancel_task(task_id)
        
        if not cancelled:
            # Check if task exists but couldn't be cancelled
            task_info = async_processor.get_task_status(task_id)
            if not task_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task {task_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Task {task_id} cannot be cancelled (status: {task_info.status})"
                )
        
        return TaskCancelResponse(
            task_id=task_id,
            status="cancelled",
            message="Task cancellation requested successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )


@router.post("/iopaint/callback/{task_id}")
async def iopaint_callback(task_id: str, request: Request, db_session: AsyncSession = Depends(get_db_session)):
    """
    Receive processing results from IOPaint service.
    
    Args:
        task_id: IOPaint task ID
        request: Request containing processing results
    """
    from app.websocket.iopaint_client import iopaint_ws_client
    from app.domain.value_objects.image_file import ImageFile, Dimensions
    from app.domain.value_objects.session_status import SessionStatus
    import base64
    import os
    
    try:
        # Parse callback data
        callback_data = await request.json()
        
        logger.info(f"Received IOPaint callback for task {task_id}")
        
        # The task_id in the callback URL is actually the backend_task_id
        backend_task_id = task_id
        logger.info(f"Processing callback for backend task: {backend_task_id}")
        
        # Get async processor and task info
        async_processor = get_global_async_processor()
        task_info = async_processor.get_task_status(backend_task_id)
        
        if not task_info:
            logger.warning(f"Backend task {backend_task_id} not found in async processor")
            return {"status": "error", "message": "Backend task not found"}
        
        # Get session from database
        session_id = task_info.session_id
        repository = SessionRepository(db_session)
        session = await repository.get_by_id(session_id)
        
        if not session:
            logger.warning(f"Session {session_id} not found for callback")
            return {"status": "error", "message": "Session not found"}
        
        # Extract image data from callback
        image_base64 = callback_data.get("image_data")
        if not image_base64:
            logger.error("No image data in IOPaint callback")
            return {"status": "error", "message": "No image data provided"}
        
        # Decode and save processed image
        try:
            image_data = base64.b64decode(image_base64)
            
            # Save to processed directory
            file_storage = FileStorageService(
                upload_dir=settings.upload_dir,
                processed_dir=settings.processed_dir
            )
            
            processed_filename = f"processed_{session_id}.png"
            processed_path = os.path.join(settings.processed_dir, processed_filename)
            
            with open(processed_path, 'wb') as f:
                f.write(image_data)
            
            # Create processed image file object
            from uuid import uuid4
            processed_image = ImageFile(
                id=str(uuid4()),
                filename=processed_filename,
                path=processed_path,
                mime_type="image/png",
                size=len(image_data),
                dimensions=session.original_image.dimensions  # Use original dimensions for now
            )
            
            # Update session with processed image
            session.processed_image = processed_image
            session.status = SessionStatus.COMPLETED
            
            # Update session in database
            await repository.update(session)
            
            # Update task info in async processor
            task_info.status = "completed"
            task_info.stage = "completed"
            task_info.progress = 100.0
            task_info.message = "Processing completed successfully"
            task_info.completed_at = datetime.now()
            task_info.result = {
                "processed_image_path": processed_path,
                "processing_time": callback_data.get("processing_time", 0),
                "regions_processed": callback_data.get("regions_processed", 0)
            }
            
            # Send WebSocket completion notification to frontend
            from app.websocket.connection_manager import connection_manager
            progress_message = {
                "task_id": task_info.task_id,
                "status": task_info.status,
                "stage": task_info.stage,
                "progress": task_info.progress,
                "message": task_info.message,
                "session_id": task_info.session_id,
                "processed_image_url": f"/api/v1/sessions/{task_info.session_id}/result",
                "timestamp": datetime.now().isoformat()
            }
            await connection_manager.broadcast_to_task(task_info.task_id, progress_message)
            
            logger.info(f"Successfully processed IOPaint callback for task {backend_task_id}")
            
            return {"status": "success", "message": "Callback processed successfully"}
            
        except Exception as e:
            logger.error(f"Failed to process image data from callback: {e}")
            return {"status": "error", "message": f"Failed to process image: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Error processing IOPaint callback for task {task_id}: {e}")
        return {"status": "error", "message": f"Callback processing error: {str(e)}"}


# Historical sessions endpoints
@router.get("/sessions", response_model=List[dict])
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    List historical sessions with pagination and filtering.
    
    Args:
        limit: Maximum number of sessions to return (1-100)
        offset: Number of sessions to skip
        status: Optional status filter
        db: Database session
        
    Returns:
        List of session summaries
    """
    try:
        use_case = ListSessionsUseCase(db)
        sessions = await use_case.execute(
            limit=limit,
            offset=offset,
            status_filter=status
        )
        
        # Convert to response format
        session_summaries = []
        for session in sessions:
            session_summaries.append({
                "session_id": session.id,
                "filename": session.original_image.filename,
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
                "region_count": len(session.text_regions),
                "image_dimensions": {
                    "width": session.original_image.dimensions.width,
                    "height": session.original_image.dimensions.height
                } if session.original_image.dimensions else None
            })
        
        return session_summaries
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}/restore")
async def restore_session(
    session_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Restore a historical session for editing.
    
    Args:
        session_id: ID of session to restore
        db: Database session
        
    Returns:
        Complete session data
    """
    try:
        use_case = ListSessionsUseCase(db)
        session = await use_case.get_by_id(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Convert to response format (similar to get_session)
        return _convert_session_to_response(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics")
async def get_statistics(db: AsyncSession = Depends(get_db_session)):
    """
    Get processing statistics and analytics.
    
    Args:
        db: Database session
        
    Returns:
        Statistics data
    """
    try:
        use_case = SessionStatisticsUseCase(db)
        stats = await use_case.execute()
        
        # Add computed metrics
        stats["success_rate"] = (
            stats["status_distribution"].get("completed", 0) + 
            stats["status_distribution"].get("generated", 0)
        ) / max(stats["total_sessions"], 1) * 100
        
        return {
            "total_sessions": stats["total_sessions"],
            "status_distribution": stats["status_distribution"],
            "total_regions": stats["total_regions"],
            "average_confidence": round(stats["average_confidence"], 2),
            "success_rate": round(stats["success_rate"], 2),
            "category_distribution": stats["category_distribution"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/admin/cleanup",
    status_code=status.HTTP_200_OK,
    summary="Manual cleanup",
    description="Manually clean all files and database records (for development/testing)"
)
async def manual_cleanup():
    """Manually clean all files and database records."""
    try:
        # Import the cleanup function from main.py
        from app.main import cleanup_cache_directories
        
        # Execute cleanup
        cleanup_cache_directories()
        
        return {
            "message": "Cleanup completed successfully",
            "cleaned": ["uploads", "processed", "exports", "database"]
        }
        
    except Exception as e:
        logger.error(f"Manual cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )