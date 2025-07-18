"""Window service module for CyberCorp Server."""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio
import platform

from ..models.windows import (
    WindowInfo, WindowBounds, WindowState, WindowAction,
    WindowQuery, WindowControlRequest, WindowMoveRequest, WindowResizeRequest
)
from ..logging_config import get_logger

logger = get_logger(__name__)


class WindowService:
    """Service for window management operations."""
    
    def __init__(self):
        """Initialize the window service."""
        self.platform = platform.system()
        self.window_manager = None
        self.window_cache = {}
        self.cache_expiry = 5  # seconds
        self.last_cache_update = None
    
    async def initialize(self):
        """Initialize the service."""
        # Import platform-specific window manager
        if self.platform == "Windows":
            from ..utils.windows_manager import WindowsManager
            self.window_manager = WindowsManager()
        elif self.platform == "Darwin":  # macOS
            from ..utils.macos_manager import MacOSManager
            self.window_manager = MacOSManager()
        elif self.platform == "Linux":
            from ..utils.linux_manager import LinuxManager
            self.window_manager = LinuxManager()
        else:
            raise RuntimeError(f"Unsupported platform: {self.platform}")
        
        # Initialize window manager
        await self.window_manager.initialize()
        
        logger.info(f"Window service initialized for platform: {self.platform}")
    
    async def shutdown(self):
        """Shutdown the service."""
        if self.window_manager:
            await self.window_manager.shutdown()
        
        logger.info("Window service shutting down")
    
    async def list_windows(self, query: WindowQuery) -> Tuple[List[WindowInfo], int]:
        """List windows based on query parameters."""
        try:
            # Check if cache is valid
            now = datetime.utcnow()
            if not self.last_cache_update or (now - self.last_cache_update).total_seconds() > self.cache_expiry:
                # Cache expired, refresh windows
                await self._refresh_window_cache()
            
            # Filter windows based on query
            filtered_windows = []
            for window in self.window_cache.values():
                # Apply filters
                if query.visible_only and not window.visible:
                    continue
                
                if query.active_only and not window.active:
                    continue
                
                if query.process_id and window.process_id != query.process_id:
                    continue
                
                if query.title_contains and query.title_contains.lower() not in window.title.lower():
                    continue
                
                filtered_windows.append(window)
            
            # Sort windows by z-order (if available) or by title
            if hasattr(filtered_windows[0], 'z_order') if filtered_windows else False:
                filtered_windows.sort(key=lambda w: w.z_order)
            else:
                filtered_windows.sort(key=lambda w: w.title)
            
            # Apply pagination
            total = len(filtered_windows)
            start = query.offset
            end = start + query.limit if query.limit else total
            paginated_windows = filtered_windows[start:end]
            
            return paginated_windows, total
        except Exception as e:
            logger.error(f"Error listing windows: {e}")
            raise
    
    async def get_window(self, window_id: str) -> Optional[WindowInfo]:
        """Get window by ID."""
        try:
            # Check if window is in cache
            if window_id in self.window_cache:
                return self.window_cache[window_id]
            
            # Not in cache, get directly from window manager
            window = await self.window_manager.get_window_info(window_id)
            if window:
                # Add to cache
                self.window_cache[window_id] = window
            
            return window
        except Exception as e:
            logger.error(f"Error getting window {window_id}: {e}")
            raise
    
    async def control_window(self, window_id: str, action: WindowAction) -> bool:
        """Control a window."""
        try:
            # Get window
            window = await self.get_window(window_id)
            if not window:
                return False
            
            # Perform action
            result = False
            if action == WindowAction.FOCUS:
                result = await self.window_manager.focus_window(window_id)
            elif action == WindowAction.MINIMIZE:
                result = await self.window_manager.minimize_window(window_id)
            elif action == WindowAction.MAXIMIZE:
                result = await self.window_manager.maximize_window(window_id)
            elif action == WindowAction.RESTORE:
                result = await self.window_manager.restore_window(window_id)
            elif action == WindowAction.CLOSE:
                result = await self.window_manager.close_window(window_id)
            elif action == WindowAction.HIDE:
                result = await self.window_manager.hide_window(window_id)
            elif action == WindowAction.SHOW:
                result = await self.window_manager.show_window(window_id)
            else:
                raise ValueError(f"Unsupported window action: {action}")
            
            # Invalidate cache for this window
            if window_id in self.window_cache:
                del self.window_cache[window_id]
            
            return result
        except Exception as e:
            logger.error(f"Error controlling window {window_id} with action {action}: {e}")
            raise
    
    async def move_window(self, window_id: str, x: int, y: int) -> bool:
        """Move a window to a new position."""
        try:
            # Get window
            window = await self.get_window(window_id)
            if not window:
                return False
            
            # Move window
            result = await self.window_manager.move_window(window_id, x, y)
            
            # Invalidate cache for this window
            if window_id in self.window_cache:
                del self.window_cache[window_id]
            
            return result
        except Exception as e:
            logger.error(f"Error moving window {window_id} to ({x}, {y}): {e}")
            raise
    
    async def resize_window(self, window_id: str, width: int, height: int) -> bool:
        """Resize a window."""
        try:
            # Get window
            window = await self.get_window(window_id)
            if not window:
                return False
            
            # Resize window
            result = await self.window_manager.resize_window(window_id, width, height)
            
            # Invalidate cache for this window
            if window_id in self.window_cache:
                del self.window_cache[window_id]
            
            return result
        except Exception as e:
            logger.error(f"Error resizing window {window_id} to {width}x{height}: {e}")
            raise
    
    async def set_window_bounds(self, window_id: str, bounds: WindowBounds) -> bool:
        """Set window bounds (position and size)."""
        try:
            # Get window
            window = await self.get_window(window_id)
            if not window:
                return False
            
            # Set window bounds
            result = await self.window_manager.set_window_bounds(
                window_id, bounds.x, bounds.y, bounds.width, bounds.height
            )
            
            # Invalidate cache for this window
            if window_id in self.window_cache:
                del self.window_cache[window_id]
            
            return result
        except Exception as e:
            logger.error(f"Error setting window bounds for {window_id}: {e}")
            raise
    
    async def set_window_state(self, window_id: str, state: WindowState) -> bool:
        """Set window state."""
        try:
            # Get window
            window = await self.get_window(window_id)
            if not window:
                return False
            
            # Set window state
            result = False
            if state == WindowState.NORMAL:
                result = await self.window_manager.restore_window(window_id)
            elif state == WindowState.MINIMIZED:
                result = await self.window_manager.minimize_window(window_id)
            elif state == WindowState.MAXIMIZED:
                result = await self.window_manager.maximize_window(window_id)
            else:
                raise ValueError(f"Unsupported window state: {state}")
            
            # Invalidate cache for this window
            if window_id in self.window_cache:
                del self.window_cache[window_id]
            
            return result
        except Exception as e:
            logger.error(f"Error setting window state for {window_id} to {state}: {e}")
            raise
    
    async def get_active_window(self) -> Optional[WindowInfo]:
        """Get the currently active window."""
        try:
            # Get active window from window manager
            window = await self.window_manager.get_active_window()
            
            # Update cache
            if window:
                self.window_cache[window.id] = window
            
            return window
        except Exception as e:
            logger.error(f"Error getting active window: {e}")
            raise
    
    async def get_windows_by_process(self, process_id: int) -> List[WindowInfo]:
        """Get all windows belonging to a specific process."""
        try:
            # Check if cache is valid
            now = datetime.utcnow()
            if not self.last_cache_update or (now - self.last_cache_update).total_seconds() > self.cache_expiry:
                # Cache expired, refresh windows
                await self._refresh_window_cache()
            
            # Filter windows by process ID
            process_windows = []
            for window in self.window_cache.values():
                if window.process_id == process_id:
                    process_windows.append(window)
            
            return process_windows
        except Exception as e:
            logger.error(f"Error getting windows for process {process_id}: {e}")
            raise
    
    async def _refresh_window_cache(self) -> None:
        """Refresh the window cache."""
        try:
            # Get all windows from window manager
            windows = await self.window_manager.list_windows()
            
            # Update cache
            self.window_cache = {window.id: window for window in windows}
            self.last_cache_update = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error refreshing window cache: {e}")
            raise


# Singleton instance
window_service = WindowService()