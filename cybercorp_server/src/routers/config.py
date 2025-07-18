"""Configuration management router for CyberCorp Server."""

from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models.auth import User, PermissionScope
from ..auth import get_current_user, require_permission
from ..config import config_manager
from ..logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=Dict[str, Any])
async def get_config(
    section: Optional[str] = Query(None, description="Configuration section"),
    key: Optional[str] = Query(None, description="Configuration key"),
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_READ))
) -> Dict[str, Any]:
    """Get configuration."""
    try:
        logger.info(f"Config get request by: {current_user.username}")
        
        # Get configuration
        if section and key:
            value = config_manager.get(section, key)
            return {
                "section": section,
                "key": key,
                "value": value
            }
        elif section:
            config = config_manager.get_section(section)
            return {
                "section": section,
                "config": config
            }
        else:
            config = config_manager.get_all()
            return {
                "config": config
            }
        
    except Exception as e:
        logger.error(f"Config get error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration"
        )


@router.put("", response_model=Dict[str, Any])
async def update_config(
    section: str,
    key: str,
    value: Any,
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_WRITE))
) -> Dict[str, Any]:
    """Update configuration."""
    try:
        logger.info(
            f"Config update request: {section}.{key} = {value} "
            f"by: {current_user.username}"
        )
        
        # Update configuration
        result = await config_manager.set(section, key, value)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Configuration update failed")
            )
        
        logger.info(
            f"Configuration {section}.{key} updated successfully "
            f"by {current_user.username}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration"
        )


@router.put("/section", response_model=Dict[str, Any])
async def update_config_section(
    section: str,
    config: Dict[str, Any],
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_WRITE))
) -> Dict[str, Any]:
    """Update entire configuration section."""
    try:
        logger.info(
            f"Config section update request: {section} "
            f"by: {current_user.username}"
        )
        
        # Update configuration section
        result = await config_manager.set_section(section, config)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Configuration section update failed")
            )
        
        logger.info(
            f"Configuration section {section} updated successfully "
            f"by {current_user.username}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config section update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration section"
        )


@router.delete("", response_model=Dict[str, Any])
async def delete_config(
    section: str,
    key: str,
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_WRITE))
) -> Dict[str, Any]:
    """Delete configuration key."""
    try:
        logger.info(
            f"Config delete request: {section}.{key} "
            f"by: {current_user.username}"
        )
        
        # Delete configuration
        result = await config_manager.delete(section, key)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Configuration deletion failed")
            )
        
        logger.info(
            f"Configuration {section}.{key} deleted successfully "
            f"by {current_user.username}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config delete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete configuration"
        )


@router.delete("/section", response_model=Dict[str, Any])
async def delete_config_section(
    section: str,
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_WRITE))
) -> Dict[str, Any]:
    """Delete entire configuration section."""
    try:
        logger.info(
            f"Config section delete request: {section} "
            f"by: {current_user.username}"
        )
        
        # Delete configuration section
        result = await config_manager.delete_section(section)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Configuration section deletion failed")
            )
        
        logger.info(
            f"Configuration section {section} deleted successfully "
            f"by {current_user.username}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config section delete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete configuration section"
        )


@router.post("/reload", response_model=Dict[str, Any])
async def reload_config(
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_WRITE))
) -> Dict[str, Any]:
    """Reload configuration from file."""
    try:
        logger.info(f"Config reload request by: {current_user.username}")
        
        # Reload configuration
        result = await config_manager.reload()
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Configuration reload failed")
            )
        
        logger.info(f"Configuration reloaded successfully by {current_user.username}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config reload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload configuration"
        )


@router.post("/save", response_model=Dict[str, Any])
async def save_config(
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_WRITE))
) -> Dict[str, Any]:
    """Save configuration to file."""
    try:
        logger.info(f"Config save request by: {current_user.username}")
        
        # Save configuration
        result = await config_manager.save()
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Configuration save failed")
            )
        
        logger.info(f"Configuration saved successfully by {current_user.username}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config save error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save configuration"
        )


@router.get("/schema", response_model=Dict[str, Any])
async def get_config_schema(
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_READ))
) -> Dict[str, Any]:
    """Get configuration schema."""
    try:
        logger.info(f"Config schema request by: {current_user.username}")
        
        # Get configuration schema
        schema = config_manager.get_schema()
        
        return {
            "schema": schema
        }
        
    except Exception as e:
        logger.error(f"Config schema error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration schema"
        )


@router.get("/validate", response_model=Dict[str, Any])
async def validate_config(
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_READ))
) -> Dict[str, Any]:
    """Validate current configuration."""
    try:
        logger.info(f"Config validate request by: {current_user.username}")
        
        # Validate configuration
        result = await config_manager.validate()
        
        return result
        
    except Exception as e:
        logger.error(f"Config validate error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate configuration"
        )


@router.get("/backup", response_model=Dict[str, Any])
async def backup_config(
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_WRITE))
) -> Dict[str, Any]:
    """Create configuration backup."""
    try:
        logger.info(f"Config backup request by: {current_user.username}")
        
        # Create backup
        result = await config_manager.backup()
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Configuration backup failed")
            )
        
        logger.info(f"Configuration backup created successfully by {current_user.username}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config backup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create configuration backup"
        )


@router.post("/restore", response_model=Dict[str, Any])
async def restore_config(
    backup_path: str,
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_WRITE))
) -> Dict[str, Any]:
    """Restore configuration from backup."""
    try:
        logger.info(
            f"Config restore request from {backup_path} "
            f"by: {current_user.username}"
        )
        
        # Restore configuration
        result = await config_manager.restore(backup_path)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Configuration restore failed")
            )
        
        logger.info(
            f"Configuration restored successfully from {backup_path} "
            f"by {current_user.username}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config restore error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore configuration"
        )


@router.get("/history", response_model=Dict[str, Any])
async def get_config_history(
    limit: int = Query(default=10, ge=1, le=100, description="Maximum history entries"),
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_READ))
) -> Dict[str, Any]:
    """Get configuration change history."""
    try:
        logger.info(f"Config history request by: {current_user.username}")
        
        # Get configuration history
        history = await config_manager.get_history(limit)
        
        return {
            "data": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Config history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration history"
        )


@router.get("/watch", response_model=Dict[str, Any])
async def watch_config(
    section: Optional[str] = Query(None, description="Section to watch"),
    key: Optional[str] = Query(None, description="Key to watch"),
    current_user: User = Depends(require_permission(PermissionScope.CONFIG_READ))
) -> Dict[str, Any]:
    """Watch configuration changes."""
    try:
        logger.info(f"Config watch request by: {current_user.username}")
        
        # Watch configuration
        result = await config_manager.watch(section, key)
        
        return result
        
    except Exception as e:
        logger.error(f"Config watch error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to watch configuration"
        )