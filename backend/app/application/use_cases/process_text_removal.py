"""Use case for processing text removal from images."""
from typing import Optional
from loguru import logger

from app.domain.entities.label_session import LabelSession
from app.domain.value_objects.session_status import SessionStatus
from app.application.interfaces.image_service import ImageServicePort, InpaintingServicePort


class ProcessTextRemovalUseCase:
    """Use case for text removal processing."""
    
    def __init__(
        self,
        inpainting_service: InpaintingServicePort,
        image_service: ImageServicePort
    ):
        """
        Initialize the text removal use case.
        
        Args:
            inpainting_service: Service for image inpainting
            image_service: Service for image file operations
        """
        self.inpainting_service = inpainting_service
        self.image_service = image_service
    
    async def execute(
        self, 
        session: LabelSession,
        inpainting_method: str = "telea",
        custom_radius: Optional[int] = None
    ) -> LabelSession:
        """
        Execute text removal processing workflow.
        
        Args:
            session: LabelSession to process
            inpainting_method: Method to use for inpainting ('telea' or 'ns')
            custom_radius: Custom inpainting radius (overrides automatic calculation)
            
        Returns:
            Updated LabelSession with processed image
            
        Raises:
            ValueError: If session is not ready for processing
        """
        if not session.is_ready_for_processing():
            raise ValueError(f"Session {session.id} is not ready for processing (status: {session.status.value})")
        
        logger.info(f"Starting text removal processing for session {session.id}")
        logger.info(f"Processing {len(session.text_regions)} text regions")
        
        try:
            # If session is completed/generated but has user-modified regions, it means user made changes
            # after completion, so we should allow reprocessing
            if session.status in {SessionStatus.COMPLETED, SessionStatus.GENERATED}:
                user_modified_count = sum(1 for r in session.text_regions if r.is_user_modified)
                logger.info(f"Session is {session.status.value} but found {user_modified_count} user-modified regions - allowing reprocessing")
            
            # CRITICAL: Initialize processed_text_regions before processing
            # For reprocessing, force reinitialize to use current OCR regions
            is_reprocessing = session.processed_text_regions is not None
            session.initialize_processed_regions(force_reinitialize=is_reprocessing)
            
            if is_reprocessing:
                logger.info(f"REPROCESSING: Reinitialized {len(session.processed_text_regions)} processed text regions from current OCR regions")
            else:
                logger.info(f"FIRST PROCESSING: Initialized {len(session.processed_text_regions)} processed text regions as independent copy")
            
            # Transition to processing status
            session.transition_to_status(SessionStatus.PROCESSING)
            
            # Validate regions before processing
            validation_result = self.inpainting_service.validate_regions_for_inpainting(
                session.text_regions
            )
            
            if not validation_result['valid']:
                raise ValueError(f"Regions validation failed: {validation_result['issues']}")
            
            # Log processing complexity
            complexity_info = self._calculate_processing_complexity(session)
            logger.info(f"Processing complexity: {complexity_info}")
            
            # Get regions to process (apply quality filters)
            regions_to_process = self._optimize_regions_for_processing(session.text_regions)
            
            if not regions_to_process:
                raise ValueError("No valid regions to process after filtering")
            
            logger.info(f"Processing {len(regions_to_process)} regions after filtering")
            logger.info(f"Sending {len(regions_to_process)} regions to inpainting service")
            
            # Process text removal using inpainting service
            processed_image_path = await self.inpainting_service.remove_text_regions(
                session.original_image.path,
                regions_to_process,
                output_dir="processed"
            )
            
            # Create metadata for processed image
            processed_image = await self.image_service.create_processed_image_metadata(
                processed_image_path,
                session.original_image
            )
            
            # Update session with processed image
            session.set_processed_image(processed_image)
            
            # Log completion
            processing_summary = session.get_processing_summary()
            logger.info(f"Text removal completed successfully: {processing_summary}")
            
            return session
            
        except Exception as e:
            logger.error(f"Text removal processing failed for session {session.id}: {e}")
            session.transition_to_status(
                SessionStatus.ERROR,
                f"Text removal processing failed: {str(e)}"
            )
            raise
    
    async def estimate_processing_time(self, session: LabelSession) -> dict:
        """
        Estimate processing time for the session.
        
        Args:
            session: LabelSession to analyze
            
        Returns:
            Dictionary with time estimates and complexity info
        """
        if not session.text_regions:
            return {
                'estimated_seconds': 0,
                'complexity': 'none',
                'region_count': 0,
                'recommendations': []
            }
        
        # Get complexity analysis
        complexity_info = self._calculate_processing_complexity(session)
        
        # Base time estimates (in seconds)
        base_times = {
            'low': 5,
            'medium': 15,
            'high': 30
        }
        
        base_time = base_times.get(complexity_info['complexity'], 20)
        
        # Factor in region count
        region_factor = len(session.text_regions) * 2
        
        # Factor in image size
        image_area = session.original_image.dimensions.width * session.original_image.dimensions.height
        size_factor = max(0, (image_area - 1_000_000) // 1_000_000)  # Additional seconds per megapixel
        
        total_estimate = base_time + region_factor + size_factor
        
        # Cap at reasonable maximum (5 minutes)
        total_estimate = min(total_estimate, 300)
        
        recommendations = []
        if complexity_info['complexity'] == 'high':
            recommendations.append("Consider using 'ns' method for better quality")
            recommendations.append("Large or complex regions may take longer to process")
        
        if len(session.text_regions) > 20:
            recommendations.append("Many regions detected - consider removing unnecessary ones")
        
        return {
            'estimated_seconds': total_estimate,
            'complexity': complexity_info['complexity'],
            'region_count': len(session.text_regions),
            'image_size_mp': round(image_area / 1_000_000, 1),
            'recommendations': recommendations,
            'details': complexity_info
        }
    
    def _optimize_regions_for_processing(self, regions):
        """Apply quality filters to regions before processing."""
        from app.domain.entities.text_region import TextRegion
        
        optimized_regions = []
        
        for region in regions:
            # Always include user-modified regions (they're likely more accurate)
            if region.is_user_modified:
                optimized_regions.append(region)
                continue
            
            # Include high-confidence automatic detections
            if region.is_high_confidence(threshold=0.7):
                optimized_regions.append(region)
                continue
            
            # For medium confidence, check region size
            if region.confidence >= 0.5 and region.get_area() > 200:
                optimized_regions.append(region)
                continue
            
            # For low confidence, only include if reasonably sized and not tiny
            if region.confidence >= 0.3 and 500 <= region.get_area() <= 50000:
                optimized_regions.append(region)
        
        logger.info(f"Filtered {len(regions)} regions to {len(optimized_regions)} for processing")
        return optimized_regions
    
    def _calculate_processing_complexity(self, session: LabelSession) -> dict:
        """Calculate processing complexity metrics."""
        regions = session.text_regions
        
        if not regions:
            return {'complexity': 'none', 'factors': {}}
        
        # Calculate various complexity factors
        total_area = sum(region.get_area() for region in regions)
        image_area = session.original_image.dimensions.width * session.original_image.dimensions.height
        coverage_ratio = total_area / image_area if image_area > 0 else 0
        
        avg_confidence = sum(r.confidence for r in regions) / len(regions)
        user_modified_count = len([r for r in regions if r.is_user_modified])
        low_confidence_count = len([r for r in regions if r.confidence < 0.6])
        
        # Calculate region size distribution
        small_regions = len([r for r in regions if r.get_area() < 500])
        large_regions = len([r for r in regions if r.get_area() > 5000])
        
        # Determine complexity level based on multiple factors
        complexity_score = 0
        
        # Coverage ratio impact
        if coverage_ratio > 0.3:
            complexity_score += 3
        elif coverage_ratio > 0.15:
            complexity_score += 2
        elif coverage_ratio > 0.05:
            complexity_score += 1
        
        # Confidence impact
        if avg_confidence < 0.6:
            complexity_score += 2
        elif avg_confidence < 0.8:
            complexity_score += 1
        
        # Region count impact
        if len(regions) > 20:
            complexity_score += 2
        elif len(regions) > 10:
            complexity_score += 1
        
        # Low confidence regions impact
        if low_confidence_count > len(regions) * 0.4:
            complexity_score += 2
        
        # Large regions impact (harder to inpaint well)
        if large_regions > 3:
            complexity_score += 1
        
        # Determine final complexity
        if complexity_score >= 6:
            complexity = 'high'
        elif complexity_score >= 3:
            complexity = 'medium'
        else:
            complexity = 'low'
        
        return {
            'complexity': complexity,
            'score': complexity_score,
            'factors': {
                'coverage_ratio': round(coverage_ratio, 3),
                'avg_confidence': round(avg_confidence, 3),
                'region_count': len(regions),
                'user_modified_count': user_modified_count,
                'low_confidence_count': low_confidence_count,
                'small_regions': small_regions,
                'large_regions': large_regions,
                'total_area': int(total_area),
                'image_area': int(image_area)
            }
        }
    
    def validate_processing_request(
        self, 
        session: LabelSession,
        inpainting_method: str = "telea"
    ) -> dict:
        """
        Validate that processing can proceed.
        
        Args:
            session: LabelSession to validate
            inpainting_method: Requested inpainting method
            
        Returns:
            Validation result dictionary
        """
        issues = []
        warnings = []
        
        # Check session status
        if not session.is_ready_for_processing():
            issues.append(f"Session not ready for processing (status: {session.status.value})")
        
        # Check regions
        if not session.text_regions:
            issues.append("No text regions to process")
        
        # Check inpainting method
        if inpainting_method not in ['telea', 'ns']:
            issues.append(f"Invalid inpainting method: {inpainting_method}")
        
        # Check image file exists
        import os
        if not os.path.exists(session.original_image.path):
            issues.append("Original image file not found")
        
        # Validate regions for inpainting
        if session.text_regions:
            region_validation = self.inpainting_service.validate_regions_for_inpainting(
                session.text_regions
            )
            if not region_validation['valid']:
                issues.extend(region_validation['issues'])
            
            if region_validation.get('recommendations'):
                warnings.extend(region_validation['recommendations'])
        
        # Check for processing complexity warnings
        complexity_info = self._calculate_processing_complexity(session)
        if complexity_info['complexity'] == 'high':
            warnings.append("High complexity processing - may take longer than usual")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'complexity': complexity_info,
            'estimated_time': self._estimate_time_from_complexity(complexity_info)
        }
    
    def _estimate_time_from_complexity(self, complexity_info: dict) -> int:
        """Estimate processing time from complexity info."""
        base_times = {'low': 10, 'medium': 25, 'high': 45}
        return base_times.get(complexity_info['complexity'], 30)