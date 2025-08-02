"""Use case for updating text regions based on user modifications."""
from typing import List, Optional
from loguru import logger

from app.domain.entities.label_session import LabelSession
from app.domain.entities.text_region import TextRegion
from app.domain.value_objects.rectangle import Rectangle
from app.domain.value_objects.point import Point
from app.domain.value_objects.session_status import SessionStatus
from app.application.dto.session_dto import TextRegionDTO
from app.infrastructure.storage.file_storage import FileStorageService


class UpdateTextRegionsUseCase:
    """Use case for manual adjustment of text regions."""
    
    def __init__(self, file_storage_service: Optional[FileStorageService] = None):
        """Initialize the update text regions use case."""
        self.file_storage_service = file_storage_service or FileStorageService()
    
    async def execute(
        self, 
        session: LabelSession, 
        updated_regions: List[TextRegionDTO],
        update_mode: str = "auto",  # "ocr", "processed", or "auto"
        export_csv: bool = True  # Whether to export regions to CSV file
    ) -> LabelSession:
        """
        Execute text region updates.
        
        Args:
            session: LabelSession to update
            updated_regions: List of updated text region DTOs
            update_mode: Which regions to update ("ocr", "processed", or "auto")
            export_csv: Whether to export regions to CSV file for persistence
            
        Returns:
            Updated LabelSession
            
        Raises:
            ValueError: If session state or region data is invalid
        """
        if session.status not in {SessionStatus.DETECTED, SessionStatus.EDITING, SessionStatus.COMPLETED, SessionStatus.GENERATED}:
            raise ValueError(f"Cannot update regions in status: {session.status.value}")
        
        logger.info(f"Updating {len(updated_regions)} text regions for session {session.id} (mode: {update_mode})")
        
        try:
            # Validate input regions
            validation_result = self._validate_regions(updated_regions, session)
            if not validation_result['valid']:
                raise ValueError(f"Invalid regions: {validation_result['issues']}")
            
            # Convert DTOs to domain entities
            new_regions = []
            for region_dto in updated_regions:
                domain_region = self._convert_dto_to_domain(region_dto)
                new_regions.append(domain_region)
            
            # Determine which regions to update based on mode and session status
            if update_mode == "auto":
                # Auto-detect: if session is completed/generated, prefer updating processed regions
                if session.status in {SessionStatus.COMPLETED, SessionStatus.GENERATED}:
                    update_mode = "processed"
                else:
                    update_mode = "ocr"
            
            if update_mode == "processed":
                # Update processed regions
                logger.info("Updating processed text regions")
                
                
                # Initialize processed regions if they don't exist
                if session.processed_text_regions is None:
                    session.initialize_processed_regions()
                
                # Update processed regions
                session.processed_text_regions = new_regions
                
                # Don't change status when updating processed regions
                logger.info("Processed regions updated without status change")
                
            else:  # update_mode == "ocr"
                # Update OCR regions
                logger.info("Updating OCR text regions")
                
                # Check for significant changes
                changes_detected = self._detect_changes(session.text_regions, new_regions)
                
                # Update session with new regions
                session.text_regions = new_regions
                
                # Transition to editing status if changes were made
                if changes_detected and session.status == SessionStatus.DETECTED:
                    session.transition_to_status(SessionStatus.EDITING)
            
            # Export regions to CSV file for persistence (if requested)
            if export_csv:
                try:
                    await self._export_regions_to_csv(session, new_regions)
                except Exception as csv_error:
                    logger.warning(f"Failed to export regions to CSV: {csv_error}")
                    # Don't fail the main operation if CSV export fails
            
            logger.info(f"Successfully updated text regions for session {session.id}")
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to update text regions for session {session.id}: {e}")
            session.transition_to_status(
                SessionStatus.ERROR,
                f"Failed to update text regions: {str(e)}"
            )
            raise
    
    async def update_single_region(
        self, 
        session: LabelSession, 
        region_id: str, 
        updated_region: TextRegionDTO
    ) -> LabelSession:
        """
        Update a single text region.
        
        Args:
            session: LabelSession to update
            region_id: ID of region to update
            updated_region: Updated region data
            
        Returns:
            Updated LabelSession
            
        Raises:
            ValueError: If region is not found or data is invalid
        """
        if session.status not in {SessionStatus.DETECTED, SessionStatus.EDITING}:
            raise ValueError(f"Cannot update region in status: {session.status.value}")
        
        logger.info(f"Updating single text region {region_id} for session {session.id}")
        
        try:
            # Find the region to update
            region_index = None
            for i, region in enumerate(session.text_regions):
                if region.id == region_id:
                    region_index = i
                    break
            
            if region_index is None:
                raise ValueError(f"Text region {region_id} not found")
            
            # Validate the updated region
            validation_result = self._validate_single_region(updated_region, session)
            if not validation_result['valid']:
                raise ValueError(f"Invalid region data: {validation_result['issues']}")
            
            # Convert DTO to domain entity
            domain_region = self._convert_dto_to_domain(updated_region)
            
            # Update the region
            old_region = session.text_regions[region_index]
            session.text_regions[region_index] = domain_region
            
            # Check if this was a significant change
            is_significant_change = self._is_significant_region_change(old_region, domain_region)
            
            # Transition to editing status if significant change
            if is_significant_change and session.status == SessionStatus.DETECTED:
                session.transition_to_status(SessionStatus.EDITING)
            
            logger.info(f"Successfully updated region {region_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to update region {region_id}: {e}")
            raise
    
    async def remove_region(
        self, 
        session: LabelSession, 
        region_id: str
    ) -> LabelSession:
        """
        Remove a text region from the session.
        
        Args:
            session: LabelSession to update
            region_id: ID of region to remove
            
        Returns:
            Updated LabelSession
            
        Raises:
            ValueError: If region is not found
        """
        logger.info(f"Removing text region {region_id} from session {session.id}")
        
        try:
            session.remove_text_region(region_id)
            logger.info(f"Successfully removed region {region_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to remove region {region_id}: {e}")
            raise
    
    def _convert_dto_to_domain(self, region_dto: TextRegionDTO) -> TextRegion:
        """Convert TextRegionDTO to domain TextRegion entity."""
        # Convert rectangle
        bounding_box = Rectangle(
            x=region_dto.bounding_box.x,
            y=region_dto.bounding_box.y,
            width=region_dto.bounding_box.width,
            height=region_dto.bounding_box.height
        )
        
        # Convert corners
        corners = [
            Point(x=corner.x, y=corner.y) 
            for corner in region_dto.corners
        ]
        
        # Convert original_box_size if it exists
        original_box_size = None
        if region_dto.original_box_size:
            original_box_size = Rectangle(
                x=region_dto.original_box_size.x,
                y=region_dto.original_box_size.y,
                width=region_dto.original_box_size.width,
                height=region_dto.original_box_size.height
            )
        
        # Create TextRegion
        text_region = TextRegion(
            id=region_dto.id,
            bounding_box=bounding_box,
            confidence=region_dto.confidence,
            corners=corners,
            is_selected=region_dto.is_selected,
            is_user_modified=region_dto.is_user_modified,
            original_text=region_dto.original_text,
            edited_text=region_dto.edited_text,
            user_input_text=region_dto.user_input_text,
            font_properties=region_dto.font_properties,
            original_box_size=original_box_size,
            is_size_modified=region_dto.is_size_modified,
            text_category=getattr(region_dto, 'text_category', None),
            category_config=getattr(region_dto, 'category_config', None)
        )
        
        # If classification data is missing but we have text, re-classify
        if not text_region.text_category and text_region.original_text:
            from app.infrastructure.text_classification.japanese_text_classifier import JapaneseTextClassifier
            JapaneseTextClassifier.add_classification_to_text_region(text_region)
        
        return text_region
    
    def _validate_regions(
        self, 
        regions: List[TextRegionDTO], 
        session: LabelSession
    ) -> dict:
        """Validate a list of text regions."""
        issues = []
        
        if not regions:
            return {'valid': True, 'issues': []}
        
        # Check for duplicate IDs
        region_ids = [region.id for region in regions]
        if len(region_ids) != len(set(region_ids)):
            issues.append("Duplicate region IDs found")
        
        # Validate each region
        for i, region in enumerate(regions):
            region_validation = self._validate_single_region(region, session)
            if not region_validation['valid']:
                issues.extend([f"Region {i}: {issue}" for issue in region_validation['issues']])
        
        # Note: Overlapping regions are normal for OCR results and text generation
        # No overlap validation needed as users may intentionally create overlapping regions
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'region_count': len(regions)
        }
    
    def _validate_single_region(
        self, 
        region: TextRegionDTO, 
        session: LabelSession
    ) -> dict:
        """Validate a single text region."""
        issues = []
        
        # Check bounding box validity
        bbox = region.bounding_box
        if bbox.width <= 0 or bbox.height <= 0:
            issues.append("Invalid bounding box dimensions")
        
        # Check if region is within image bounds
        image_dims = session.original_image.dimensions
        if (bbox.x < 0 or bbox.y < 0 or 
            bbox.x + bbox.width > image_dims.width or 
            bbox.y + bbox.height > image_dims.height):
            issues.append("Region extends beyond image boundaries")
        
        # Check confidence score
        if not 0.0 <= region.confidence <= 1.0:
            issues.append(f"Invalid confidence score: {region.confidence}")
        
        # Check corners count
        if len(region.corners) != 4:
            issues.append(f"Expected 4 corners, got {len(region.corners)}")
        
        # Check region size (too small might be noise)
        area = bbox.width * bbox.height
        if area < 10:
            issues.append("Region is too small (possible noise)")
        elif area > image_dims.width * image_dims.height * 0.8:
            issues.append("Region is suspiciously large")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'area': area
        }
    
    def _detect_changes(
        self, 
        old_regions: List[TextRegion], 
        new_regions: List[TextRegion]
    ) -> bool:
        """Detect if there are significant changes between old and new regions."""
        if len(old_regions) != len(new_regions):
            return True
        
        # Create lookup maps by ID
        old_map = {region.id: region for region in old_regions}
        new_map = {region.id: region for region in new_regions}
        
        # Check for added/removed regions
        if set(old_map.keys()) != set(new_map.keys()):
            return True
        
        # Check for modifications
        for region_id in old_map.keys():
            if self._is_significant_region_change(old_map[region_id], new_map[region_id]):
                return True
        
        return False
    
    def _is_significant_region_change(
        self, 
        old_region: TextRegion, 
        new_region: TextRegion
    ) -> bool:
        """Check if a region change is significant enough to mark as user-modified."""
        # Check bounding box changes
        old_bbox = old_region.bounding_box
        new_bbox = new_region.bounding_box
        
        # Calculate relative changes
        x_change = abs(old_bbox.x - new_bbox.x) / max(old_bbox.width, 1)
        y_change = abs(old_bbox.y - new_bbox.y) / max(old_bbox.height, 1)
        width_change = abs(old_bbox.width - new_bbox.width) / max(old_bbox.width, 1)
        height_change = abs(old_bbox.height - new_bbox.height) / max(old_bbox.height, 1)
        
        # Threshold for significant change (5% of region size)
        threshold = 0.05
        
        return (x_change > threshold or y_change > threshold or 
                width_change > threshold or height_change > threshold or
                old_region.is_selected != new_region.is_selected)
    
    async def _export_regions_to_csv(self, session: LabelSession, regions: List[TextRegion]) -> str:
        """
        Export text regions to CSV file for persistence.
        
        Args:
            session: LabelSession containing the regions
            regions: List of TextRegion entities to export
            
        Returns:
            Path to the saved CSV file
        """
        # Convert TextRegion entities to dictionary format for CSV export
        regions_data = []
        for region in regions:
            region_dict = {
                'id': region.id,
                'bounding_box': {
                    'x': region.bounding_box.x,
                    'y': region.bounding_box.y,
                    'width': region.bounding_box.width,
                    'height': region.bounding_box.height
                },
                'confidence': region.confidence,
                'original_text': region.original_text or '',
                'is_user_modified': region.is_user_modified,
                'is_selected': region.is_selected
            }
            regions_data.append(region_dict)
        
        # Save to CSV file using image ID to match with uploaded file naming
        csv_path = await self.file_storage_service.save_text_regions_csv(
            image_id=session.original_image.id,
            regions=regions_data,
            image_filename=session.original_image.filename
        )
        
        logger.info(f"Exported {len(regions)} text regions to CSV: {csv_path}")
        return csv_path