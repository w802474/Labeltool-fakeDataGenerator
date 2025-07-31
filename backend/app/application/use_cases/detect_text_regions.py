"""Use case for detecting text regions in uploaded images."""
from loguru import logger

from app.domain.entities.label_session import LabelSession
from app.domain.value_objects.session_status import SessionStatus
from app.application.interfaces.ocr_service import OCRServicePort
from app.application.interfaces.image_service import ImageServicePort


class DetectTextRegionsUseCase:
    """Use case for OCR text detection in images."""
    
    def __init__(
        self, 
        ocr_service: OCRServicePort,
        image_service: ImageServicePort
    ):
        """
        Initialize the detect text regions use case.
        
        Args:
            ocr_service: OCR service for text detection
            image_service: Image service for file handling
        """
        self.ocr_service = ocr_service
        self.image_service = image_service
    
    async def execute(self, file_data: bytes, filename: str) -> LabelSession:
        """
        Execute text detection workflow.
        
        Args:
            file_data: Raw image file data
            filename: Original filename
            
        Returns:
            LabelSession with detected text regions
            
        Raises:
            ValueError: If image processing fails
            FileNotFoundError: If image cannot be saved
        """
        logger.info(f"Starting text detection for file: {filename}")
        
        try:
            # Save uploaded image with validation
            logger.info("Saving and validating uploaded image")
            image_file = await self.image_service.save_uploaded_image(file_data, filename)
            
            # Create new session
            session = LabelSession.create(image_file)
            logger.info(f"Created session {session.id} for image {image_file.filename}")
            
            # Transition to detecting status
            session.transition_to_status(SessionStatus.DETECTING)
            
            # Detect text regions using OCR
            logger.info(f"Running OCR detection on {image_file.path}")
            detected_regions = await self.ocr_service.detect_text_regions(image_file.path)
            
            # Add detected regions to session
            if detected_regions:
                session.add_text_regions(detected_regions)
                logger.info(f"Successfully detected {len(detected_regions)} text regions")
            else:
                logger.warning("No text regions detected in image")
                # Still transition to detected status even if no regions found
                session.transition_to_status(SessionStatus.DETECTED)
            
            # Log detection summary
            summary = session.get_processing_summary()
            logger.info(f"Detection complete: {summary}")
            
            return session
            
        except Exception as e:
            logger.error(f"Text detection failed for {filename}: {e}")
            # If we have a session, mark it as error
            if 'session' in locals():
                session.transition_to_status(
                    SessionStatus.ERROR, 
                    f"Text detection failed: {str(e)}"
                )
                return session
            raise
    
    async def execute_for_existing_session(self, session: LabelSession) -> None:
        """
        Execute text detection for an existing session.
        
        Args:
            session: Existing LabelSession to process
            
        Raises:
            ValueError: If session is not ready for detection
        """
        if not session.is_ready_for_text_detection():
            raise ValueError(f"Session {session.id} is not ready for text detection (status: {session.status.value})")
        
        logger.info(f"Running text detection for existing session {session.id}")
        
        try:
            # Transition to detecting status
            session.transition_to_status(SessionStatus.DETECTING)
            
            # Detect text regions
            detected_regions = await self.ocr_service.detect_text_regions(
                session.original_image.path
            )
            
            # Clear existing regions and add new ones
            session.text_regions.clear()
            
            if detected_regions:
                session.add_text_regions(detected_regions)
                logger.info(f"Re-detected {len(detected_regions)} text regions for session {session.id}")
            else:
                logger.warning(f"No text regions detected in re-detection for session {session.id}")
                session.transition_to_status(SessionStatus.DETECTED)
            
        except Exception as e:
            logger.error(f"Re-detection failed for session {session.id}: {e}")
            session.transition_to_status(
                SessionStatus.ERROR,
                f"Text re-detection failed: {str(e)}"
            )
            raise
    
    def validate_input(self, file_data: bytes, filename: str) -> dict:
        """
        Validate input for text detection.
        
        Args:
            file_data: Raw image file data
            filename: Original filename
            
        Returns:
            Dictionary with validation results
        """
        issues = []
        
        # Check file size
        if len(file_data) == 0:
            issues.append("File is empty")
        elif len(file_data) > 10 * 1024 * 1024:  # 10MB
            issues.append("File size exceeds 10MB limit")
        
        # Check filename
        if not filename or not filename.strip():
            issues.append("Filename is empty")
        
        # Basic file format check
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        if not any(filename.lower().endswith(ext) for ext in valid_extensions):
            issues.append("File must be JPEG, PNG, or WEBP format")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'file_size': len(file_data),
            'filename': filename
        }