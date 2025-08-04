"""Task management for tracking IOPaint processing tasks and their progress."""
import uuid
import asyncio
from typing import Dict, Optional, Any, Callable, Awaitable
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
from loguru import logger

from app.websocket.manager import websocket_manager


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    PREPARING = "preparing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class ProcessingStage(Enum):
    """Processing stage enumeration."""
    PREPARING = "preparing"
    MASKING = "masking"
    INPAINTING = "inpainting"
    FINALIZING = "finalizing"


@dataclass
class TaskInfo:
    """Information about a processing task."""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    stage: ProcessingStage = ProcessingStage.PREPARING
    overall_progress: float = 0.0
    stage_progress: float = 0.0
    current_region: int = 0
    total_regions: int = 0
    message: str = "Task created"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if not self.started_at:
            return 0.0
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()
    
    @property
    def estimated_remaining(self) -> Optional[float]:
        """Estimate remaining time based on current progress."""
        try:
            # Check for valid progress value
            if not self.overall_progress or self.overall_progress <= 0 or self.overall_progress != self.overall_progress:
                return None
            
            elapsed = self.elapsed_time
            if elapsed <= 0:
                return None
            
            # Calculate estimated total time based on current progress (safe division)
            progress_ratio = max(0.01, min(1.0, self.overall_progress / 100.0))  # Prevent division by zero
            estimated_total = elapsed / progress_ratio
            remaining = estimated_total - elapsed
            
            # Return safe value
            result = max(0, remaining)
            return result if result == result else None  # NaN check
            
        except (ValueError, ZeroDivisionError, TypeError):
            return None


