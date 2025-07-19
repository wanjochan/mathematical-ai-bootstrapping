"""WebSocket manager for CyberCorp server."""
import asyncio
from typing import List, Any, Optional
from fastapi import WebSocket
import json
from datetime import datetime


class ConnectionManager:
    """WebSocket connection manager."""
    
    def __init__(self):
        """Initialize the manager."""
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific connection."""
        await websocket.send_text(message)
        
    async def broadcast(self, message: str):
        """Broadcast a message to all connections."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
                
        # Clean up disconnected connections
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


class DashboardManager:
    """Dashboard real-time data manager."""
    
    def __init__(self):
        """Initialize dashboard manager."""
        self.manager = ConnectionManager()
        self._update_task: Optional[asyncio.Task] = None
        
    def start(self):
        """Start dashboard data updates."""
        if self._update_task is None:
            self._update_task = asyncio.create_task(self._update_loop())
            
    def stop(self):
        """Stop dashboard data updates."""
        if self._update_task and not self._update_task.done():
            self._update_task.cancel()
            self._update_task = None
            
    async def _update_loop(self):
        """Update loop for dashboard data."""
        try:
            while True:
                await asyncio.sleep(2)  # Update every 2 seconds
                await self._broadcast_metrics()
        except asyncio.CancelledError:
            pass
            
    async def _broadcast_metrics(self):
        """Broadcast metrics to connected clients."""
        try:
            # Import here to avoid circular dependency
            from .monitoring import monitoring_service
            
            metrics = await monitoring_service.get_system_metrics()
            message = {
                "type": "metrics",
                "data": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.manager.broadcast(json.dumps(message))
            
        except Exception as e:
            # Handle errors gracefully
            error_message = {
                "type": "error",
                "data": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.manager.broadcast(json.dumps(error_message))


# Global WebSocket managers
websocket_manager = ConnectionManager()
dashboard_manager = DashboardManager()