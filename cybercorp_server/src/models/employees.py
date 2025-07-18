"""Employee management data models."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class EmployeeType(str, Enum):
    """Employee type enumeration."""
    DEVELOPER = "developer"
    DESIGNER = "designer"
    MANAGER = "manager"
    ANALYST = "analyst"
    TESTER = "tester"
    ADMIN = "admin"


class EmployeeStatus(str, Enum):
    """Employee status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy"
    IDLE = "idle"
    OFFLINE = "offline"


class EmployeeSkill(BaseModel):
    """Employee skill data model."""
    name: str = Field(..., description="Skill name")
    level: int = Field(..., ge=1, le=10, description="Skill level (1-10)")
    experience: int = Field(..., ge=0, description="Experience in months")


class EmployeeConfig(BaseModel):
    """Employee configuration data model."""
    work_hours: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Work hours by day of week"
    )
    skills: List[EmployeeSkill] = Field(
        default_factory=list,
        description="Employee skills"
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Employee preferences"
    )
    performance_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Performance metrics"
    )


class Employee(BaseModel):
    """Employee data model."""
    id: str = Field(..., description="Unique employee identifier")
    name: str = Field(..., description="Employee name")
    type: EmployeeType = Field(..., description="Employee type")
    status: EmployeeStatus = Field(..., description="Current employee status")
    email: Optional[str] = Field(None, description="Employee email")
    department: Optional[str] = Field(None, description="Employee department")
    position: Optional[str] = Field(None, description="Employee position")
    manager_id: Optional[str] = Field(None, description="Manager employee ID")
    config: EmployeeConfig = Field(
        default_factory=EmployeeConfig,
        description="Employee configuration"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Employee creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update time"
    )


class EmployeeCreate(BaseModel):
    """Employee creation request data model."""
    name: str = Field(..., description="Employee name")
    type: EmployeeType = Field(..., description="Employee type")
    email: Optional[str] = Field(None, description="Employee email")
    department: Optional[str] = Field(None, description="Employee department")
    position: Optional[str] = Field(None, description="Employee position")
    manager_id: Optional[str] = Field(None, description="Manager employee ID")
    config: Optional[EmployeeConfig] = Field(None, description="Employee configuration")


class EmployeeUpdate(BaseModel):
    """Employee update request data model."""
    name: Optional[str] = Field(None, description="Employee name")
    type: Optional[EmployeeType] = Field(None, description="Employee type")
    status: Optional[EmployeeStatus] = Field(None, description="Current employee status")
    email: Optional[str] = Field(None, description="Employee email")
    department: Optional[str] = Field(None, description="Employee department")
    position: Optional[str] = Field(None, description="Employee position")
    manager_id: Optional[str] = Field(None, description="Manager employee ID")
    config: Optional[Dict[str, Any]] = Field(None, description="Employee configuration")


class EmployeeQuery(BaseModel):
    """Query parameters for employee listing."""
    type: Optional[EmployeeType] = Field(None, description="Filter by employee type")
    status: Optional[EmployeeStatus] = Field(None, description="Filter by employee status")
    department: Optional[str] = Field(None, description="Filter by department")
    manager_id: Optional[str] = Field(None, description="Filter by manager ID")
    name_contains: Optional[str] = Field(None, description="Filter by name containing text")
    skill: Optional[str] = Field(None, description="Filter by skill name")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Result offset for pagination")


class EmployeeListResponse(BaseModel):
    """Response model for employee listing."""
    data: List[Employee] = Field(..., description="List of employees")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
    total: int = Field(..., description="Total number of employees")


class EmployeeStatusUpdate(BaseModel):
    """Employee status update request data model."""
    status: EmployeeStatus = Field(..., description="New employee status")
    reason: Optional[str] = Field(None, description="Reason for status change")


class EmployeePerformanceMetrics(BaseModel):
    """Employee performance metrics data model."""
    employee_id: str = Field(..., description="Employee ID")
    metrics: Dict[str, float] = Field(..., description="Performance metrics")
    period_start: datetime = Field(..., description="Period start time")
    period_end: datetime = Field(..., description="Period end time")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")