"""Process management router for CyberCorp Server."""

from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models.processes import ProcessInfo, ProcessFilter, ProcessControlRequest, ProcessCreateRequest
from ..models.auth import User, PermissionScope
from ..auth import get_current_user, require_permission
from ..processes import processes_manager
from ..logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=Dict[str, Any])
async def list_processes(
    name: Optional[str] = Query(None, description="Filter by process name"),
    pid: Optional[int] = Query(None, description="Filter by process ID"),
    parent_pid: Optional[int] = Query(None, description="Filter by parent process ID"),
    user: Optional[str] = Query(None, description="Filter by username"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    page: int = Query(default=1, ge=1, description="Page number"),
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_READ))
) -> Dict[str, Any]:
    """List all processes."""
    try:
        logger.info(f"Processes list request by: {current_user.username}")
        
        # Create filter
        process_filter = ProcessFilter(
            name=name,
            pid=pid,
            parent_pid=parent_pid,
            user=user,
            status=status_filter,
            limit=limit,
            page=page
        )
        
        # Get processes
        processes = await processes_manager.list_processes(process_filter)
        
        return {
            "data": processes,
            "pagination": {
                "total": len(processes),
                "page": page,
                "per_page": limit,
                "pages": (len(processes) + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Processes list error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve processes"
        )


@router.get("/{process_id}", response_model=ProcessInfo)
async def get_process(
    process_id: int,
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_READ))
) -> ProcessInfo:
    """Get process details."""
    try:
        logger.info(f"Process get request for {process_id} by: {current_user.username}")
        
        # Get process
        process = await processes_manager.get_process(process_id)
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process not found"
            )
        
        return process
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process get error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve process"
        )


@router.post("/{process_id}/control", response_model=Dict[str, Any])
async def control_process(
    process_id: int,
    control_request: ProcessControlRequest,
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_WRITE))
) -> Dict[str, Any]:
    """Control process (terminate, suspend, resume, etc.)."""
    try:
        logger.info(
            f"Process control request for {process_id} "
            f"action: {control_request.action} by: {current_user.username}"
        )
        
        # Control process
        result = await processes_manager.control_process(
            process_id=process_id,
            action=control_request.action,
            parameters=control_request.parameters
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Process control failed")
            )
        
        logger.info(
            f"Process {process_id} {control_request.action} "
            f"completed successfully by {current_user.username}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process control error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to control process"
        )


@router.post("/{process_id}/terminate", response_model=Dict[str, Any])
async def terminate_process(
    process_id: int,
    force: bool = Query(default=False, description="Force terminate process"),
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_WRITE))
) -> Dict[str, Any]:
    """Terminate process."""
    try:
        logger.info(f"Process terminate request for {process_id} by: {current_user.username}")
        
        # Terminate process
        result = await processes_manager.terminate_process(process_id, force=force)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to terminate process")
            )
        
        logger.info(f"Process {process_id} terminated successfully by {current_user.username}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process terminate error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to terminate process"
        )


@router.post("/{process_id}/suspend", response_model=Dict[str, Any])
async def suspend_process(
    process_id: int,
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_WRITE))
) -> Dict[str, Any]:
    """Suspend process."""
    try:
        logger.info(f"Process suspend request for {process_id} by: {current_user.username}")
        
        # Suspend process
        result = await processes_manager.suspend_process(process_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to suspend process")
            )
        
        logger.info(f"Process {process_id} suspended successfully by {current_user.username}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process suspend error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend process"
        )


@router.post("/{process_id}/resume", response_model=Dict[str, Any])
async def resume_process(
    process_id: int,
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_WRITE))
) -> Dict[str, Any]:
    """Resume suspended process."""
    try:
        logger.info(f"Process resume request for {process_id} by: {current_user.username}")
        
        # Resume process
        result = await processes_manager.resume_process(process_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to resume process")
            )
        
        logger.info(f"Process {process_id} resumed successfully by {current_user.username}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process resume error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume process"
        )


