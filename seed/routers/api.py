"""
REST API routes for CyberCorp Seed Server
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import psutil
import platform
import time
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint
    Returns server health status and basic system information
    """
    try:
        # Get system information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/status")
async def server_status() -> Dict[str, Any]:
    """
    Server status endpoint
    Returns current server configuration and runtime information
    """
    from config import settings
    
    return {
        "server": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "host": settings.host,
            "port": settings.port
        },
        "runtime": {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.time() - psutil.Process().create_time(),
            "log_level": settings.log_level
        }
    }


@router.get("/info")
async def system_info() -> Dict[str, Any]:
    """
    System information endpoint
    Returns detailed system and application information
    """
    try:
        process = psutil.Process()
        
        return {
            "application": {
                "name": "CyberCorp Seed Server",
                "version": "0.1.0",
                "description": "FastAPI seed server for CyberCorp system development"
            },
            "process": {
                "pid": process.pid,
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
                "memory_info": process.memory_info()._asdict(),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads()
            },
            "python": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "compiler": platform.python_compiler()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}") 