"""Windows management router for CyberCorp Server."""

from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models.windows import WindowInfo, WindowAction, WindowFilter, WindowControlRequest
from ..models.auth import User, PermissionScope
from ..auth import get_current_user, require_permission
from ..windows import windows_manager
from ..logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=Dict[str, Any])
async def list_windows(
    visible_only: bool = Query(default=False, description="Show only visible windows"),
    active_only: bool = Query(default=False, description="Show only active windows"),
    process_id: Optional[int] = Query(None, description="Filter by process ID"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    page: int = Query(default=1, ge=1, description="Page number"),
    current_user: User = Depends(require_permission(PermissionScope.WINDOWS_READ))
) -> Dict[str, Any]:
    """List all windows."""
    try:
        logger.info(f"Windows list request by: {current_user.username}")
        
        # Create filter
        window_filter = WindowFilter(
            visible_only=visible_only,
            active_only=active_only,
            process_id=process_id,
            limit=limit,
            page=page
        )
        
        # Get windows
        windows = await windows_manager.list_windows(window_filter)
        
        return {
            "data": windows,
            "pagination": {
                "total": len(windows),
                "page": page,
                "per_page": limit,
                "pages": (len(windows) + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Windows list error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve windows"
        )


@router.get("/{window_id}", response_model=WindowInfo)
async def get_window(
    window_id: str,
    current_user: User = Depends(require_permission(PermissionScope.WINDOWS_READ))
) -> WindowInfo:
    """Get window details."""
    try:
        logger.info(f"Window get request for {window_id} by: {current_user.username}")
        
        # Get window
        window = await windows_manager.get_window(window_id)
        if not window:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Window not found"
            )
        
        return window
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Window get error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve window"
        )


@router.post("/{window_id}/control", response_model=Dict[str, Any])
async def control_window(
    window_id: str,
    control_request: WindowControlRequest,
    current_user: User = Depends(require_permission(PermissionScope.WINDOWS_WRITE))
) -> Dict[str, Any]:
    """Control window (focus, minimize, maximize, etc.)."""
    try:
        logger.info(
            f"Window control request for {window_id} "
            f"action: {control_request.action} by: {current_user.username}"
        )
        
        # Control window
        result = await windows_manager.control_window(
            window_id=window_id,
            action=control_request.action,
            parameters=control_request.parameters
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Window control failed")
            )
        
        logger.info(
            f"Window {window_id} {control_request.action} "
            f"completed successfully by {current_user.username}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Window control error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to control window"
        )


@router.post("/{window_id}/focus", response_model=Dict[str, Any])
async def focus_window(
    window_id: str,
    current_user: User = Depends(require_permission(PermissionScope.WINDOWS_WRITE))
) -> Dict[str, Any]:
    """Focus window."""
    try:
        logger.info(f"Window focus request for {window_id} by: {current_user.username}")
        
        # Focus window
        result = await windows_manager.focus_window(window_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to focus window")
            )
        
        logger.info(f"Window {window_id} focused successfully by {current_user.username}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Window focus error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to focus window"
        )


@router.post("/{window_id}/minimize", response_model=Dict[str, Any])
async def minimize_window(
    window_id: str,
    current_user: User = Depends(require_permission(PermissionScope.WINDOWS_WRITE))
) -> Dict[str, Any]:
    """Minimize window."""
    try:
        logger.info(f"Window minimize request for {window_id} by: {current_user.username}")
        
        # Minimize window
        result = await windows_manager.minimize_window(window_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to minimize window")
            )
        
        logger.info(f"Window {window_id} minimized successfully by {current_user.username}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Window minimize error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to minimize window"
        )


@router.post("/{window_id}/maximize", response_model=Dict[str, Any])
async def maximize_window(
    window_id: str,
    current_user: User = Depends(require_permission(PermissionScope.WINDOWS_WRITE))
) -> Dict[str, Any]:
    """Maximize window."""
    try:
        logger.info(f"Window maximize request for {window_id} by: {current_user.username}")
        
        # Maximize window
        result = await windows_manager.maximize_window(window_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to maximize window")
            )
        
        logger.info(f"Window {window_id} maximized successfully by {current_user.username}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Window maximize error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to maximize window"
        )


@router.post("/{window_id}/restore", response_model=Dict[str, Any])
async def restore_window(
    window_id: str,
    current_user: User = Depends(require_permission(PermissionScope.WINDOWS_WRITE))
) -> Dict[str, Any]:
    """Restore window."""
    try:
        logger.info(f"Window restore request for {window_id} by: {current_user.username}")
        
        # Restore window
        result = await windows_manager.restore_window(window_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to restore window")
            )
        
        logger.info(f"Window {window_id} restored successfully by {current_user.username}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Window restore error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore window"
        )


@router.post("/{window_id}/close", response_model=Dict[str, Any])
async def close_window(
    window_id: str,
    force: bool = Query(default=False, description="Force close window"),
    current_user: User = Depends(require_permission(PermissionScope.WINDOWS_WRITE))
) -> Dict[str, Any]:
    """Close window."""
    try:
        logger.info(f"Window close request for {window_id} by: {current_user.username}")
        
        # Close window
        result = await windows_manager.close_window(window_id, force=force)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to close window")
            )
        
        logger.info(f"Window {window_id} closed successfully by {current_user.username}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Window close error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close window"
        )


