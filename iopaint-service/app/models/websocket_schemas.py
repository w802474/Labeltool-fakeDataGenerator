"""WebSocket message schemas for real-time progress monitoring."""
from typing import Optional, Any, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class MessageType(str, Enum):
    """WebSocket message types."""
    # Connection management
    CONNECTION_ESTABLISHED = "connection_established"
    TASK_SUBSCRIBED = "task_subscribed"
    TASK_UNSUBSCRIBED = "task_unsubscribed"
    
    # Progress updates
    PROGRESS_UPDATE = "progress_update"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    
    # Client requests
    SUBSCRIBE_TASK = "subscribe_task"
    UNSUBSCRIBE_TASK = "unsubscribe_task"
    GET_TASK_STATUS = "get_task_status"
    CANCEL_TASK = "cancel_task"
    PING = "ping"
    PONG = "pong"


class TaskStatusEnum(str, Enum):
    """Task status values."""
    PENDING = "pending"
    PREPARING = "preparing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class ProcessingStageEnum(str, Enum):
    """Processing stage values."""
    PREPARING = "preparing"
    MASKING = "masking"
    INPAINTING = "inpainting"
    FINALIZING = "finalizing"


# Base message schemas
class BaseMessage(BaseModel):
    """Base WebSocket message."""
    type: MessageType
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ClientMessage(BaseMessage):
    """Message sent from client to server."""
    pass


class ServerMessage(BaseMessage):
    """Message sent from server to client."""
    pass


# Connection management messages
class ConnectionEstablishedMessage(ServerMessage):
    """Sent when WebSocket connection is established."""
    type: MessageType = MessageType.CONNECTION_ESTABLISHED
    connection_id: str
    task_id: Optional[str] = None


class TaskSubscribedMessage(ServerMessage):
    """Sent when client subscribes to a task."""
    type: MessageType = MessageType.TASK_SUBSCRIBED
    task_id: str


class TaskUnsubscribedMessage(ServerMessage):
    """Sent when client unsubscribes from a task."""
    type: MessageType = MessageType.TASK_UNSUBSCRIBED
    task_id: str


# Progress update messages
class ProgressUpdateMessage(ServerMessage):
    """Progress update message."""
    type: MessageType = MessageType.PROGRESS_UPDATE
    task_id: str
    status: TaskStatusEnum
    stage: ProcessingStageEnum
    overall_progress: float = Field(ge=0, le=100, description="Overall progress percentage")
    stage_progress: float = Field(ge=0, le=100, description="Current stage progress percentage")
    current_region: int = Field(ge=0, description="Current region being processed")
    total_regions: int = Field(ge=0, description="Total number of regions")
    message: str = Field(description="Human-readable progress message")
    elapsed_time: float = Field(ge=0, description="Elapsed time in seconds")
    estimated_remaining: Optional[float] = Field(None, ge=0, description="Estimated remaining time in seconds")
    error: Optional[str] = Field(None, description="Error message if failed")
    result_path: Optional[str] = Field(None, description="Result file path if completed")


class TaskCompletedMessage(ServerMessage):
    """Task completion message."""
    type: MessageType = MessageType.TASK_COMPLETED
    task_id: str
    result_path: Optional[str] = None
    elapsed_time: float
    total_regions: int


class TaskFailedMessage(ServerMessage):
    """Task failure message."""
    type: MessageType = MessageType.TASK_FAILED
    task_id: str
    error: str
    elapsed_time: float


class TaskCancelledMessage(ServerMessage):
    """Task cancellation message."""
    type: MessageType = MessageType.TASK_CANCELLED
    task_id: str
    elapsed_time: float


# Client request messages
class SubscribeTaskMessage(ClientMessage):
    """Subscribe to task progress updates."""
    type: MessageType = MessageType.SUBSCRIBE_TASK
    task_id: str


class UnsubscribeTaskMessage(ClientMessage):
    """Unsubscribe from task progress updates."""
    type: MessageType = MessageType.UNSUBSCRIBE_TASK
    task_id: str


class GetTaskStatusMessage(ClientMessage):
    """Request current task status."""
    type: MessageType = MessageType.GET_TASK_STATUS
    task_id: str


class CancelTaskMessage(ClientMessage):
    """Cancel a running task."""
    type: MessageType = MessageType.CANCEL_TASK
    task_id: str


class PingMessage(ClientMessage):
    """Ping message for connection health check."""
    type: MessageType = MessageType.PING


class PongMessage(ServerMessage):
    """Pong response to ping."""
    type: MessageType = MessageType.PONG


# Response message for task status requests
class TaskStatusResponse(ServerMessage):
    """Response to task status request."""
    type: MessageType = MessageType.PROGRESS_UPDATE
    task_id: str
    status: TaskStatusEnum
    stage: ProcessingStageEnum
    overall_progress: float
    stage_progress: float
    current_region: int
    total_regions: int
    message: str
    elapsed_time: float
    estimated_remaining: Optional[float] = None
    error: Optional[str] = None
    result_path: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# Async task request/response models moved to schemas.py to avoid circular imports


# Error response
class ErrorMessage(ServerMessage):
    """Error message."""
    type: MessageType = MessageType.TASK_FAILED
    error: str
    details: Optional[Dict[str, Any]] = None