"""API routers for CyberCorp Server."""

from .auth import router as auth_router
from .system import router as system_router
from .windows import router as windows_router
from .processes import router as processes_router
from .config import router as config_router
from .websocket import router as websocket_router
from .employees import router as employees_router
from .tasks import router as tasks_router

__all__ = [
    "auth_router",
    "system_router", 
    "windows_router",
    "processes_router",
    "config_router",
    "websocket_router",
    "employees_router",
    "tasks_router",
]