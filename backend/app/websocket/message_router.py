"""Message routing for WebSocket communications."""
import json
import asyncio
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from app.websocket.connection_manager import connection_manager
from app.websocket.iopaint_client import iopaint_ws_client


async def handle_websocket_connection(websocket: WebSocket, task_id: str = None):
    """
    Handle WebSocket connection from frontend client.
    
    Args:
        websocket: WebSocket connection
        task_id: Optional task ID to subscribe to
    """
    connection_id = f"{websocket.client.host}:{websocket.client.port}_{id(websocket)}"
    
    try:
        # Connect to frontend client
        await connection_manager.connect(websocket, connection_id, task_id)
        
        # Ensure IOPaint WebSocket client is connected
        if not iopaint_ws_client.is_connected():
            await iopaint_ws_client.connect()
        
        # Subscribe to IOPaint task if provided
        if task_id:
            await iopaint_ws_client.subscribe_to_task(task_id)
        
        logger.info(f"Frontend WebSocket connected: {connection_id}, task: {task_id}")
        
        # Message handling loop
        while True:
            try:
                # Receive message from frontend client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle client message
                await handle_client_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Frontend WebSocket client disconnected: {connection_id}")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received from client {connection_id}: {e}")
                await send_error_to_client(connection_id, "Invalid JSON format")
            except Exception as e:
                logger.error(f"Error handling WebSocket message from {connection_id}: {e}")
                await send_error_to_client(connection_id, f"Message handling error: {str(e)}")
    
    except Exception as e:
        logger.error(f"WebSocket connection error for {connection_id}: {e}")
    
    finally:
        # Clean up connection
        connection_manager.disconnect(connection_id)
        
        # Unsubscribe from IOPaint task if needed
        if task_id and task_id in iopaint_ws_client.get_active_tasks():
            # Check if any other frontend connections are still subscribed to this task
            if connection_manager.get_connection_count(task_id) == 0:
                await iopaint_ws_client.unsubscribe_from_task(task_id)


async def handle_client_message(connection_id: str, message: Dict[str, Any]):
    """
    Handle incoming message from frontend client.
    
    Args:
        connection_id: Frontend connection ID
        message: Parsed message data
    """
    message_type = message.get("type")
    
    if not message_type:
        await send_error_to_client(connection_id, "Message type is required")
        return
    
    logger.debug(f"Handling client message: {message_type} from {connection_id}")
    
    try:
        if message_type == "subscribe_task":
            await handle_subscribe_task(connection_id, message)
        
        elif message_type == "unsubscribe_task":
            await handle_unsubscribe_task(connection_id, message)
        
        elif message_type == "get_task_status":
            await handle_get_task_status(connection_id, message)
        
        elif message_type == "cancel_task":
            await handle_cancel_task(connection_id, message)
        
        elif message_type == "ping":
            await handle_ping(connection_id, message)
        
        else:
            await send_error_to_client(connection_id, f"Unknown message type: {message_type}")
    
    except Exception as e:
        logger.error(f"Error handling message type {message_type} from {connection_id}: {e}")
        await send_error_to_client(connection_id, f"Error processing {message_type}: {str(e)}")


async def handle_subscribe_task(connection_id: str, message: Dict[str, Any]):
    """Handle task subscription request."""
    task_id = message.get("task_id")
    if not task_id:
        await send_error_to_client(connection_id, "task_id is required for subscription")
        return
    
    # Subscribe frontend connection to task
    await connection_manager.subscribe_to_task(connection_id, task_id)
    
    # Subscribe to IOPaint service if not already subscribed
    if task_id not in iopaint_ws_client.get_active_tasks():
        await iopaint_ws_client.subscribe_to_task(task_id)
    
    logger.info(f"Client {connection_id} subscribed to task {task_id}")


async def handle_unsubscribe_task(connection_id: str, message: Dict[str, Any]):
    """Handle task unsubscription request."""
    task_id = message.get("task_id")
    if not task_id:
        await send_error_to_client(connection_id, "task_id is required for unsubscription")
        return
    
    # Unsubscribe frontend connection from task
    await connection_manager.unsubscribe_from_task(connection_id, task_id)
    
    # Check if any other frontend connections are still subscribed to this task
    if connection_manager.get_connection_count(task_id) == 0:
        await iopaint_ws_client.unsubscribe_from_task(task_id)
    
    logger.info(f"Client {connection_id} unsubscribed from task {task_id}")


async def handle_get_task_status(connection_id: str, message: Dict[str, Any]):
    """Handle task status request by forwarding to IOPaint service."""
    task_id = message.get("task_id")
    if not task_id:
        await send_error_to_client(connection_id, "task_id is required for status request")
        return
    
    # For now, we'll fetch status via HTTP API since the WebSocket doesn't support status queries
    from app.infrastructure.clients.iopaint_client import IOPaintClient
    
    try:
        client = IOPaintClient()
        # Note: This would require implementing a get_task_status method in IOPaintClient
        # For now, send a placeholder response
        response = {
            "type": "task_status_response",
            "task_id": task_id,
            "message": "Status query not yet implemented via WebSocket"
        }
        
        await connection_manager.send_personal_message(response, connection_id)
        
    except Exception as e:
        await send_error_to_client(connection_id, f"Failed to get task status: {str(e)}")


async def handle_cancel_task(connection_id: str, message: Dict[str, Any]):
    """Handle task cancellation request by forwarding to IOPaint service."""
    task_id = message.get("task_id")
    if not task_id:
        await send_error_to_client(connection_id, "task_id is required for cancellation")
        return
    
    # For now, we'll cancel via HTTP API since the WebSocket doesn't support cancellation
    from app.infrastructure.clients.iopaint_client import IOPaintClient
    
    try:
        client = IOPaintClient()
        # Note: This would require implementing a cancel_task method in IOPaintClient
        # For now, send a placeholder response
        response = {
            "type": "task_cancel_response",
            "task_id": task_id,
            "message": "Task cancellation not yet implemented via WebSocket"
        }
        
        await connection_manager.send_personal_message(response, connection_id)
        
    except Exception as e:
        await send_error_to_client(connection_id, f"Failed to cancel task: {str(e)}")


async def handle_ping(connection_id: str, message: Dict[str, Any]):
    """Handle ping request."""
    pong_response = {
        "type": "pong",
        "timestamp": message.get("timestamp"),
        "server_timestamp": asyncio.get_event_loop().time()
    }
    
    await connection_manager.send_personal_message(pong_response, connection_id)


async def send_error_to_client(connection_id: str, error_message: str):
    """
    Send error message to frontend client.
    
    Args:
        connection_id: Frontend connection ID
        error_message: Error description
    """
    error_response = {
        "type": "error",
        "error": error_message,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await connection_manager.send_personal_message(error_response, connection_id)