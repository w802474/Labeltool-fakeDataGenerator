"""LabelSession entity - aggregate root for a labeling session."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from app.domain.value_objects.image_file import ImageFile
from app.domain.value_objects.session_status import SessionStatus
from app.domain.entities.text_region import TextRegion


@dataclass
class LabelSession:
    """Aggregate root for a labeling session."""
    
    id: str
    original_image: ImageFile
    text_regions: List[TextRegion] = field(default_factory=list)  # OCR detected regions (immutable positions)
    processed_text_regions: Optional[List[TextRegion]] = None  # User-modified regions for processed image
    processed_image: Optional[ImageFile] = None
    status: SessionStatus = SessionStatus.UPLOADED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate session properties."""
        if not self.id:
            raise ValueError("Session ID cannot be empty")
        if not self.original_image:
            raise ValueError("Original image is required")
    
    @classmethod
    def create(cls, original_image: ImageFile) -> 'LabelSession':
        """Create a new labeling session."""
        return cls(
            id=str(uuid4()),
            original_image=original_image,
            text_regions=[],
            processed_text_regions=None,
            processed_image=None,
            status=SessionStatus.UPLOADED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def transition_to_status(self, new_status: SessionStatus, error_message: Optional[str] = None) -> None:
        """Transition to a new status with validation."""
        if not self.status.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status.value} to {new_status.value}")
        
        # Clear processed image when starting new processing
        if new_status == SessionStatus.PROCESSING:
            self.processed_image = None
            from loguru import logger
            logger.info(f"Session {self.id}: Cleared previous processed image for new processing")
        
        self.status = new_status
        self.updated_at = datetime.now()
        
        if new_status == SessionStatus.ERROR:
            self.error_message = error_message
        else:
            self.error_message = None
    
    def add_text_regions(self, regions: List[TextRegion]) -> None:
        """Add detected text regions to the session."""
        if self.status not in {SessionStatus.DETECTING, SessionStatus.DETECTED}:
            raise ValueError(f"Cannot add regions in status: {self.status.value}")
        
        self.text_regions.extend(regions)
        self.updated_at = datetime.now()
        
        if self.status == SessionStatus.DETECTING:
            self.transition_to_status(SessionStatus.DETECTED)
    
    def update_text_region(self, region_id: str, updated_region: TextRegion) -> None:
        """Update a specific text region."""
        if self.status not in {SessionStatus.DETECTED, SessionStatus.EDITING}:
            raise ValueError(f"Cannot update regions in status: {self.status.value}")
        
        for i, region in enumerate(self.text_regions):
            if region.id == region_id:
                self.text_regions[i] = updated_region
                self.updated_at = datetime.now()
                
                if self.status == SessionStatus.DETECTED:
                    self.transition_to_status(SessionStatus.EDITING)
                return
        
        raise ValueError(f"Text region with ID {region_id} not found")
    
    def remove_text_region(self, region_id: str) -> None:
        """Remove a text region from the session."""
        if self.status not in {SessionStatus.DETECTED, SessionStatus.EDITING}:
            raise ValueError(f"Cannot remove regions in status: {self.status.value}")
        
        original_count = len(self.text_regions)
        self.text_regions = [r for r in self.text_regions if r.id != region_id]
        
        if len(self.text_regions) == original_count:
            raise ValueError(f"Text region with ID {region_id} not found")
        
        self.updated_at = datetime.now()
        
        if self.status == SessionStatus.DETECTED:
            self.transition_to_status(SessionStatus.EDITING)
    
    def get_selected_regions(self) -> List[TextRegion]:
        """Get all currently selected text regions."""
        return [region for region in self.text_regions if region.is_selected]
    
    def get_user_modified_regions(self) -> List[TextRegion]:
        """Get all text regions that have been modified by the user."""
        return [region for region in self.text_regions if region.is_user_modified]
    
    def set_processed_image(self, processed_image: ImageFile) -> None:
        """Set the processed image and transition to completed status."""
        if self.status != SessionStatus.PROCESSING:
            raise ValueError(f"Cannot set processed image in status: {self.status.value}")
        
        self.processed_image = processed_image
        self.transition_to_status(SessionStatus.COMPLETED)
    
    def clear_selections(self) -> None:
        """Clear all text region selections."""
        for region in self.text_regions:
            region.deselect()
        self.updated_at = datetime.now()
    
    def is_ready_for_processing(self) -> bool:
        """Check if the session is ready for text removal processing."""
        return (
            self.status in {SessionStatus.DETECTED, SessionStatus.EDITING, SessionStatus.COMPLETED, SessionStatus.GENERATED} and
            len(self.text_regions) > 0
        )
    
    def is_ready_for_text_detection(self) -> bool:
        """Check if the session is ready for text detection."""
        return self.status == SessionStatus.UPLOADED
    
    def get_processed_regions_for_display(self) -> List[TextRegion]:
        """Get regions for processed image display (user-modified if available, otherwise OCR)."""
        if self.processed_text_regions is not None:
            return self.processed_text_regions
        # Return copies of OCR regions if no processed regions exist yet
        import copy
        return copy.deepcopy(self.text_regions)
    
    def initialize_processed_regions(self, force_reinitialize: bool = False) -> None:
        """Initialize processed_text_regions as copies of OCR regions with preserved classification."""
        if self.processed_text_regions is None or force_reinitialize:
            import copy
            self.processed_text_regions = copy.deepcopy(self.text_regions)
            
            # Prepare regions for processed mode while preserving classification
            for region in self.processed_text_regions:
                if region.edited_text and region.edited_text.strip():
                    # If user edited the text in OCR mode, move edited_text to original_text (as placeholder)
                    # and clear user_input_text so user can fill new text
                    region.original_text = region.edited_text
                    region.user_input_text = ""
                else:
                    # For regular OCR regions, keep original_text as placeholder and clear user_input_text
                    region.user_input_text = ""
                
                # Ensure classification data is preserved
                # If classification data is missing, re-classify based on original_text
                if not hasattr(region, 'text_category') or not region.text_category:
                    if region.original_text:
                        from app.infrastructure.text_classification.japanese_text_classifier import JapaneseTextClassifier
                        JapaneseTextClassifier.add_classification_to_text_region(region)
            
            self.updated_at = datetime.now()
    
    def update_processed_text_region(self, region_id: str, updated_region: TextRegion) -> None:
        """Update a processed text region (for processed image display)."""
        if self.status not in {SessionStatus.COMPLETED, SessionStatus.GENERATED}:
            raise ValueError(f"Cannot update processed regions in status: {self.status.value}")
        
        # Initialize processed regions if not exists
        if self.processed_text_regions is None:
            self.initialize_processed_regions()
        
        for i, region in enumerate(self.processed_text_regions):
            if region.id == region_id:
                self.processed_text_regions[i] = updated_region
                self.updated_at = datetime.now()
                return
        
        raise ValueError(f"Processed text region with ID {region_id} not found")
    
    def get_processing_summary(self) -> dict:
        """Get a summary of the session for processing."""
        return {
            'session_id': self.id,
            'total_regions': len(self.text_regions),
            'user_modified_regions': len(self.get_user_modified_regions()),
            'high_confidence_regions': len([r for r in self.text_regions if r.is_high_confidence()]),
            'average_confidence': sum(r.confidence for r in self.text_regions) / len(self.text_regions) if self.text_regions else 0.0,
            'image_dimensions': self.original_image.dimensions,
            'status': self.status.value
        }