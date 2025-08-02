"""WebSocket routes for backend service."""
from fastapi import APIRouter, WebSocket
from loguru import logger

from app.websocket.message_router import handle_websocket_connection

router = APIRouter(prefix="/api/v1")


@router.websocket("/ws/progress/{task_id}")
async def websocket_task_progress(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for task-specific progress updates.
    
    Args:
        websocket: WebSocket connection
        task_id: Task ID to subscribe to
    """
    logger.info(f"WebSocket connection request for task: {task_id}")
    await handle_websocket_connection(websocket, task_id)


@router.websocket("/ws/progress")
async def websocket_general_progress(websocket: WebSocket):
    """
    WebSocket endpoint for general progress updates.
    
    Args:
        websocket: WebSocket connection
    """
    logger.info("WebSocket connection request for general progress")
    await handle_websocket_connection(websocket)