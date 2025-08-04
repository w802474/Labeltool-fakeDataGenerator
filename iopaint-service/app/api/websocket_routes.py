"""WebSocket routes for real-time progress monitoring."""
import json
import asyncio
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from loguru import logger

from app.websocket.manager import websocket_manager
from app.websocket.task_manager import task_manager
from app.models.websocket_schemas import (
    MessageType, 
    SubscribeTaskMessage,
    UnsubscribeTaskMessage,
    GetTaskStatusMessage,
    CancelTaskMessage,
    PingMessage
)


async def websocket_endpoint(websocket: WebSocket, task_id: str = None):
    """
    WebSocket endpoint for real-time progress updates.
    
    Args:
        websocket: WebSocket connection
        task_id: Optional task ID to subscribe to immediately
    """
    await websocket.accept()
    
    try:
        # Register connection
        await websocket_manager.connect(websocket, task_id)
        
        logger.info(f"WebSocket connection established for task: {task_id}")
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await handle_client_message(websocket, message)
                
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received: {e}")
                await send_error(websocket, "Invalid JSON format")
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await send_error(websocket, f"Message handling error: {str(e)}")
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # Unregister connection
        await websocket_manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, message: Dict[str, Any]):
    """
    Handle incoming client messages.
    
    Args:
        websocket: WebSocket connection
        message: Parsed message dictionary
    """
    message_type = message.get("type")
    
    if not message_type:
        await send_error(websocket, "Message type is required")
        return
    
    try:
        if message_type == MessageType.SUBSCRIBE_TASK:
            await handle_subscribe_task(websocket, message)
        
        elif message_type == MessageType.UNSUBSCRIBE_TASK:
            await handle_unsubscribe_task(websocket, message)
        
        elif message_type == MessageType.GET_TASK_STATUS:
            await handle_get_task_status(websocket, message)
        
        elif message_type == MessageType.CANCEL_TASK:
            await handle_cancel_task(websocket, message)
        
        elif message_type == MessageType.PING:
            await handle_ping(websocket, message)
        
        else:
            await send_error(websocket, f"Unknown message type: {message_type}")
    
    except Exception as e:
        logger.error(f"Error handling message type {message_type}: {e}")
        await send_error(websocket, f"Error processing {message_type}: {str(e)}")


async def handle_subscribe_task(websocket: WebSocket, message: Dict[str, Any]):
    """Handle task subscription request."""
    task_id = message.get("task_id")
    if not task_id:
        await send_error(websocket, "task_id is required for subscription")
        return
    
    await websocket_manager.subscribe_to_task(websocket, task_id)
    
    # Send current task status if available
    task = task_manager.get_task(task_id)
    if task:
        status_message = {
            "type": MessageType.PROGRESS_UPDATE,
            "task_id": task_id,
            "status": task.status.value,
            "stage": task.stage.value,
            "progress": task.overall_progress,
            "stage_progress": task.stage_progress,
            "current_region": task.current_region,
            "total_regions": task.total_regions,
            "message": task.message,
            "elapsed_time": task.elapsed_time,
            "estimated_remaining": task.estimated_remaining
        }
        await websocket_manager.send_to_connection(websocket, status_message)


async def handle_unsubscribe_task(websocket: WebSocket, message: Dict[str, Any]):
    """Handle task unsubscription request."""
    task_id = message.get("task_id")
    if not task_id:
        await send_error(websocket, "task_id is required for unsubscription")
        return
    
    await websocket_manager.unsubscribe_from_task(websocket, task_id)


async def handle_get_task_status(websocket: WebSocket, message: Dict[str, Any]):
    """Handle task status request."""
    task_id = message.get("task_id")
    if not task_id:
        await send_error(websocket, "task_id is required for status request")
        return
    
    task = task_manager.get_task(task_id)
    if not task:
        await send_error(websocket, f"Task {task_id} not found")
        return
    
    status_message = {
        "type": MessageType.PROGRESS_UPDATE,
        "task_id": task_id,
        "status": task.status.value,
        "stage": task.stage.value,
        "progress": task.overall_progress,
        "stage_progress": task.stage_progress,
        "current_region": task.current_region,
        "total_regions": task.total_regions,
        "message": task.message,
        "elapsed_time": task.elapsed_time,
        "estimated_remaining": task.estimated_remaining,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "error_message": task.error_message
    }
    
    await websocket_manager.send_to_connection(websocket, status_message)


async def handle_cancel_task(websocket: WebSocket, message: Dict[str, Any]):
    """Handle task cancellation request."""
    task_id = message.get("task_id")
    if not task_id:
        await send_error(websocket, "task_id is required for cancellation")
        return
    
    success = await task_manager.cancel_task(task_id)
    
    if success:
        response = {
            "type": MessageType.TASK_CANCELLED,
            "task_id": task_id,
            "message": "Task cancelled successfully"
        }
    else:
        response = {
            "type": "error",
            "message": f"Failed to cancel task {task_id} - task not found"
        }
    
    await websocket_manager.send_to_connection(websocket, response)


async def handle_ping(websocket: WebSocket, message: Dict[str, Any]):
    """Handle ping request."""
    pong_message = {
        "type": MessageType.PONG,
        "timestamp": message.get("timestamp")
    }
    
    await websocket_manager.send_to_connection(websocket, pong_message)


async def send_error(websocket: WebSocket, error_message: str):
    """
    Send error message to client.
    
    Args:
        websocket: WebSocket connection
        error_message: Error description
    """
    error_response = {
        "type": "error",
        "error": error_message,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await websocket_manager.send_to_connection(websocket, error_response)