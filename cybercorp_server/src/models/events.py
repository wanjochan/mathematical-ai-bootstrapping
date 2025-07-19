"""Event models for CyberCorp Server."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class EventType(str, Enum):
    """Event type enumeration."""
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_METRICS_UPDATE = "system.metrics_update"
    SYSTEM_ERROR = "system.error"
    
    # Window events
    WINDOW_CREATED = "window.created"
    WINDOW_DESTROYED = "window.destroyed"
    WINDOW_FOCUSED = "window.focused"
    WINDOW_MINIMIZED = "window.minimized"
    WINDOW_MAXIMIZED = "window.maximized"
    WINDOW_RESTORED = "window.restored"
    WINDOW_MOVED = "window.moved"
    WINDOW_RESIZED = "window.resized"
    WINDOW_TITLE_CHANGED = "window.title_changed"
    
    # Process events
    PROCESS_STARTED = "process.started"
    PROCESS_TERMINATED = "process.terminated"
    PROCESS_SUSPENDED = "process.suspended"
    PROCESS_RESUMED = "process.resumed"
    PROCESS_CPU_HIGH = "process.cpu_high"
    PROCESS_MEMORY_HIGH = "process.memory_high"
    
    # Authentication events
    USER_LOGIN = "auth.user_login"
    USER_LOGOUT = "auth.user_logout"
    TOKEN_EXPIRED = "auth.token_expired"
    AUTH_FAILED = "auth.failed"
    
    # Configuration events
    CONFIG_UPDATED = "config.updated"
    CONFIG_RELOADED = "config.reloaded"
    
    # WebSocket events
    CLIENT_CONNECTED = "websocket.client_connected"
    CLIENT_DISCONNECTED = "websocket.client_disconnected"
    SUBSCRIPTION_ADDED = "websocket.subscription_added"
    SUBSCRIPTION_REMOVED = "websocket.subscription_removed"


class EventMessage(BaseModel):
    """Generic event message structure for real-time communication."""
    id: str = Field(..., description="Unique identifier for the event")
    type: EventType = Field(..., description="Type of the event")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event occurrence time")
    source: str = Field(..., description="Source system/component that triggered the event")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data payload")
    message: Optional[str] = Field(None, description="Human-readable event description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context information")
    priority: str = Field(default="normal", description="Event priority level (low, normal, high, critical)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event message to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data,
            "message": self.message,
            "metadata": self.metadata,
            "priority": self.priority
        }


class EventAcknowledgement(BaseModel):
    """Acknowledgement response for event messages."""
    received_at: datetime = Field(default_factory=datetime.now)
    processed: bool = Field(default=True)
    event_id: str = Field(..., description="Original event message ID")
    client_id: Optional[str] = Field(None, description="Acknowledging client identifier")
    error: Optional[str] = Field(None, description="Error message if processing failed")


class EventSubscription(BaseModel):
    """WebSocket event subscription model."""
    client_id: str = Field(..., description="Unique client identifier")
    event_types: List[EventType] = Field(..., description="List of event types to subscribe to")
    filter_conditions: Dict[str, Any] = Field(default_factory=dict, description="Additional filtering criteria")
    created_at: datetime = Field(default_factory=datetime.now)


class EventFilter(BaseModel):
    """Filter criteria for events."""
    event_types: Optional[List[EventType]] = Field(None, description="Filter by event types")
    source: Optional[str] = Field(None, description="Filter by event source")
    priority: Optional[str] = Field(None, description="Filter by priority")
    time_range: Optional[Dict[str, datetime]] = Field(None, description="Time range filter")
    data_filter: Optional[Dict[str, Any]] = Field(None, description="Filter by event data properties")
    


class EventSeverity(str, Enum):
    """Event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Event(BaseModel):
    """Base event model."""
    id: str = Field(..., description="Unique event identifier")
    type: EventType = Field(..., description="Event type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    severity: EventSeverity = Field(default=EventSeverity.INFO, description="Event severity")
    source: str = Field(..., description="Event source component")
    message: str = Field(..., description="Human-readable event message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional event data")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    session_id: Optional[str] = Field(None, description="Associated session ID")
    client_id: Optional[str] = Field(None, description="Associated client ID")
    tags: Optional[List[str]] = Field(None, description="Event tags for categorization")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemEvent(Event):
    """System-specific event model."""
    type: EventType = Field(..., description="System event type")
    system_info: Optional[Dict[str, Any]] = Field(None, description="System information")
    metrics: Optional[Dict[str, Any]] = Field(None, description="System metrics")


class WindowEvent(Event):
    """Window-specific event model."""
    type: EventType = Field(..., description="Window event type")
    window_id: str = Field(..., description="Window identifier")
    window_handle: Optional[int] = Field(None, description="Window handle")
    window_title: Optional[str] = Field(None, description="Window title")
    process_id: Optional[int] = Field(None, description="Associated process ID")
    bounds: Optional[Dict[str, int]] = Field(None, description="Window bounds")


class ProcessEvent(Event):
    """Process-specific event model."""
    type: EventType = Field(..., description="Process event type")
    process_id: int = Field(..., description="Process ID")
    process_name: Optional[str] = Field(None, description="Process name")
    executable: Optional[str] = Field(None, description="Process executable path")
    cpu_percent: Optional[float] = Field(None, description="CPU usage percentage")
    memory_percent: Optional[float] = Field(None, description="Memory usage percentage")


class AuthEvent(Event):
    """Authentication-specific event model."""
    type: EventType = Field(..., description="Authentication event type")
    username: Optional[str] = Field(None, description="Username involved")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    success: bool = Field(..., description="Whether the auth action was successful")
    failure_reason: Optional[str] = Field(None, description="Reason for failure if applicable")


class ConfigEvent(Event):
    """Configuration-specific event model."""
    type: EventType = Field(..., description="Configuration event type")
    config_section: Optional[str] = Field(None, description="Configuration section affected")
    changes: Optional[Dict[str, Any]] = Field(None, description="Configuration changes")
    previous_values: Optional[Dict[str, Any]] = Field(None, description="Previous configuration values")


class WebSocketEvent(Event):
    """WebSocket-specific event model."""
    type: EventType = Field(..., description="WebSocket event type")
    connection_id: str = Field(..., description="WebSocket connection identifier")
    topics: Optional[List[str]] = Field(None, description="Subscribed topics")
    message_count: Optional[int] = Field(None, description="Number of messages sent/received")


class MonitoringEvent(Event):
    """Monitoring-specific event model."""
    type: EventType = Field(..., description="Monitoring event type")
    metric_name: Optional[str] = Field(None, description="Metric name")
    threshold: Optional[float] = Field(None, description="Alert threshold")
    current_value: Optional[float] = Field(None, description="Current metric value")
    alert_rule: Optional[str] = Field(None, description="Alert rule identifier")


class EventFilter(BaseModel):
    """Event filtering model."""
    types: Optional[List[EventType]] = Field(None, description="Event types to include")
    severities: Optional[List[EventSeverity]] = Field(None, description="Event severities to include")
    sources: Optional[List[str]] = Field(None, description="Event sources to include")
    start_time: Optional[datetime] = Field(None, description="Start time filter")
    end_time: Optional[datetime] = Field(None, description="End time filter")
    user_id: Optional[str] = Field(None, description="User ID filter")
    session_id: Optional[str] = Field(None, description="Session ID filter")
    tags: Optional[List[str]] = Field(None, description="Tags filter")
    limit: Optional[int] = Field(100, description="Maximum number of events to return")
    offset: Optional[int] = Field(0, description="Number of events to skip")


class EventSubscription(BaseModel):
    """Event subscription model for WebSocket clients."""
    subscription_id: str = Field(..., description="Subscription identifier")
    client_id: str = Field(..., description="Client identifier")
    connection_id: str = Field(..., description="WebSocket connection identifier")
    event_types: List[EventType] = Field(..., description="Event types to subscribe to")
    filters: Optional[EventFilter] = Field(None, description="Additional event filters")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Subscription creation time")
    is_active: bool = Field(default=True, description="Whether subscription is active")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventBatch(BaseModel):
    """Event batch model for bulk operations."""
    events: List[Event] = Field(..., description="List of events")
    batch_id: str = Field(..., description="Batch identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Batch creation time")
    total_count: int = Field(..., description="Total number of events in batch")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventStats(BaseModel):
    """Event statistics model."""
    total_events: int = Field(..., description="Total number of events")
    events_by_type: Dict[EventType, int] = Field(..., description="Event count by type")
    events_by_severity: Dict[EventSeverity, int] = Field(..., description="Event count by severity")
    events_by_source: Dict[str, int] = Field(..., description="Event count by source")
    time_range: Dict[str, datetime] = Field(..., description="Time range of events")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# WebSocket message types for events
class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str = Field(..., description="Message type")
    id: str = Field(..., description="Message identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    payload: Dict[str, Any] = Field(..., description="Message payload")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventNotification(WebSocketMessage):
    """Event notification WebSocket message."""
    type: str = Field(default="event_notification", description="Message type")
    payload: Dict[str, Any] = Field(..., description="Event notification payload")


class DataUpdate(WebSocketMessage):
    """Data update WebSocket message."""
    type: str = Field(default="data_update", description="Message type")
    payload: Dict[str, Any] = Field(..., description="Data update payload")


class CommandResponse(WebSocketMessage):
    """Command response WebSocket message."""
    type: str = Field(default="command_response", description="Message type")
    payload: Dict[str, Any] = Field(..., description="Command response payload")