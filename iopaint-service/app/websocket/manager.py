"""WebSocket connection manager for handling real-time progress updates."""
import json
import asyncio
from typing import Dict, Set, Optional, Any, Union
from datetime import datetime
import websockets
from fastapi import WebSocket
from loguru import logger


class WebSocketManager:
    """Manages WebSocket connections for real-time progress updates."""
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self.connections: Dict[str, Set[Union[websockets.WebSocketServerProtocol, WebSocket]]] = {}
        self.task_connections: Dict[str, Set[Union[websockets.WebSocketServerProtocol, WebSocket]]] = {}
        self.connection_tasks: Dict[str, str] = {}  # connection_id -> task_id
        
        logger.info("WebSocket manager initialized")
    
    async def connect(self, websocket: Union[websockets.WebSocketServerProtocol, WebSocket], task_id: Optional[str] = None):
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            task_id: Optional task ID to subscribe to
        """
        # Generate connection ID safely for both FastAPI WebSocket and websockets WebSocketServerProtocol
        try:
            if isinstance(websocket, WebSocket) and hasattr(websocket, 'client') and websocket.client:
                # FastAPI WebSocket
                connection_id = f"{websocket.client.host}:{websocket.client.port}_{id(websocket)}"
            elif hasattr(websocket, 'remote_address') and websocket.remote_address:
                # websockets WebSocketServerProtocol
                connection_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}_{id(websocket)}"
            else:
                connection_id = f"ws_{id(websocket)}"
        except Exception:
            connection_id = f"ws_{id(websocket)}"
        
        # Add to general connections
        if task_id not in self.connections:
            self.connections[task_id or "general"] = set()
        self.connections[task_id or "general"].add(websocket)
        
        # If subscribing to specific task
        if task_id:
            if task_id not in self.task_connections:
                self.task_connections[task_id] = set()
            self.task_connections[task_id].add(websocket)
            self.connection_tasks[connection_id] = task_id
        
        logger.info(f"WebSocket connected: {connection_id}, task: {task_id}")
        
        # Send connection confirmation
        await self.send_to_connection(websocket, {
            "type": "connection_established",
            "connection_id": connection_id,
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def disconnect(self, websocket: Union[websockets.WebSocketServerProtocol, WebSocket]):
        """
        Unregister a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        # Generate connection ID safely for both FastAPI WebSocket and websockets WebSocketServerProtocol
        try:
            if isinstance(websocket, WebSocket) and hasattr(websocket, 'client') and websocket.client:
                # FastAPI WebSocket
                connection_id = f"{websocket.client.host}:{websocket.client.port}_{id(websocket)}"
            elif hasattr(websocket, 'remote_address') and websocket.remote_address:
                # websockets WebSocketServerProtocol
                connection_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}_{id(websocket)}"
            else:
                connection_id = f"ws_{id(websocket)}"
        except Exception:
            connection_id = f"ws_{id(websocket)}"
        
        # Remove from general connections
        for connections in self.connections.values():
            connections.discard(websocket)
        
        # Remove from task-specific connections
        if connection_id in self.connection_tasks:
            task_id = self.connection_tasks[connection_id]
            if task_id in self.task_connections:
                self.task_connections[task_id].discard(websocket)
                if not self.task_connections[task_id]:
                    del self.task_connections[task_id]
            del self.connection_tasks[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_to_connection(self, websocket: Union[websockets.WebSocketServerProtocol, WebSocket], message: Dict[str, Any]):
        """
        Send message to a specific connection.
        
        Args:
            websocket: Target WebSocket connection
            message: Message to send
        """
        try:
            # Ensure message is a dictionary before serializing
            if isinstance(message, dict):
                json_message = json.dumps(message)
            else:
                logger.warning(f"Message is not a dict: {type(message)}, converting to string")
                json_message = json.dumps({"message": str(message)})
            
            # Send message using appropriate method based on WebSocket type
            if isinstance(websocket, WebSocket):
                # FastAPI WebSocket
                await websocket.send_text(json_message)
            else:
                # websockets WebSocketServerProtocol
                await websocket.send(json_message)
        except (websockets.ConnectionClosed, Exception) as e:
            if "ConnectionClosed" in str(type(e)):
                logger.warning("Attempted to send to closed WebSocket connection")
            else:
                logger.error(f"Error sending WebSocket message: {e}, message type: {type(message)}")
    
    async def broadcast_to_task(self, task_id: str, message: Dict[str, Any]):
        """
        Broadcast message to all connections subscribed to a specific task.
        
        Args:
            task_id: Task ID to broadcast to
            message: Message to broadcast
        """
        if task_id not in self.task_connections:
            logger.debug(f"No connections subscribed to task {task_id}")
            return
        
        # Add timestamp if not present and message is a dictionary
        if isinstance(message, dict) and "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        elif not isinstance(message, dict):
            logger.warning(f"Broadcast message is not a dict: {type(message)}, converting")
            message = {"message": str(message), "timestamp": datetime.now().isoformat()}
        
        logger.debug(f"Broadcasting to {len(self.task_connections[task_id])} connections for task {task_id}")
        
        # Send to all connections for this task
        disconnected_connections = set()
        for websocket in self.task_connections[task_id].copy():
            try:
                # Ensure message is a dictionary before serializing
                if isinstance(message, dict):
                    json_message = json.dumps(message)
                else:
                    logger.warning(f"Broadcast message is not a dict: {type(message)}, converting to string")
                    json_message = json.dumps({"message": str(message)})
                
                # Send message using appropriate method based on WebSocket type
                if isinstance(websocket, WebSocket):
                    # FastAPI WebSocket
                    await websocket.send_text(json_message)
                else:
                    # websockets WebSocketServerProtocol
                    await websocket.send(json_message)
            except websockets.ConnectionClosed:
                disconnected_connections.add(websocket)
                logger.debug("Connection closed during broadcast")
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}, message type: {type(message)}")
                disconnected_connections.add(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected_connections:
            await self.disconnect(websocket)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Message to broadcast
        """
        if isinstance(message, dict) and "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        elif not isinstance(message, dict):
            logger.warning(f"Broadcast all message is not a dict: {type(message)}, converting")
            message = {"message": str(message), "timestamp": datetime.now().isoformat()}
        
        all_connections = set()
        for connections in self.connections.values():
            all_connections.update(connections)
        
        logger.debug(f"Broadcasting to {len(all_connections)} total connections")
        
        # Send to all connections
        disconnected_connections = set()
        for websocket in all_connections:
            try:
                # Send message using appropriate method based on WebSocket type
                json_message = json.dumps(message)
                if isinstance(websocket, WebSocket):
                    # FastAPI WebSocket
                    await websocket.send_text(json_message)
                else:
                    # websockets WebSocketServerProtocol
                    await websocket.send(json_message)
            except websockets.ConnectionClosed:
                disconnected_connections.add(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected_connections.add(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected_connections:
            await self.disconnect(websocket)
    
    async def subscribe_to_task(self, websocket: Union[websockets.WebSocketServerProtocol, WebSocket], task_id: str):
        """
        Subscribe a connection to a specific task.
        
        Args:
            websocket: WebSocket connection
            task_id: Task ID to subscribe to
        """
        # Generate connection ID safely for both FastAPI WebSocket and websockets WebSocketServerProtocol
        try:
            if isinstance(websocket, WebSocket) and hasattr(websocket, 'client') and websocket.client:
                # FastAPI WebSocket
                connection_id = f"{websocket.client.host}:{websocket.client.port}_{id(websocket)}"
            elif hasattr(websocket, 'remote_address') and websocket.remote_address:
                # websockets WebSocketServerProtocol
                connection_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}_{id(websocket)}"
            else:
                connection_id = f"ws_{id(websocket)}"
        except Exception:
            connection_id = f"ws_{id(websocket)}"
        
        # Add to task connections
        if task_id not in self.task_connections:
            self.task_connections[task_id] = set()
        self.task_connections[task_id].add(websocket)
        self.connection_tasks[connection_id] = task_id
        
        logger.info(f"Connection {connection_id} subscribed to task {task_id}")
        
        # Send subscription confirmation
        await self.send_to_connection(websocket, {
            "type": "task_subscribed",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def unsubscribe_from_task(self, websocket: Union[websockets.WebSocketServerProtocol, WebSocket], task_id: str):
        """
        Unsubscribe a connection from a specific task.
        
        Args:
            websocket: WebSocket connection
            task_id: Task ID to unsubscribe from
        """
        # Generate connection ID safely for both FastAPI WebSocket and websockets WebSocketServerProtocol
        try:
            if isinstance(websocket, WebSocket) and hasattr(websocket, 'client') and websocket.client:
                # FastAPI WebSocket
                connection_id = f"{websocket.client.host}:{websocket.client.port}_{id(websocket)}"
            elif hasattr(websocket, 'remote_address') and websocket.remote_address:
                # websockets WebSocketServerProtocol
                connection_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}_{id(websocket)}"
            else:
                connection_id = f"ws_{id(websocket)}"
        except Exception:
            connection_id = f"ws_{id(websocket)}"
        
        # Remove from task connections
        if task_id in self.task_connections:
            self.task_connections[task_id].discard(websocket)
            if not self.task_connections[task_id]:
                del self.task_connections[task_id]
        
        if connection_id in self.connection_tasks:
            del self.connection_tasks[connection_id]
        
        logger.info(f"Connection {connection_id} unsubscribed from task {task_id}")
        
        # Send unsubscription confirmation
        await self.send_to_connection(websocket, {
            "type": "task_unsubscribed", 
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_connection_count(self, task_id: Optional[str] = None) -> int:
        """
        Get number of connections for a task or total.
        
        Args:
            task_id: Optional task ID, if None returns total connections
            
        Returns:
            Number of connections
        """
        if task_id:
            return len(self.task_connections.get(task_id, set()))
        else:
            all_connections = set()
            for connections in self.connections.values():
                all_connections.update(connections)
            return len(all_connections)
    
    def get_active_tasks(self) -> list[str]:
        """
        Get list of active task IDs.
        
        Returns:
            List of task IDs with active connections
        """
        return list(self.task_connections.keys())


# Global WebSocket manager instance
websocket_manager = WebSocketManager()