class TaskManager:
    """Manages IOPaint processing tasks and their progress."""
    
    def __init__(self):
        """Initialize task manager."""
        self.tasks: Dict[str, TaskInfo] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Stage progress weights (percentage of total progress)
        self.stage_weights = {
            ProcessingStage.PREPARING: (0, 5),
            ProcessingStage.MASKING: (5, 15),
            ProcessingStage.INPAINTING: (15, 90),
            ProcessingStage.FINALIZING: (90, 100)
        }
        
        logger.info("Task manager initialized")
    
    def create_task(self, total_regions: int = 0, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new processing task.
        
        Args:
            total_regions: Number of regions to process
            metadata: Additional metadata for the task
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        task_info = TaskInfo(
            task_id=task_id,
            total_regions=total_regions,
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task_info
        
        logger.info(f"Created task {task_id} with {total_regions} regions")
        return task_id
    
    def register_task(
        self,
        task_id: str,
        total_regions: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register an existing task ID with the task manager.
        
        Args:
            task_id: Existing task ID to register
            total_regions: Total number of regions to process
            metadata: Optional metadata for the task
            
        Returns:
            The registered task ID
        """
        task_info = TaskInfo(
            task_id=task_id,
            total_regions=total_regions,
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task_info
        
        logger.info(f"Registered existing task {task_id} with {total_regions} regions")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """
        Get task information.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task information or None if not found
        """
        return self.tasks.get(task_id)
    
    async def start_task(self, task_id: str):
        """
        Mark task as started.
        
        Args:
            task_id: Task ID
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.status = TaskStatus.PREPARING
        task.started_at = datetime.now(timezone.utc)
        task.message = "Task started"
        
        await self._broadcast_progress(task_id)
        logger.info(f"Started task {task_id}")
    
    async def update_progress(
        self,
        task_id: str,
        stage: ProcessingStage,
        stage_progress: float,
        current_region: Optional[int] = None,
        message: Optional[str] = None
    ):
        """
        Update task progress.
        
        Args:
            task_id: Task ID
            stage: Current processing stage
            stage_progress: Progress within current stage (0-100)
            current_region: Current region being processed
            message: Progress message
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        # Update task info
        task.stage = stage
        task.stage_progress = min(100, max(0, stage_progress))
        task.status = TaskStatus.PROCESSING
        
        if current_region is not None:
            task.current_region = current_region
        
        if message:
            task.message = message
        
        # Calculate overall progress
        task.overall_progress = self._calculate_overall_progress(task)
        
        # Broadcast progress update
        await self._broadcast_progress(task_id)
        
        logger.debug(f"Task {task_id}: {task.overall_progress:.1f}% - {task.message}")
    
    async def complete_task(self, task_id: str, result_path: Optional[str] = None):
        """
        Mark task as completed.
        
        Args:
            task_id: Task ID
            result_path: Path to result file
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.status = TaskStatus.COMPLETED
        task.overall_progress = 100.0
        task.stage_progress = 100.0
        task.completed_at = datetime.now(timezone.utc)
        task.message = "Task completed successfully"
        
        if result_path:
            task.metadata["result_path"] = result_path
        
        # Remove from active tasks
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        await self._broadcast_progress(task_id)
        logger.info(f"Completed task {task_id} in {task.elapsed_time:.2f}s")
    
    async def fail_task(self, task_id: str, error_message: str):
        """
        Mark task as failed.
        
        Args:
            task_id: Task ID
            error_message: Error description
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.status = TaskStatus.ERROR
        task.error_message = error_message
        task.completed_at = datetime.now(timezone.utc)
        task.message = f"Task failed: {error_message}"
        
        # Remove from active tasks
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        await self._broadcast_progress(task_id)
        logger.error(f"Failed task {task_id}: {error_message}")
    
    async def cancel_task(self, task_id: str):
        """
        Cancel a running task.
        
        Args:
            task_id: Task ID
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        # Cancel active task if running
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now(timezone.utc)
        task.message = "Task cancelled by user"
        
        await self._broadcast_progress(task_id)
        logger.info(f"Cancelled task {task_id}")
    
    def _calculate_overall_progress(self, task: TaskInfo) -> float:
        """
        Calculate overall progress based on stage and stage progress.
        
        Args:
            task: Task information
            
        Returns:
            Overall progress (0-100), guaranteed to be a valid float
        """
        try:
            stage_start, stage_end = self.stage_weights[task.stage]
            stage_range = max(1, stage_end - stage_start)  # Prevent zero range
            
            # Ensure stage_progress is valid and convert to float
            stage_progress = float(task.stage_progress or 0.0)
            stage_progress = max(0.0, min(100.0, stage_progress))
            
            if task.stage == ProcessingStage.INPAINTING and task.total_regions > 0:
                # For inpainting stage, calculate based on current region and region progress
                if task.current_region > 0:
                    # Calculate progress based on completed regions + current region progress
                    completed_regions = max(0, task.current_region - 1)
                    completed_progress = (completed_regions / task.total_regions) * stage_range
                    current_region_progress = (stage_progress / 100.0) * (stage_range / task.total_regions)
                    overall_progress = stage_start + completed_progress + current_region_progress
                else:
                    # Fallback to simple stage progress
                    overall_progress = stage_start + (stage_progress / 100.0) * stage_range
            else:
                # For other stages, use stage progress directly
                overall_progress = stage_start + (stage_progress / 100.0) * stage_range
            
            # Ensure result is valid float within bounds
            overall_progress = float(overall_progress)
            overall_progress = max(0.0, min(100.0, overall_progress))
            
            # Return safe value (no NaN check needed due to controlled calculation)
            return overall_progress
            
        except (ValueError, ZeroDivisionError, TypeError, AttributeError) as e:
            logger.warning(f"Progress calculation error: {e}, returning 0.0")
            return 0.0
    
    async def _broadcast_progress(self, task_id: str):
        """
        Broadcast progress update to WebSocket clients.
        
        Args:
            task_id: Task ID
        """
        task = self.get_task(task_id)
        if not task:
            return
        
        # Choose message type based on task status
        if task.status == TaskStatus.COMPLETED:
            message = {
                "type": "task_completed",
                "task_id": task_id,
                "session_id": None,  # Will be filled by backend mapping
                "result": {
                    "processed_image_path": task.metadata.get("result_path", ""),
                    "processing_time": round(task.elapsed_time, 2),
                    "regions_processed": task.total_regions
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        elif task.status == TaskStatus.ERROR:
            message = {
                "type": "task_failed",
                "task_id": task_id,
                "session_id": None,  # Will be filled by backend mapping
                "error_message": task.error_message or "Processing failed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        elif task.status == TaskStatus.CANCELLED:
            message = {
                "type": "task_cancelled",
                "task_id": task_id,
                "session_id": None,  # Will be filled by backend mapping
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            # Progress update for ongoing tasks
            # Ensure progress is a clean float value (no NaN check needed since _calculate_overall_progress guarantees valid float)
            progress_value = round(task.overall_progress, 1)
            
            message = {
                "type": "progress_update",
                "task_id": task_id,
                "session_id": None,  # Will be filled by backend mapping
                "status": task.status.value,
                "stage": task.stage.value,
                "progress": progress_value,
                "message": task.message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "current_region": task.current_region,
                "total_regions": task.total_regions,
                "elapsed_time": round(task.elapsed_time, 1),
                "estimated_remaining": round(task.estimated_remaining) if task.estimated_remaining else None
            }
        
        await websocket_manager.broadcast_to_task(task_id, message)
    
    def get_task_stats(self) -> Dict[str, Any]:
        """
        Get task statistics.
        
        Returns:
            Task statistics
        """
        total_tasks = len(self.tasks)
        active_count = len([t for t in self.tasks.values() if t.status in [TaskStatus.PREPARING, TaskStatus.PROCESSING]])
        completed_count = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        error_count = len([t for t in self.tasks.values() if t.status == TaskStatus.ERROR])
        
        return {
            "total_tasks": total_tasks,
            "active_tasks": active_count,
            "completed_tasks": completed_count,
            "error_tasks": error_count,
            "active_task_ids": list(self.active_tasks.keys())
        }
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """
        Clean up old completed/failed tasks.
        
        Args:
            max_age_hours: Maximum age in hours for keeping tasks
        """
        cutoff_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - max_age_hours)
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.ERROR, TaskStatus.CANCELLED] and
                task.completed_at and task.completed_at < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            logger.debug(f"Cleaned up old task {task_id}")
        
        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")


# Global task manager instance
task_manager = TaskManager()