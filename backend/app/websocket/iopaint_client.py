"""WebSocket client for connecting to IOPaint service."""
import json
import asyncio
import uuid
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import websockets
from loguru import logger

from app.config.settings import settings
from app.websocket.connection_manager import connection_manager


class IOPaintWebSocketClient:
    """WebSocket client for receiving progress updates from IOPaint service."""
    
    def __init__(self):
        """Initialize IOPaint WebSocket client."""
        self.iopaint_ws_url = f"ws://iopaint-service:{settings.iopaint_port}/api/v1/ws/progress"
        self.connection = None
        self.active_tasks: Dict[str, bool] = {}
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        
        # Task ID mapping: iopaint_task_id -> backend_task_id
        self.task_id_mapping: Dict[str, str] = {}
        
        logger.info(f"IOPaint WebSocket client initialized with URL: {self.iopaint_ws_url}")
    
    async def connect(self) -> bool:
        """
        Connect to IOPaint WebSocket service.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            logger.info("Connecting to IOPaint WebSocket service...")
            
            self.connection = await websockets.connect(
                self.iopaint_ws_url,
                ping_interval=30,
                ping_timeout=10
            )
            
            logger.info("Connected to IOPaint WebSocket service")
            self.reconnect_attempts = 0
            
            # Start message listening task
            asyncio.create_task(self._listen_for_messages())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to IOPaint WebSocket: {e}")
            self.connection = None
            return False
    
    async def disconnect(self):
        """Disconnect from IOPaint WebSocket service."""
        if self.connection:
            try:
                await self.connection.close()
                logger.info("Disconnected from IOPaint WebSocket service")
            except Exception as e:
                logger.warning(f"Error during WebSocket disconnect: {e}")
            finally:
                self.connection = None
    
    async def subscribe_to_task(self, task_id: str):
        """
        Subscribe to progress updates for a specific task.
        
        Args:
            task_id: Task ID to subscribe to
        """
        if not self.connection:
            logger.warning(f"Cannot subscribe to task {task_id}: not connected to IOPaint service")
            return
        
        try:
            subscribe_message = {
                "type": "subscribe_task",
                "task_id": task_id
            }
            
            await self.connection.send(json.dumps(subscribe_message))
            self.active_tasks[task_id] = True
            
            logger.info(f"Subscribed to IOPaint task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to IOPaint task {task_id}: {e}")
    
    async def unsubscribe_from_task(self, task_id: str):
        """
        Unsubscribe from progress updates for a specific task.
        
        Args:
            task_id: Task ID to unsubscribe from
        """
        if not self.connection:
            return
        
        try:
            unsubscribe_message = {
                "type": "unsubscribe_task",
                "task_id": task_id
            }
            
            await self.connection.send(json.dumps(unsubscribe_message))
            
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            logger.info(f"Unsubscribed from IOPaint task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from IOPaint task {task_id}: {e}")
    
    async def _listen_for_messages(self):
        """Listen for messages from IOPaint WebSocket service."""
        logger.info("Started listening for IOPaint WebSocket messages")
        
        try:
            async for message in self.connection:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON received from IOPaint service: {e}")
                except Exception as e:
                    logger.error(f"Error handling IOPaint message: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.warning("IOPaint WebSocket connection closed")
            await self._handle_disconnect()
        except Exception as e:
            logger.error(f"Error in IOPaint WebSocket listener: {e}")
            await self._handle_disconnect()
    
    async def _handle_message(self, data: Dict[str, Any]):
        """
        Handle incoming message from IOPaint service.
        
        Args:
            data: Parsed message data
        """
        message_type = data.get("type")
        task_id = data.get("task_id")
        
        logger.debug(f"Received IOPaint message: {message_type} for task {task_id}")
        
        # Forward messages to frontend clients with mapped task ID and session ID
        if message_type in ["progress_update", "task_completed", "task_failed", "task_cancelled"] and task_id:
            # Use mapped backend task ID if available
            frontend_task_id = self.task_id_mapping.get(task_id, task_id)
            mapped_data = data.copy()
            mapped_data["task_id"] = frontend_task_id
            
            # Add session_id from task info if available
            # Import here to avoid circular imports
            from app.infrastructure.api.routes import get_global_async_processor
            async_processor = get_global_async_processor()
            if async_processor and frontend_task_id in async_processor._active_tasks:
                task_info = async_processor._active_tasks[frontend_task_id]
                mapped_data["session_id"] = task_info.session_id
            
            # Handle task completion special processing
            if message_type == "task_completed":
                await self._handle_task_completion(task_id, data)
            
            await connection_manager.broadcast_to_task(frontend_task_id, mapped_data)
            
            # Clean up task subscription and mapping for terminal states
            if message_type in ["task_completed", "task_failed", "task_cancelled"]:
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                self.remove_task_mapping(task_id)
        
        elif message_type in ["connection_established", "task_subscribed", "task_unsubscribed"]:
            logger.debug(f"IOPaint service acknowledgment: {message_type}")
        
        else:
            logger.debug(f"Unhandled IOPaint message type: {message_type}")
    
    async def _handle_task_completion(self, task_id: str, data: Dict[str, Any]):
        """Handle task completion - update session with processed image."""
        try:
            # Import here to avoid circular imports
            from app.infrastructure.api.routes import get_global_async_processor
            
            # Get async processor and task info using mapped task ID
            async_processor = get_global_async_processor()
            # Use mapped backend task ID if available
            frontend_task_id = self.task_id_mapping.get(task_id, task_id)
            task_info = async_processor.get_task_status(frontend_task_id)
            
            if not task_info:
                logger.warning(f"Task {frontend_task_id} (mapped from {task_id}) not found in async processor")
                return
            
            # Session lookup not needed here since HTTP callback handles the actual processing
            session_id = task_info.session_id
            
            # Note: With HTTP callback mechanism, the processed image will be handled
            # via the callback endpoint, not through WebSocket completion messages.
            # We just update the task status here.
            logger.info(f"Task {task_id} completed via WebSocket - processed image will be handled via HTTP callback")
            
            # Update task info in async processor (minimal update, full handling via HTTP callback)
            task_info.status = "completed"
            task_info.stage = "completed"
            task_info.progress = 100.0
            task_info.message = "Processing completed successfully"
            task_info.completed_at = datetime.now()
            
            # Note: WebSocket completion notification is sent by HTTP callback in routes.py
            # to avoid duplicate notifications and ensure processed image is ready
            
            logger.info(f"Task {frontend_task_id} (IOPaint: {task_id}) marked as completed, HTTP callback will handle WebSocket notification")
            
        except Exception as e:
            logger.error(f"Error handling task completion for {task_id}: {e}")
            
            # Update task as failed
            try:
                async_processor = get_global_async_processor()
                task_info = async_processor.get_task_status(task_id)
                if task_info:
                    task_info.status = "failed"
                    task_info.error_message = f"Post-processing error: {str(e)}"
                    task_info.completed_at = datetime.now()
            except:
                pass
    
    async def _handle_disconnect(self):
        """Handle WebSocket disconnection and attempt reconnection."""
        self.connection = None
        
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"Attempting to reconnect to IOPaint service (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
            
            await asyncio.sleep(self.reconnect_delay)
            
            if await self.connect():
                # Resubscribe to active tasks
                for task_id in list(self.active_tasks.keys()):
                    await self.subscribe_to_task(task_id)
            else:
                # Schedule another reconnection attempt
                asyncio.create_task(self._handle_disconnect())
        else:
            logger.error("Max reconnection attempts reached for IOPaint WebSocket")
    
    async def send_ping(self):
        """Send ping to keep connection alive."""
        if self.connection:
            try:
                ping_message = {
                    "type": "ping",
                    "timestamp": asyncio.get_event_loop().time()
                }
                await self.connection.send(json.dumps(ping_message))
            except Exception as e:
                logger.warning(f"Failed to send ping to IOPaint service: {e}")
    
    def is_connected(self) -> bool:
        """
        Check if connected to IOPaint service.
        
        Returns:
            True if connected, False otherwise
        """
        if self.connection is None:
            return False
        
        try:
            # Check if connection is still open - different websockets versions use different attributes
            if hasattr(self.connection, 'closed'):
                return not self.connection.closed
            elif hasattr(self.connection, 'open'):
                return self.connection.open
            elif hasattr(self.connection, 'state'):
                # For newer websockets versions, check state
                return str(self.connection.state) == 'State.OPEN'
            else:
                # Fallback: assume connected if connection object exists
                return True
        except Exception:
            return False
    
    def get_active_tasks(self) -> list[str]:
        """
        Get list of active task subscriptions.
        
        Returns:
            List of task IDs
        """
        return list(self.active_tasks.keys())
    
    def add_task_mapping(self, iopaint_task_id: str, backend_task_id: str):
        """
        Add task ID mapping from IOPaint to Backend.
        
        Args:
            iopaint_task_id: Task ID from IOPaint service
            backend_task_id: Task ID used by Backend/Frontend
        """
        self.task_id_mapping[iopaint_task_id] = backend_task_id
        logger.info(f"Added task mapping: {iopaint_task_id} -> {backend_task_id}")
    
    def remove_task_mapping(self, iopaint_task_id: str):
        """
        Remove task ID mapping.
        
        Args:
            iopaint_task_id: Task ID to remove from mapping
        """
        if iopaint_task_id in self.task_id_mapping:
            backend_task_id = self.task_id_mapping.pop(iopaint_task_id)
            logger.info(f"Removed task mapping: {iopaint_task_id} -> {backend_task_id}")


# Global IOPaint WebSocket client instance
iopaint_ws_client = IOPaintWebSocketClient()