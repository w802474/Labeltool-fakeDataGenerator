"""Progress tracking utility for IOPaint processing operations."""
import asyncio
from typing import Optional, Callable, Any
from loguru import logger

from app.websocket.task_manager import task_manager, ProcessingStage


class ProgressTracker:
    """Utility class for tracking and reporting progress during IOPaint processing."""
    
    def __init__(self, task_id: str, total_regions: int = 0):
        """
        Initialize progress tracker.
        
        Args:
            task_id: Task ID to track
            total_regions: Total number of regions to process
        """
        self.task_id = task_id
        self.total_regions = total_regions
        self.current_stage = ProcessingStage.PREPARING
        self.current_region = 0
        
        logger.debug(f"Progress tracker initialized for task {task_id} with {total_regions} regions")
    
    async def start_stage(self, stage: ProcessingStage, message: Optional[str] = None):
        """
        Start a new processing stage.
        
        Args:
            stage: Processing stage
            message: Optional progress message
        """
        self.current_stage = stage
        
        if not message:
            stage_messages = {
                ProcessingStage.PREPARING: "Preparing image and regions...",
                ProcessingStage.MASKING: "Generating masks from regions...",
                ProcessingStage.INPAINTING: "Performing AI inpainting...",
                ProcessingStage.FINALIZING: "Finalizing result..."
            }
            message = stage_messages.get(stage, f"Processing {stage.value}...")
        
        await task_manager.update_progress(
            self.task_id,
            stage=stage,
            stage_progress=0.0,
            message=message
        )
        
        logger.debug(f"Task {self.task_id}: Started stage {stage.value}")
    
    async def update_stage_progress(self, progress: float, message: Optional[str] = None):
        """
        Update progress within current stage.
        
        Args:
            progress: Progress within stage (0-100)
            message: Optional progress message
        """
        await task_manager.update_progress(
            self.task_id,
            stage=self.current_stage,
            stage_progress=progress,
            current_region=self.current_region,
            message=message
        )
    
    async def advance_region(self, region_index: int, region_progress: float = 0.0, message: Optional[str] = None):
        """
        Advance to processing a specific region.
        
        Args:
            region_index: Index of current region (1-based)
            region_progress: Progress within this region (0-100)
            message: Optional progress message
        """
        self.current_region = region_index
        
        if not message and self.total_regions > 0:
            message = f"Processing region {region_index} of {self.total_regions}..."
        
        await task_manager.update_progress(
            self.task_id,
            stage=self.current_stage,
            stage_progress=region_progress,
            current_region=region_index,
            message=message
        )
    
    async def complete_stage(self, message: Optional[str] = None):
        """
        Complete current stage.
        
        Args:
            message: Optional completion message
        """
        if not message:
            message = f"Completed {self.current_stage.value}"
        
        await task_manager.update_progress(
            self.task_id,
            stage=self.current_stage,
            stage_progress=100.0,
            message=message
        )
        
        logger.debug(f"Task {self.task_id}: Completed stage {self.current_stage.value}")
    
    async def prepare_image(self, progress: float = 0.0):
        """Report image preparation progress."""
        await self.start_stage(ProcessingStage.PREPARING)
        await self.update_stage_progress(progress, "Loading and validating image...")
    
    async def prepare_regions(self, progress: float = 50.0):
        """Report region preparation progress."""
        await self.update_stage_progress(progress, f"Preparing {self.total_regions} text regions...")
    
    async def start_masking(self):
        """Start mask generation stage."""
        await self.complete_stage("Image preparation complete")
        await self.start_stage(ProcessingStage.MASKING, "Generating inpainting masks...")
    
    async def update_masking_progress(self, progress: float):
        """Update mask generation progress."""
        await self.update_stage_progress(progress, "Creating masks from text regions...")
    
    async def start_inpainting(self):
        """Start AI inpainting stage."""
        await self.complete_stage("Mask generation complete")
        await self.start_stage(ProcessingStage.INPAINTING, "AI inpainting in progress...")
    
    async def update_inpainting_progress(self, region_index: int, region_progress: float):
        """
        Update inpainting progress (simplified - just pass data to task_manager).
        
        Args:
            region_index: Current region index (1-based)
            region_progress: Progress within current region (0-100)
        """
        # Update current region info for task_manager calculation
        self.current_region = max(0, int(region_index))
        
        # Ensure region_progress is a valid float in range [0, 100]
        try:
            safe_progress = float(region_progress or 0.0)
            safe_progress = max(0.0, min(100.0, safe_progress))
        except (ValueError, TypeError):
            safe_progress = 0.0
        
        message = "AI inpainting in progress..."
        await self.update_stage_progress(safe_progress, message)
    
    async def start_finalizing(self):
        """Start finalization stage."""
        await self.complete_stage("AI inpainting complete")
        await self.start_stage(ProcessingStage.FINALIZING, "Finalizing processed image...")
    
    async def update_finalizing_progress(self, progress: float, message: Optional[str] = None):
        """Update finalization progress."""
        if not message:
            message = "Saving processed image..."
        await self.update_stage_progress(progress, message)
    
    async def complete(self, result_path: Optional[str] = None):
        """
        Complete the entire processing task.
        
        Args:
            result_path: Path to result file
        """
        await self.complete_stage("Processing complete")
        await task_manager.complete_task(self.task_id, result_path)
        
        logger.info(f"Task {self.task_id}: Processing completed successfully")
    
    async def fail(self, error_message: str):
        """
        Mark task as failed.
        
        Args:
            error_message: Error description
        """
        await task_manager.fail_task(self.task_id, error_message)
        
        logger.error(f"Task {self.task_id}: Processing failed - {error_message}")
    
    def create_callback(self, stage: ProcessingStage, max_progress: float = 100.0) -> Callable[[float], Any]:
        """
        Create a progress callback function for external libraries.
        
        Args:
            stage: Processing stage this callback is for
            max_progress: Maximum progress value this callback will receive
            
        Returns:
            Async callback function
        """
        async def progress_callback(current_progress: float):
            """Progress callback that normalizes and reports progress."""
            normalized_progress = (current_progress / max_progress) * 100.0
            await self.update_stage_progress(normalized_progress)
        
        return progress_callback
    
    def create_region_callback(self, region_index: int, max_progress: float = 100.0) -> Callable[[float], Any]:
        """
        Create a progress callback for a specific region.
        
        Args:
            region_index: Index of the region (1-based)
            max_progress: Maximum progress value this callback will receive
            
        Returns:
            Async callback function
        """
        async def region_progress_callback(current_progress: float):
            """Region-specific progress callback."""
            normalized_progress = (current_progress / max_progress) * 100.0
            await self.update_inpainting_progress(region_index, normalized_progress)
        
        return region_progress_callback