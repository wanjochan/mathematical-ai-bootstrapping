"""System router for CyberCorp Server."""

from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models.system import SystemMetrics, SystemInfo, SystemAlert
from ..models.auth import User, PermissionScope
from ..auth import get_current_user, require_permission
from ..monitoring import monitoring_service
from ..logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/info", response_model=SystemInfo)
async def get_system_info(
    current_user: User = Depends(require_permission(PermissionScope.SYSTEM_READ))
) -> SystemInfo:
    """Get system information."""
    try:
        logger.info(f"System info request by: {current_user.username}")
        
        # Get system information
        system_info = await monitoring_service.get_system_info()
        
        return system_info
        
    except Exception as e:
        logger.error(f"System info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system information"
        )


@router.get("/metrics", response_model=SystemMetrics)
async def get_current_metrics(
    format: str = Query(default="json", regex="^(json|prometheus)$"),
    detailed: bool = Query(default=False),
    current_user: User = Depends(require_permission(PermissionScope.SYSTEM_READ))
) -> SystemMetrics:
    """Get current system metrics."""
    try:
        logger.info(f"System metrics request by: {current_user.username}")
        
        # Get current metrics
        metrics = await monitoring_service.get_current_metrics(detailed=detailed)
        
        if format == "prometheus":
            # Convert to Prometheus format
            prometheus_metrics = await monitoring_service.get_prometheus_metrics()
            return {"format": "prometheus", "data": prometheus_metrics}
        
        return metrics
        
    except Exception as e:
        logger.error(f"System metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics"
        )


@router.get("/history")
async def get_historical_data(
    start: Optional[datetime] = Query(None, description="Start time (ISO8601)"),
    end: Optional[datetime] = Query(None, description="End time (ISO8601)"),
    interval: int = Query(default=60, description="Data aggregation interval in seconds"),
    metrics: Optional[List[str]] = Query(None, description="Specific metrics to include"),
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=100, ge=1, le=1000, description="Items per page"),
    current_user: User = Depends(require_permission(PermissionScope.SYSTEM_READ))
) -> Dict[str, Any]:
    """Get historical system data."""
    try:
        logger.info(f"System history request by: {current_user.username}")
        
        # Get historical data
        history_data = await monitoring_service.get_historical_data(
            start=start,
            end=end,
            interval=interval,
            metrics=metrics,
            page=page,
            per_page=per_page
        )
        
        return {
            "data": history_data,
            "pagination": {
                "total": len(history_data),
                "page": page,
                "per_page": per_page,
                "pages": (len(history_data) + per_page - 1) // per_page
            }
        }
        
    except Exception as e:
        logger.error(f"System history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve historical data"
        )


@router.get("/metrics/cpu")
async def get_cpu_metrics(
    start: Optional[datetime] = Query(None, description="Start time (ISO8601)"),
    end: Optional[datetime] = Query(None, description="End time (ISO8601)"),
    per_cpu: bool = Query(default=False, description="Include per-CPU data"),
    current_user: User = Depends(require_permission(PermissionScope.SYSTEM_READ))
) -> Dict[str, Any]:
    """Get CPU metrics."""
    try:
        logger.info(f"CPU metrics request by: {current_user.username}")
        
        # Get CPU metrics
        cpu_metrics = await monitoring_service.get_cpu_metrics(
            start=start,
            end=end,
            per_cpu=per_cpu
        )
        
        return {"data": cpu_metrics}
        
    except Exception as e:
        logger.error(f"CPU metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve CPU metrics"
        )


@router.get("/metrics/memory")
async def get_memory_metrics(
    start: Optional[datetime] = Query(None, description="Start time (ISO8601)"),
    end: Optional[datetime] = Query(None, description="End time (ISO8601)"),
    current_user: User = Depends(require_permission(PermissionScope.SYSTEM_READ))
) -> Dict[str, Any]:
    """Get memory metrics."""
    try:
        logger.info(f"Memory metrics request by: {current_user.username}")
        
        # Get memory metrics
        memory_metrics = await monitoring_service.get_memory_metrics(
            start=start,
            end=end
        )
        
        return {"data": memory_metrics}
        
    except Exception as e:
        logger.error(f"Memory metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memory metrics"
        )