@router.put("/{window_id}/bounds", response_model=Dict[str, Any])
async def move_resize_window(
    window_id: str,
    x: int = Query(..., description="X coordinate"),
    y: int = Query(..., description="Y coordinate"),
    width: int = Query(..., description="Width"),
    height: int = Query(..., description="Height"),
    current_user: User = Depends(require_permission(PermissionScope.WINDOWS_WRITE))
) -> Dict[str, Any]:
    """Move and resize window."""
    try:
        logger.info(
            f"Window move/resize request for {window_id} "
            f"to ({x}, {y}) {width}x{height} by: {current_user.username}"
        )
        
        # Move and resize window
        result = await windows_manager.move_resize_window(
            window_id=window_id,
            x=x,
            y=y,
            width=width,
            height=height
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to move/resize window")
            )
        
        logger.info(
            f"Window {window_id} moved/resized successfully by {current_user.username}"
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Window move/resize error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to move/resize window"
        )


@router.get("/{window_id}/screenshot")
async def get_window_screenshot(
    window_id: str,
    format: str = Query(default="png", pattern="^(png|jpg|jpeg)$"),
    quality: int = Query(default=80, ge=1, le=100, description="Image quality (1-100)"),
    current_user: User = Depends(require_permission(PermissionScope.WINDOWS_READ))
) -> Dict[str, Any]:
    """Get window screenshot."""
    try:
        logger.info(f"Window screenshot request for {window_id} by: {current_user.username}")
        
        # Get screenshot
        screenshot = await windows_manager.get_window_screenshot(
            window_id=window_id,
            format=format,
            quality=quality
        )
        
        return {
            "success": True,
            "data": screenshot
        }
        
    except Exception as e:
        logger.error(f"Window screenshot error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get window screenshot"
        )


@router.get("/process/{process_id}")
async def get_process_windows(
    process_id: int,
    current_user: User = Depends(require_permission(PermissionScope.WINDOWS_READ))
) -> Dict[str, Any]:
    """Get all windows for a specific process."""
    try:
        logger.info(f"Process windows request for PID {process_id} by: {current_user.username}")
        
        # Get process windows
        windows = await windows_manager.get_process_windows(process_id)
        
        return {
            "data": windows,
            "process_id": process_id,
            "count": len(windows)
        }
        
    except Exception as e:
        logger.error(f"Process windows error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve process windows"
        )


@router.get("/active")
async def get_active_window(
    current_user: User = Depends(require_permission(PermissionScope.WINDOWS_READ))
) -> Dict[str, Any]:
    """Get currently active window."""
    try:
        logger.info(f"Active window request by: {current_user.username}")
        
        # Get active window
        window = await windows_manager.get_active_window()
        
        return {
            "data": window,
            "active": window is not None
        }
        
    except Exception as e:
        logger.error(f"Active window error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active window"
        )