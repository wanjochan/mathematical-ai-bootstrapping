"""Windows management data models."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class WindowBounds(BaseModel):
    """Window bounds/position data model."""
    x: int = Field(..., description="Window X position")
    y: int = Field(..., description="Window Y position")
    width: int = Field(..., ge=0, description="Window width")
    height: int = Field(..., ge=0, description="Window height")


class WindowState(str, Enum):
    """Window state enumeration."""
    NORMAL = "normal"
    MINIMIZED = "minimized"
    MAXIMIZED = "maximized"
    FULLSCREEN = "fullscreen"
    HIDDEN = "hidden"


class WindowAction(str, Enum):
    """Window action enumeration."""
    FOCUS = "focus"
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    RESTORE = "restore"
    CLOSE = "close"
    MOVE = "move"
    RESIZE = "resize"
    SHOW = "show"
    HIDE = "hide"
    BRING_TO_FRONT = "bring_to_front"
    SEND_TO_BACK = "send_to_back"


class WindowInfo(BaseModel):
    """Window information data model."""
    id: str = Field(..., description="Unique window identifier")
    handle: int = Field(..., description="Window handle (HWND on Windows)")
    title: str = Field(..., description="Window title")
    class_name: Optional[str] = Field(None, description="Window class name")
    process_id: int = Field(..., description="Process ID that owns the window")
    process_name: str = Field(..., description="Process name")
    bounds: WindowBounds = Field(..., description="Window position and size")
    state: WindowState = Field(..., description="Current window state")
    is_visible: bool = Field(..., description="Whether window is visible")
    is_active: bool = Field(..., description="Whether window is currently active")
    opacity: float = Field(1.0, ge=0.0, le=1.0, description="Window opacity (0.0 to 1.0)")
    z_order: int = Field(..., description="Window Z-order position")
    styles: List[str] = Field(default_factory=list, description="Window styles")
    ex_styles: List[str] = Field(default_factory=list, description="Extended window styles")
    thread_id: Optional[int] = Field(None, description="Thread ID that created the window")
    module_path: Optional[str] = Field(None, description="Path to the executable module")
    icon_path: Optional[str] = Field(None, description="Path to the window icon")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Window creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


class WindowControlRequest(BaseModel):
    """Window control request data model."""
    action: WindowAction = Field(..., description="Action to perform on the window")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")


class WindowMoveRequest(BaseModel):
    """Window move request parameters."""
    x: int = Field(..., description="New X position")
    y: int = Field(..., description="New Y position")


class WindowResizeRequest(BaseModel):
    """Window resize request parameters."""
    width: int = Field(..., ge=1, description="New window width")
    height: int = Field(..., ge=1, description="New window height")


class WindowQuery(BaseModel):
    """Query parameters for window listing."""
    visible_only: bool = Field(False, description="Show only visible windows")
    active_only: bool = Field(False, description="Show only active windows")
    process_id: Optional[int] = Field(None, description="Filter by process ID")
    process_name: Optional[str] = Field(None, description="Filter by process name")
    title_contains: Optional[str] = Field(None, description="Filter by title containing text")
    class_name: Optional[str] = Field(None, description="Filter by window class name")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Result offset for pagination")


class WindowListResponse(BaseModel):
    """Response model for window listing."""
    data: List[WindowInfo] = Field(..., description="List of windows")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
    total: int = Field(..., description="Total number of windows")


class WindowResponse(BaseModel):
    """Response model for single window operations."""
    data: WindowInfo = Field(..., description="Window information")


class WindowControlResponse(BaseModel):
    """Response model for window control operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Operation result message")
    window_id: str = Field(..., description="Window ID that was controlled")
    action: WindowAction = Field(..., description="Action that was performed")


class WindowEvent(BaseModel):
    """Window event data model."""
    event_type: str = Field(..., description="Type of window event")
    window_id: str = Field(..., description="Window ID")
    window_info: Optional[WindowInfo] = Field(None, description="Window information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional event details")


class WindowEventType(str, Enum):
    """Window event type enumeration."""
    CREATED = "window_created"
    DESTROYED = "window_destroyed"
    MOVED = "window_moved"
    RESIZED = "window_resized"
    MINIMIZED = "window_minimized"
    MAXIMIZED = "window_maximized"
    RESTORED = "window_restored"
    FOCUSED = "window_focused"
    UNFOCUSED = "window_unfocused"
    TITLE_CHANGED = "window_title_changed"
    VISIBILITY_CHANGED = "window_visibility_changed"


class WindowFilter(BaseModel):
    """Window filtering criteria."""
    include_system_windows: bool = Field(False, description="Include system windows")
    include_hidden_windows: bool = Field(False, description="Include hidden windows")
    min_width: Optional[int] = Field(None, ge=1, description="Minimum window width")
    min_height: Optional[int] = Field(None, ge=1, description="Minimum window height")
    exclude_process_names: List[str] = Field(default_factory=list, description="Process names to exclude")
    include_process_names: List[str] = Field(default_factory=list, description="Process names to include")
    exclude_class_names: List[str] = Field(default_factory=list, description="Class names to exclude")
    include_class_names: List[str] = Field(default_factory=list, description="Class names to include")


class WindowStatistics(BaseModel):
    """Window statistics data model."""
    total_windows: int = Field(..., description="Total number of windows")
    visible_windows: int = Field(..., description="Number of visible windows")
    hidden_windows: int = Field(..., description="Number of hidden windows")
    minimized_windows: int = Field(..., description="Number of minimized windows")
    maximized_windows: int = Field(..., description="Number of maximized windows")
    active_window_id: Optional[str] = Field(None, description="Currently active window ID")
    top_processes: List[Dict[str, Any]] = Field(default_factory=list, description="Top processes by window count")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Statistics timestamp")


class WindowSnapshot(BaseModel):
    """Window snapshot data model."""
    window_id: str = Field(..., description="Window ID")
    screenshot_path: Optional[str] = Field(None, description="Path to screenshot file")
    screenshot_data: Optional[bytes] = Field(None, description="Screenshot binary data")
    thumbnail_path: Optional[str] = Field(None, description="Path to thumbnail file")
    thumbnail_data: Optional[bytes] = Field(None, description="Thumbnail binary data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Snapshot timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")