@router.get("/metrics/disk")
async def get_disk_metrics(
    start: Optional[datetime] = Query(None, description="Start time (ISO8601)"),
    end: Optional[datetime] = Query(None, description="End time (ISO8601)"),
    current_user: User = Depends(require_permission(PermissionScope.SYSTEM_READ))
) -> Dict[str, Any]:
    """Get disk metrics."""
    try:
        logger.info(f"Disk metrics request by: {current_user.username}")
        
        # Get disk metrics
        disk_metrics = await monitoring_service.get_disk_metrics(
            start=start,
            end=end
        )
        
        return {"data": disk_metrics}
        
    except Exception as e:
        logger.error(f"Disk metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve disk metrics"
        )


@router.get("/metrics/network")
async def get_network_metrics(
    start: Optional[datetime] = Query(None, description="Start time (ISO8601)"),
    end: Optional[datetime] = Query(None, description="End time (ISO8601)"),
    current_user: User = Depends(require_permission(PermissionScope.SYSTEM_READ))
) -> Dict[str, Any]:
    """Get network metrics."""
    try:
        logger.info(f"Network metrics request by: {current_user.username}")
        
        # Get network metrics
        network_metrics = await monitoring_service.get_network_metrics(
            start=start,
            end=end
        )
        
        return {"data": network_metrics}
        
    except Exception as e:
        logger.error(f"Network metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve network metrics"
        )


@router.get("/alerts", response_model=List[SystemAlert])
async def get_system_alerts(
    active_only: bool = Query(default=True, description="Show only active alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    current_user: User = Depends(require_permission(PermissionScope.SYSTEM_READ))
) -> List[SystemAlert]:
    """Get system alerts."""
    try:
        logger.info(f"System alerts request by: {current_user.username}")
        
        # Get alerts
        alerts = await monitoring_service.get_alerts(
            active_only=active_only,
            severity=severity,
            limit=limit
        )
        
        return alerts
        
    except Exception as e:
        logger.error(f"System alerts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system alerts"
        )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(require_permission(PermissionScope.SYSTEM_WRITE))
) -> Dict[str, Any]:
    """Acknowledge system alert."""
    try:
        logger.info(f"Alert acknowledge request for {alert_id} by: {current_user.username}")
        
        # Acknowledge alert
        success = await monitoring_service.acknowledge_alert(alert_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        logger.info(f"Alert {alert_id} acknowledged by {current_user.username}")
        return {"success": True, "message": "Alert acknowledged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Alert acknowledge error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )


@router.get("/status")
async def get_system_status(
    current_user: User = Depends(require_permission(PermissionScope.SYSTEM_READ))
) -> Dict[str, Any]:
    """Get overall system status."""
    try:
        logger.info(f"System status request by: {current_user.username}")
        
        # Get system status
        status_info = await monitoring_service.get_system_status()
        
        return {
            "status": status_info.get("status", "unknown"),
            "uptime": status_info.get("uptime", 0),
            "load_average": status_info.get("load_average", []),
            "active_alerts": status_info.get("active_alerts", 0),
            "services": status_info.get("services", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )


@router.post("/restart")
async def restart_monitoring(
    current_user: User = Depends(require_permission(PermissionScope.SYSTEM_WRITE))
) -> Dict[str, Any]:
    """Restart monitoring service."""
    try:
        logger.info(f"Monitoring restart request by: {current_user.username}")
        
        # Restart monitoring
        await monitoring_service.restart()
        
        logger.info(f"Monitoring service restarted by {current_user.username}")
        return {"success": True, "message": "Monitoring service restarted successfully"}
        
    except Exception as e:
        logger.error(f"Monitoring restart error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart monitoring service"
        )