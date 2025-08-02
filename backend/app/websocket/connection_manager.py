"""WebSocket connection manager for backend service."""
import json
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime
import websockets
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


class WebSocketConnectionManager:
    """Manages WebSocket connections for the backend service."""
    
    def __init__(self):
        """Initialize WebSocket connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.task_subscriptions: Dict[str, Set[str]] = {}  # task_id -> set of connection_ids
        self.connection_tasks: Dict[str, str] = {}  # connection_id -> task_id
        
        logger.info("Backend WebSocket connection manager initialized")
    
    async def connect(self, websocket: WebSocket, connection_id: str, task_id: Optional[str] = None):
        """
        Accept a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            connection_id: Unique connection identifier
            task_id: Optional task ID to subscribe to
        """
        await websocket.accept()
        
        self.active_connections[connection_id] = websocket
        
        # Subscribe to task if provided
        if task_id:
            if task_id not in self.task_subscriptions:
                self.task_subscriptions[task_id] = set()
            self.task_subscriptions[task_id].add(connection_id)
            self.connection_tasks[connection_id] = task_id
        
        logger.info(f"WebSocket connected: {connection_id}, task: {task_id}")
        
        # Send connection confirmation
        await self.send_personal_message({
            "type": "connection_established",
            "connection_id": connection_id,
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        }, connection_id)
    
    def disconnect(self, connection_id: str):
        """
        Remove a WebSocket connection.
        
        Args:
            connection_id: Connection identifier to remove
        """
        # Remove from active connections
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from task subscriptions
        if connection_id in self.connection_tasks:
            task_id = self.connection_tasks[connection_id]
            if task_id in self.task_subscriptions:
                self.task_subscriptions[task_id].discard(connection_id)
                if not self.task_subscriptions[task_id]:
                    del self.task_subscriptions[task_id]
            del self.connection_tasks[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """
        Send message to a specific connection.
        
        Args:
            message: Message to send
            connection_id: Target connection ID
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Connection {connection_id} not found")
            return
        
        websocket = self.active_connections[connection_id]
        
        try:
            await websocket.send_text(json.dumps(message))
        except WebSocketDisconnect:
            logger.info(f"Connection {connection_id} disconnected during send")
            self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            self.disconnect(connection_id)
    
    async def broadcast_to_task(self, task_id: str, message: Dict[str, Any]):
        """
        Broadcast message to all connections subscribed to a task.
        
        Args:
            task_id: Task ID to broadcast to
            message: Message to broadcast
        """
        if task_id not in self.task_subscriptions:
            logger.debug(f"No connections subscribed to task {task_id}")
            return
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        logger.debug(f"Broadcasting to {len(self.task_subscriptions[task_id])} connections for task {task_id}")
        
        # Send to all connections for this task
        disconnected_connections = []
        for connection_id in self.task_subscriptions[task_id].copy():
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.send_text(json.dumps(message))
                except WebSocketDisconnect:
                    disconnected_connections.append(connection_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_id}: {e}")
                    disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            self.disconnect(connection_id)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """
        Broadcast message to all active connections.
        
        Args:
            message: Message to broadcast
        """
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        logger.debug(f"Broadcasting to {len(self.active_connections)} total connections")
        
        # Send to all connections
        disconnected_connections = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except WebSocketDisconnect:
                disconnected_connections.append(connection_id)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            self.disconnect(connection_id)
    
    async def subscribe_to_task(self, connection_id: str, task_id: str):
        """
        Subscribe a connection to a specific task.
        
        Args:
            connection_id: Connection ID
            task_id: Task ID to subscribe to
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Connection {connection_id} not found for task subscription")
            return
        
        # Add to task subscriptions
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = set()
        self.task_subscriptions[task_id].add(connection_id)
        self.connection_tasks[connection_id] = task_id
        
        logger.info(f"Connection {connection_id} subscribed to task {task_id}")
        
        # Send subscription confirmation
        await self.send_personal_message({
            "type": "task_subscribed",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        }, connection_id)
    
    async def unsubscribe_from_task(self, connection_id: str, task_id: str):
        """
        Unsubscribe a connection from a specific task.
        
        Args:
            connection_id: Connection ID
            task_id: Task ID to unsubscribe from
        """
        # Remove from task subscriptions
        if task_id in self.task_subscriptions:
            self.task_subscriptions[task_id].discard(connection_id)
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]
        
        if connection_id in self.connection_tasks:
            del self.connection_tasks[connection_id]
        
        logger.info(f"Connection {connection_id} unsubscribed from task {task_id}")
        
        # Send unsubscription confirmation
        if connection_id in self.active_connections:
            await self.send_personal_message({
                "type": "task_unsubscribed",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            }, connection_id)
    
    def get_connection_count(self, task_id: Optional[str] = None) -> int:
        """
        Get number of connections for a task or total.
        
        Args:
            task_id: Optional task ID, if None returns total connections
            
        Returns:
            Number of connections
        """
        if task_id:
            return len(self.task_subscriptions.get(task_id, set()))
        else:
            return len(self.active_connections)
    
    def get_active_tasks(self) -> list[str]:
        """
        Get list of active task IDs.
        
        Returns:
            List of task IDs with active connections
        """
        return list(self.task_subscriptions.keys())


# Global connection manager instance
connection_manager = WebSocketConnectionManager()