"""Task management router for CyberCorp Server."""

from typing import Dict, Any, Optional, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models.tasks import (
    Task, TaskCreate, TaskUpdate, TaskType, TaskStatus,
    TaskStatusUpdate, TaskAssignRequest, TaskExecuteRequest, TaskQuery
)
from ..models.auth import User, PermissionScope
from ..auth import get_current_user, require_permission
from ..tasks import task_manager
from ..logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=Dict[str, Any])
async def list_tasks(
    type: Optional[TaskType] = Query(None, description="Filter by task type"),
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned employee ID"),
    created_by: Optional[str] = Query(None, description="Filter by creator employee ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    name_contains: Optional[str] = Query(None, description="Filter by name containing text"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    page: int = Query(default=1, ge=1, description="Page number"),
    current_user: User = Depends(require_permission(PermissionScope.TASKS_READ))
) -> Dict[str, Any]:
    """List all tasks."""
    try:
        logger.info(f"Tasks list request by: {current_user.username}")
        
        # Create query
        task_query = TaskQuery(
            type=type,
            status=status,
            assigned_to=assigned_to,
            created_by=created_by,
            project_id=project_id,
            tag=tag,
            name_contains=name_contains,
            limit=limit,
            offset=(page - 1) * limit
        )
        
        # Get tasks
        tasks = await task_manager.list_tasks(task_query)
        total = await task_manager.count_tasks(task_query)
        
        return {
            "data": tasks,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": limit,
                "pages": (total + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Tasks list error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks"
        )


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_create: TaskCreate,
    current_user: User = Depends(require_permission(PermissionScope.TASKS_WRITE))
) -> Task:
    """Create a new task."""
    try:
        logger.info(f"Task create request by: {current_user.username}")
        
        # Generate task ID
        task_id = str(uuid4())
        
        # Create task
        task = Task(
            id=task_id,
            name=task_create.name,
            description=task_create.description,
            type=task_create.type,
            status=TaskStatus.PENDING,  # Default status
            priority=task_create.priority,
            assigned_to=task_create.assigned_to,
            created_by=current_user.id,
            project_id=task_create.project_id,
            dependencies=task_create.dependencies or [],
            tags=task_create.tags or [],
            metrics=task_create.metrics or {},
            due_date=task_create.due_date
        )
        
        # Save task
        created_task = await task_manager.create_task(task)
        
        return created_task
        
    except Exception as e:
        logger.error(f"Task create error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    current_user: User = Depends(require_permission(PermissionScope.TASKS_READ))
) -> Task:
    """Get task details."""
    try:
        logger.info(f"Task get request for {task_id} by: {current_user.username}")
        
        # Get task
        task = await task_manager.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task get error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task"
        )


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    current_user: User = Depends(require_permission(PermissionScope.TASKS_WRITE))
) -> Task:
    """Update task details."""
    try:
        logger.info(f"Task update request for {task_id} by: {current_user.username}")
        
        # Get existing task
        existing_task = await task_manager.get_task(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Update task
        updated_task = await task_manager.update_task(task_id, task_update)
        
        return updated_task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task"
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: User = Depends(require_permission(PermissionScope.TASKS_WRITE))
) -> None:
    """Delete a task."""
    try:
        logger.info(f"Task delete request for {task_id} by: {current_user.username}")
        
        # Get existing task
        existing_task = await task_manager.get_task(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Delete task
        await task_manager.delete_task(task_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task delete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task"
        )


@router.patch("/{task_id}/status", response_model=Task)
async def update_task_status(
    task_id: str,
    status_update: TaskStatusUpdate,
    current_user: User = Depends(require_permission(PermissionScope.TASKS_WRITE))
) -> Task:
    """Update task status."""
    try:
        logger.info(
            f"Task status update request for {task_id} "
            f"status: {status_update.status} by: {current_user.username}"
        )
        
        # Get existing task
        existing_task = await task_manager.get_task(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Update task status
        updated_task = await task_manager.update_task_status(
            task_id, status_update.status, status_update.reason, status_update.progress_percentage
        )
        
        return updated_task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task status update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task status"
        )


@router.post("/{task_id}/assign", response_model=Task)
async def assign_task(
    task_id: str,
    assign_request: TaskAssignRequest,
    current_user: User = Depends(require_permission(PermissionScope.TASKS_WRITE))
) -> Task:
    """Assign task to an employee."""
    try:
        logger.info(
            f"Task assign request for {task_id} "
            f"to employee: {assign_request.employee_id} by: {current_user.username}"
        )
        
        # Get existing task
        existing_task = await task_manager.get_task(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Assign task
        assigned_task = await task_manager.assign_task(
            task_id, assign_request.employee_id, assign_request.message
        )
        
        return assigned_task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task assign error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign task"
        )


@router.post("/{task_id}/execute", response_model=Dict[str, Any])
async def execute_task(
    task_id: str,
    execute_request: TaskExecuteRequest,
    current_user: User = Depends(require_permission(PermissionScope.TASKS_EXECUTE))
) -> Dict[str, Any]:
    """Execute a task."""
    try:
        logger.info(f"Task execute request for {task_id} by: {current_user.username}")
        
        # Get existing task
        existing_task = await task_manager.get_task(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Execute task
        execution_result = await task_manager.execute_task(
            task_id, execute_request.parameters, execute_request.timeout
        )
        
        return {
            "task_id": task_id,
            "execution_id": execution_result.get("execution_id"),
            "status": execution_result.get("status"),
            "result": execution_result.get("result"),
            "started_at": execution_result.get("started_at"),
            "completed_at": execution_result.get("completed_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task execute error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute task"
        )


@router.get("/{task_id}/history", response_model=Dict[str, Any])
async def get_task_history(
    task_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    page: int = Query(default=1, ge=1, description="Page number"),
    current_user: User = Depends(require_permission(PermissionScope.TASKS_READ))
) -> Dict[str, Any]:
    """Get task history."""
    try:
        logger.info(f"Task history request for {task_id} by: {current_user.username}")
        
        # Get existing task
        existing_task = await task_manager.get_task(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Get task history
        history, total = await task_manager.get_task_history(
            task_id, limit, (page - 1) * limit
        )
        
        return {
            "data": history,
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
        logger.error(f"Task history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task history"
        )


@router.get("/{task_id}/comments", response_model=Dict[str, Any])
async def get_task_comments(
    task_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    page: int = Query(default=1, ge=1, description="Page number"),
    current_user: User = Depends(require_permission(PermissionScope.TASKS_READ))
) -> Dict[str, Any]:
    """Get task comments."""
    try:
        logger.info(f"Task comments request for {task_id} by: {current_user.username}")
        
        # Get existing task
        existing_task = await task_manager.get_task(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Get task comments
        comments, total = await task_manager.get_task_comments(
            task_id, limit, (page - 1) * limit
        )
        
        return {
            "data": comments,
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
        logger.error(f"Task comments error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task comments"
        )


@router.post("/{task_id}/comments", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def add_task_comment(
    task_id: str,
    comment: Dict[str, Any],
    current_user: User = Depends(require_permission(PermissionScope.TASKS_WRITE))
) -> Dict[str, Any]:
    """Add a comment to a task."""
    try:
        logger.info(f"Task comment add request for {task_id} by: {current_user.username}")
        
        # Get existing task
        existing_task = await task_manager.get_task(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Add comment
        comment_id = str(uuid4())
        created_comment = await task_manager.add_task_comment(
            task_id, comment_id, current_user.id, comment.get("content")
        )
        
        return created_comment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task comment add error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add task comment"
        )