"""Employee management router for CyberCorp Server."""

from typing import Dict, Any, Optional, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models.employees import (
    Employee, EmployeeCreate, EmployeeUpdate, EmployeeType,
    EmployeeStatus, EmployeeStatusUpdate, EmployeeQuery
)
from ..models.auth import User, PermissionScope
from ..auth import get_current_user, require_permission
from ..employees import employee_manager
from ..logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=Dict[str, Any])
async def list_employees(
    type: Optional[EmployeeType] = Query(None, description="Filter by employee type"),
    status: Optional[EmployeeStatus] = Query(None, description="Filter by employee status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    manager_id: Optional[str] = Query(None, description="Filter by manager ID"),
    name_contains: Optional[str] = Query(None, description="Filter by name containing text"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    page: int = Query(default=1, ge=1, description="Page number"),
    current_user: User = Depends(require_permission("employees.read"))
) -> Dict[str, Any]:
    """List all employees."""
    try:
        logger.info(f"Employees list request by: {current_user.username}")
        
        # Create query
        employee_query = EmployeeQuery(
            type=type,
            status=status,
            department=department,
            manager_id=manager_id,
            name_contains=name_contains,
            limit=limit,
            offset=(page - 1) * limit
        )
        
        # Get employees
        employees = await employee_manager.list_employees(employee_query)
        total = await employee_manager.count_employees(employee_query)
        
        return {
            "data": employees,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": limit,
                "pages": (total + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Employees list error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve employees"
        )


@router.post("", response_model=Employee, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_create: EmployeeCreate,
    current_user: User = Depends(require_permission("employees.write"))
) -> Employee:
    """Create a new employee."""
    try:
        logger.info(f"Employee create request by: {current_user.username}")
        
        # Generate employee ID
        employee_id = str(uuid4())
        
        # Create employee
        employee = Employee(
            id=employee_id,
            name=employee_create.name,
            type=employee_create.type,
            status=EmployeeStatus.INACTIVE,  # Default status
            email=employee_create.email,
            department=employee_create.department,
            position=employee_create.position,
            manager_id=employee_create.manager_id,
            config=employee_create.config or {}
        )
        
        # Save employee
        created_employee = await employee_manager.create_employee(employee)
        
        return created_employee
        
    except Exception as e:
        logger.error(f"Employee create error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create employee"
        )


@router.get("/{employee_id}", response_model=Employee)
async def get_employee(
    employee_id: str,
    current_user: User = Depends(require_permission("employees.read"))
) -> Employee:
    """Get employee details."""
    try:
        logger.info(f"Employee get request for {employee_id} by: {current_user.username}")
        
        # Get employee
        employee = await employee_manager.get_employee(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        return employee
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Employee get error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve employee"
        )


@router.put("/{employee_id}", response_model=Employee)
async def update_employee(
    employee_id: str,
    employee_update: EmployeeUpdate,
    current_user: User = Depends(require_permission("employees.write"))
) -> Employee:
    """Update employee details."""
    try:
        logger.info(f"Employee update request for {employee_id} by: {current_user.username}")
        
        # Get existing employee
        existing_employee = await employee_manager.get_employee(employee_id)
        if not existing_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Update employee
        updated_employee = await employee_manager.update_employee(employee_id, employee_update)
        
        return updated_employee
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Employee update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employee"
        )


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: str,
    current_user: User = Depends(require_permission("employees.write"))
) -> None:
    """Delete an employee."""
    try:
        logger.info(f"Employee delete request for {employee_id} by: {current_user.username}")
        
        # Get existing employee
        existing_employee = await employee_manager.get_employee(employee_id)
        if not existing_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Delete employee
        await employee_manager.delete_employee(employee_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Employee delete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete employee"
        )


@router.patch("/{employee_id}/status", response_model=Employee)
async def update_employee_status(
    employee_id: str,
    status_update: EmployeeStatusUpdate,
    current_user: User = Depends(require_permission("employees.write"))
) -> Employee:
    """Update employee status."""
    try:
        logger.info(
            f"Employee status update request for {employee_id} "
            f"status: {status_update.status} by: {current_user.username}"
        )
        
        # Get existing employee
        existing_employee = await employee_manager.get_employee(employee_id)
        if not existing_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Update employee status
        updated_employee = await employee_manager.update_employee_status(
            employee_id, status_update.status, status_update.reason
        )
        
        return updated_employee
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Employee status update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employee status"
        )


@router.get("/{employee_id}/tasks", response_model=Dict[str, Any])
async def get_employee_tasks(
    employee_id: str,
    status: Optional[str] = Query(None, description="Filter by task status"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    page: int = Query(default=1, ge=1, description="Page number"),
    current_user: User = Depends(require_permission("employees.read"))
) -> Dict[str, Any]:
    """Get tasks assigned to an employee."""
    try:
        logger.info(f"Employee tasks request for {employee_id} by: {current_user.username}")
        
        # Get existing employee
        existing_employee = await employee_manager.get_employee(employee_id)
        if not existing_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Get employee tasks
        tasks, total = await employee_manager.get_employee_tasks(
            employee_id, status, limit, (page - 1) * limit
        )
        
        return {
            "data": tasks,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": limit,
                "pages": (total + limit - 1) // limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Employee tasks error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve employee tasks"
        )


@router.get("/{employee_id}/performance", response_model=Dict[str, Any])
async def get_employee_performance(
    employee_id: str,
    period: str = Query("month", description="Performance period (day, week, month, year)"),
    current_user: User = Depends(require_permission("employees.read"))
) -> Dict[str, Any]:
    """Get employee performance metrics."""
    try:
        logger.info(f"Employee performance request for {employee_id} by: {current_user.username}")
        
        # Get existing employee
        existing_employee = await employee_manager.get_employee(employee_id)
        if not existing_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Get employee performance
        performance = await employee_manager.get_employee_performance(employee_id, period)
        
        return {
            "data": performance,
            "period": period
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Employee performance error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve employee performance"
        )