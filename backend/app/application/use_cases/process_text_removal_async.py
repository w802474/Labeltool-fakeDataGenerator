"""Async text removal processing use case with WebSocket progress monitoring."""
import asyncio
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from loguru import logger

from app.domain.entities.label_session import LabelSession
from app.domain.entities.text_region import TextRegion
from app.domain.value_objects.session_status import SessionStatus
from app.infrastructure.clients.iopaint_client import IOPaintClient
from app.infrastructure.storage.file_storage import FileStorageService
from app.websocket.connection_manager import connection_manager
from app.websocket.iopaint_client import iopaint_ws_client


@dataclass
class AsyncTaskInfo:
    """Information about an async processing task."""
    task_id: str
    session_id: str
    status: str
    stage: str
    progress: float
    message: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class ProcessTextRemovalAsyncUseCase:
    """Use case for async text removal processing with real-time progress."""
    
    def __init__(
        self,
        iopaint_client: IOPaintClient,
        file_service: FileStorageService
    ):
        """Initialize async processing use case."""
        self.iopaint_client = iopaint_client
        self.file_service = file_service
        self._active_tasks: Dict[str, AsyncTaskInfo] = {}
        
        logger.info("ProcessTextRemovalAsyncUseCase initialized")
    
    def validate_async_processing_request(
        self,
        session: LabelSession,
        inpainting_method: str = "iopaint"
    ) -> Dict[str, Any]:
        """Validate session is ready for async processing."""
        issues = []
        
        # Check session status
        if session.status not in [SessionStatus.DETECTED, SessionStatus.EDITING, SessionStatus.COMPLETED]:
            issues.append(f"Session status {session.status.value} not ready for processing")
        
        # Check if image exists
        if not session.original_image or not session.original_image.path:
            issues.append("No original image found")
        
        # Check text regions
        if not session.text_regions:
            issues.append("No text regions found for processing")
        
        # Check inpainting method
        supported_methods = ["iopaint", "lama", "ldm", "zits", "mat", "fcf"]
        if inpainting_method not in supported_methods:
            issues.append(f"Unsupported inpainting method: {inpainting_method}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    async def start_async_processing(
        self,
        session: LabelSession,
        regions: Optional[List[TextRegion]] = None,
        inpainting_method: str = "iopaint",
        custom_radius: Optional[int] = None,
        task_id: Optional[str] = None
    ) -> AsyncTaskInfo:
        """Start async text removal processing."""
        # Use provided task_id or generate new one
        task_id = task_id or str(uuid.uuid4())
        
        # Create task info
        task_info = AsyncTaskInfo(
            task_id=task_id,
            session_id=session.id,
            status="pending",
            stage="preparing",
            progress=0.0,
            message="Preparing for text removal processing",
            started_at=datetime.now()
        )
        
        # Store task info
        self._active_tasks[task_id] = task_info
        
        logger.info(f"Starting async processing task {task_id} for session {session.id}")
        
        # Update session status
        session.transition_to_status(SessionStatus.PROCESSING)
        
        # Start processing in background
        asyncio.create_task(self._process_async(
            task_info, session, regions, inpainting_method, custom_radius
        ))
        
        return task_info
    
    async def _process_async(
        self,
        task_info: AsyncTaskInfo,
        session: LabelSession,
        regions: Optional[List[TextRegion]],
        inpainting_method: str,
        custom_radius: Optional[int]
    ):
        """Execute async processing with progress updates."""
        try:
            # Update task status
            task_info.status = "processing"
            task_info.stage = "preparing"
            task_info.progress = 5.0
            task_info.message = "Preparing image and regions for processing"
            
            await self._broadcast_progress_update(task_info)
            
            # Use provided regions or session regions
            regions_to_process = regions if regions else session.text_regions
            
            if not regions_to_process:
                raise ValueError("No regions available for processing")
            
            logger.info(f"Processing {len(regions_to_process)} regions for task {task_info.task_id}")
            
            # Update regions in session if provided
            if regions:
                session.text_regions = regions
            
            # Prepare request for IOPaint service
            request_data = {
                "image_path": session.original_image.path,
                "text_regions": [
                    {
                        "id": region.id,
                        "bounding_box": {
                            "x": region.bounding_box.x,
                            "y": region.bounding_box.y,
                            "width": region.bounding_box.width,
                            "height": region.bounding_box.height
                        },
                        "corners": [{"x": p.x, "y": p.y} for p in region.corners]
                    }
                    for region in regions_to_process
                ],
                "inpainting_method": inpainting_method,
                "custom_radius": custom_radius,
                "task_id": task_info.task_id  # Pass unified task_id to IOPaint
            }
            
            # Update progress
            task_info.stage = "connecting"
            task_info.progress = 10.0
            task_info.message = "Connecting to IOPaint service"
            await self._broadcast_progress_update(task_info)
            
            # Ensure IOPaint WebSocket connection
            if not iopaint_ws_client.is_connected():
                await iopaint_ws_client.connect()
            
            # Subscribe to IOPaint task progress
            await iopaint_ws_client.subscribe_to_task(task_info.task_id)
            
            # Start async processing in IOPaint
            task_info.stage = "processing"
            task_info.progress = 15.0
            task_info.message = "Starting text removal processing"
            await self._broadcast_progress_update(task_info)
            
            # Call IOPaint async API with unified task_id
            response = await self.iopaint_client.inpaint_regions_async(**request_data)
            
            if not response or response.get("status") not in ["pending", "accepted"]:
                raise Exception(f"IOPaint service rejected request: {response}")
            
            # IOPaint should now use our unified task_id
            returned_task_id = response.get("task_id")
            logger.info(f"IOPaint processing started - Unified task_id: {task_info.task_id}, Returned: {returned_task_id}")
            
            # Subscribe to task progress using unified task_id
            await iopaint_ws_client.subscribe_to_task(task_info.task_id)
            
            # Note: Progress updates will come through WebSocket connection
            # The task will be marked as completed when IOPaint sends completion callback
            logger.info(f"Async processing initiated for task {task_info.task_id}, monitoring via WebSocket")
            
        except Exception as e:
            # Handle error
            task_info.status = "failed"
            task_info.stage = "error"
            task_info.progress = 0.0
            task_info.message = f"Processing failed: {str(e)}"
            task_info.error_message = str(e)
            task_info.completed_at = datetime.now()
            
            logger.error(f"Async processing failed for task {task_info.task_id}: {e}")
            
            # Update session status
            session.transition_to_status(SessionStatus.ERROR)
            session.error_message = str(e)
            
            await self._broadcast_progress_update(task_info)
    
    async def _wait_for_completion(self, task_info: AsyncTaskInfo, timeout: int = 300):
        """Wait for processing completion with timeout."""
        start_time = datetime.now()
        
        while True:
            # Check if task completed
            if task_info.status in ["completed", "failed", "cancelled"]:
                break
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                task_info.status = "failed"
                task_info.error_message = f"Processing timeout after {timeout} seconds"
                task_info.completed_at = datetime.now()
                await self._broadcast_progress_update(task_info)
                break
            
            # Wait before checking again
            await asyncio.sleep(1)
    
    async def _broadcast_progress_update(self, task_info: AsyncTaskInfo):
        """Broadcast progress update to frontend clients."""
        progress_message = {
            "type": "progress_update",
            "task_id": task_info.task_id,
            "session_id": task_info.session_id,
            "status": task_info.status,
            "stage": task_info.stage,
            "progress": task_info.progress,
            "message": task_info.message,
            "timestamp": datetime.now().isoformat()
        }
        
        if task_info.error_message:
            progress_message["error_message"] = task_info.error_message
        
        if task_info.result:
            progress_message["result"] = task_info.result
        
        # Broadcast to all clients subscribed to this task
        await connection_manager.broadcast_to_task(task_info.task_id, progress_message)
        
        logger.debug(f"Broadcasted progress update for task {task_info.task_id}: {task_info.progress}%")
    
    def get_task_status(self, task_id: str) -> Optional[AsyncTaskInfo]:
        """Get current status of a processing task."""
        return self._active_tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a processing task."""
        if task_id not in self._active_tasks:
            return False
        
        task_info = self._active_tasks[task_id]
        
        if task_info.status in ["completed", "failed", "cancelled"]:
            return False
        
        try:
            # Cancel task in IOPaint service
            cancel_response = await self.iopaint_client.cancel_task(task_id)
            
            # Update task status
            task_info.status = "cancelled"
            task_info.stage = "cancelled"
            task_info.message = "Processing cancelled by user"
            task_info.completed_at = datetime.now()
            
            await self._broadcast_progress_update(task_info)
            
            logger.info(f"Task {task_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks."""
        now = datetime.now()
        to_remove = []
        
        for task_id, task_info in self._active_tasks.items():
            if task_info.status in ["completed", "failed", "cancelled"] and task_info.completed_at:
                age_hours = (now - task_info.completed_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del self._active_tasks[task_id]
            logger.debug(f"Cleaned up old task: {task_id}")
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old tasks")
    
    def get_active_tasks(self) -> List[AsyncTaskInfo]:
        """Get list of all active tasks."""
        return list(self._active_tasks.values())
    
    async def estimate_processing_time(self, session: LabelSession) -> Dict[str, Any]:
        """Estimate processing time for async processing."""
        region_count = len(session.text_regions) if session.text_regions else 0
        
        # Base time estimates (in seconds)
        base_time = 10  # Base overhead
        per_region_time = 5  # Time per region
        
        estimated_seconds = base_time + (region_count * per_region_time)
        
        # Complexity assessment
        complexity = "low"
        if region_count > 10:
            complexity = "medium"
            estimated_seconds *= 1.5
        if region_count > 20:
            complexity = "high"
            estimated_seconds *= 2.0
        
        return {
            "estimated_seconds": int(estimated_seconds),
            "complexity": complexity,
            "region_count": region_count,
            "details": {
                "base_time": base_time,
                "per_region_time": per_region_time,
                "complexity_multiplier": estimated_seconds / (base_time + region_count * per_region_time)
            }
        }