"""Task management data models."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class TaskPriority(int, Enum):
    """Task priority enumeration."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskType(str, Enum):
    """Task type enumeration."""
    DEVELOPMENT = "development"
    DESIGN = "design"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"
    MAINTENANCE = "maintenance"
    DEPLOYMENT = "deployment"
    OTHER = "other"


class TaskDependency(BaseModel):
    """Task dependency data model."""
    task_id: str = Field(..., description="Dependent task ID")
    type: str = Field(..., description="Dependency type (e.g., 'blocks', 'requires')")
    description: Optional[str] = Field(None, description="Dependency description")


class TaskAttachment(BaseModel):
    """Task attachment data model."""
    id: str = Field(..., description="Attachment ID")
    name: str = Field(..., description="Attachment name")
    type: str = Field(..., description="Attachment type")
    url: str = Field(..., description="Attachment URL")
    size: int = Field(..., description="Attachment size in bytes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")


class TaskComment(BaseModel):
    """Task comment data model."""
    id: str = Field(..., description="Comment ID")
    task_id: str = Field(..., description="Task ID")
    user_id: str = Field(..., description="User ID")
    content: str = Field(..., description="Comment content")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")


class TaskMetrics(BaseModel):
    """Task metrics data model."""
    estimated_hours: Optional[float] = Field(None, description="Estimated hours")
    actual_hours: Optional[float] = Field(None, description="Actual hours spent")
    progress_percentage: Optional[int] = Field(
        None, ge=0, le=100, description="Progress percentage"
    )
    complexity_score: Optional[int] = Field(
        None, ge=1, le=10, description="Complexity score (1-10)"
    )


class Task(BaseModel):
    """Task data model."""
    id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Task name")
    description: str = Field(..., description="Task description")
    type: TaskType = Field(..., description="Task type")
    status: TaskStatus = Field(..., description="Current task status")
    priority: TaskPriority = Field(..., description="Task priority")
    assigned_to: Optional[str] = Field(None, description="Assigned employee ID")
    created_by: str = Field(..., description="Creator employee ID")
    project_id: Optional[str] = Field(None, description="Project ID")
    dependencies: List[TaskDependency] = Field(
        default_factory=list, description="Task dependencies"
    )
    attachments: List[TaskAttachment] = Field(
        default_factory=list, description="Task attachments"
    )
    tags: List[str] = Field(default_factory=list, description="Task tags")
    metrics: TaskMetrics = Field(default_factory=TaskMetrics, description="Task metrics")
    due_date: Optional[datetime] = Field(None, description="Due date")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Task creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update time"
    )
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")


class TaskCreate(BaseModel):
    """Task creation request data model."""
    name: str = Field(..., description="Task name")
    description: str = Field(..., description="Task description")
    type: TaskType = Field(..., description="Task type")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    assigned_to: Optional[str] = Field(None, description="Assigned employee ID")
    project_id: Optional[str] = Field(None, description="Project ID")
    dependencies: Optional[List[TaskDependency]] = Field(None, description="Task dependencies")
    tags: Optional[List[str]] = Field(None, description="Task tags")
    metrics: Optional[TaskMetrics] = Field(None, description="Task metrics")
    due_date: Optional[datetime] = Field(None, description="Due date")


class TaskUpdate(BaseModel):
    """Task update request data model."""
    name: Optional[str] = Field(None, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    type: Optional[TaskType] = Field(None, description="Task type")
    status: Optional[TaskStatus] = Field(None, description="Current task status")
    priority: Optional[TaskPriority] = Field(None, description="Task priority")
    assigned_to: Optional[str] = Field(None, description="Assigned employee ID")
    project_id: Optional[str] = Field(None, description="Project ID")
    dependencies: Optional[List[TaskDependency]] = Field(None, description="Task dependencies")
    tags: Optional[List[str]] = Field(None, description="Task tags")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Task metrics")
    due_date: Optional[datetime] = Field(None, description="Due date")


class TaskQuery(BaseModel):
    """Query parameters for task listing."""
    type: Optional[TaskType] = Field(None, description="Filter by task type")
    status: Optional[TaskStatus] = Field(None, description="Filter by task status")
    priority: Optional[TaskPriority] = Field(None, description="Filter by task priority")
    assigned_to: Optional[str] = Field(None, description="Filter by assigned employee ID")
    created_by: Optional[str] = Field(None, description="Filter by creator employee ID")
    project_id: Optional[str] = Field(None, description="Filter by project ID")
    tag: Optional[str] = Field(None, description="Filter by tag")
    name_contains: Optional[str] = Field(None, description="Filter by name containing text")
    due_before: Optional[datetime] = Field(None, description="Filter by due date before")
    due_after: Optional[datetime] = Field(None, description="Filter by due date after")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date before")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date after")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Result offset for pagination")


class TaskListResponse(BaseModel):
    """Response model for task listing."""
    data: List[Task] = Field(..., description="List of tasks")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
    total: int = Field(..., description="Total number of tasks")


class TaskStatusUpdate(BaseModel):
    """Task status update request data model."""
    status: TaskStatus = Field(..., description="New task status")
    reason: Optional[str] = Field(None, description="Reason for status change")
    progress_percentage: Optional[int] = Field(
        None, ge=0, le=100, description="Progress percentage"
    )


class TaskAssignRequest(BaseModel):
    """Task assignment request data model."""
    employee_id: str = Field(..., description="Employee ID to assign the task to")
    message: Optional[str] = Field(None, description="Assignment message")


class TaskExecuteRequest(BaseModel):
    """Task execution request data model."""
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Execution parameters")
    timeout: Optional[int] = Field(None, description="Execution timeout in seconds")