@router.post("/create", response_model=Dict[str, Any])
async def create_process(
    create_request: ProcessCreateRequest,
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_WRITE))
) -> Dict[str, Any]:
    """Create new process."""
    try:
        logger.info(
            f"Process create request for {create_request.command} "
            f"by: {current_user.username}"
        )
        
        # Create process
        result = await processes_manager.create_process(
            command=create_request.command,
            arguments=create_request.arguments,
            working_directory=create_request.working_directory,
            environment=create_request.environment,
            wait_for_completion=create_request.wait_for_completion,
            timeout=create_request.timeout
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Process creation failed")
            )
        
        logger.info(
            f"Process created successfully with PID {result.get('pid')} "
            f"by {current_user.username}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process create error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create process"
        )


@router.get("/{process_id}/children", response_model=Dict[str, Any])
async def get_process_children(
    process_id: int,
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_READ))
) -> Dict[str, Any]:
    """Get child processes."""
    try:
        logger.info(f"Process children request for {process_id} by: {current_user.username}")
        
        # Get child processes
        children = await processes_manager.get_process_children(process_id)
        
        return {
            "data": children,
            "parent_id": process_id,
            "count": len(children)
        }
        
    except Exception as e:
        logger.error(f"Process children error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve process children"
        )


@router.get("/{process_id}/threads", response_model=Dict[str, Any])
async def get_process_threads(
    process_id: int,
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_READ))
) -> Dict[str, Any]:
    """Get process threads."""
    try:
        logger.info(f"Process threads request for {process_id} by: {current_user.username}")
        
        # Get process threads
        threads = await processes_manager.get_process_threads(process_id)
        
        return {
            "data": threads,
            "process_id": process_id,
            "count": len(threads)
        }
        
    except Exception as e:
        logger.error(f"Process threads error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve process threads"
        )


@router.get("/{process_id}/modules", response_model=Dict[str, Any])
async def get_process_modules(
    process_id: int,
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_READ))
) -> Dict[str, Any]:
    """Get process loaded modules."""
    try:
        logger.info(f"Process modules request for {process_id} by: {current_user.username}")
        
        # Get process modules
        modules = await processes_manager.get_process_modules(process_id)
        
        return {
            "data": modules,
            "process_id": process_id,
            "count": len(modules)
        }
        
    except Exception as e:
        logger.error(f"Process modules error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve process modules"
        )


@router.get("/{process_id}/environment", response_model=Dict[str, Any])
async def get_process_environment(
    process_id: int,
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_READ))
) -> Dict[str, Any]:
    """Get process environment variables."""
    try:
        logger.info(f"Process environment request for {process_id} by: {current_user.username}")
        
        # Get process environment
        environment = await processes_manager.get_process_environment(process_id)
        
        return {
            "data": environment,
            "process_id": process_id
        }
        
    except Exception as e:
        logger.error(f"Process environment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve process environment"
        )


@router.get("/tree", response_model=Dict[str, Any])
async def get_process_tree(
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_READ))
) -> Dict[str, Any]:
    """Get process tree."""
    try:
        logger.info(f"Process tree request by: {current_user.username}")
        
        # Get process tree
        tree = await processes_manager.get_process_tree()
        
        return {
            "data": tree,
            "count": len(tree)
        }
        
    except Exception as e:
        logger.error(f"Process tree error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve process tree"
        )


@router.get("/current", response_model=Dict[str, Any])
async def get_current_process(
    current_user: User = Depends(require_permission(PermissionScope.PROCESSES_READ))
) -> Dict[str, Any]:
    """Get current process information."""
    try:
        logger.info(f"Current process request by: {current_user.username}")
        
        # Get current process
        process = await processes_manager.get_current_process()
        
        return {
            "data": process
        }
        
    except Exception as e:
        logger.error(f"Current process error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve current process"
        )