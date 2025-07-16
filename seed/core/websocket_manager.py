"""
WebSocket connection manager for CyberCorp Seed Server
"""

from fastapi import WebSocket
from typing import List, Dict, Any
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_data[websocket] = {
            "connected_at": datetime.utcnow(),
            "id": id(websocket),
            "message_count": 0
        }
        logger.info(f"New WebSocket connection accepted: {id(websocket)}")
        logger.info(f"Total active connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_data:
            del self.connection_data[websocket]
        logger.info(f"WebSocket connection removed: {id(websocket)}")
        logger.info(f"Total active connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(message)
            if websocket in self.connection_data:
                self.connection_data[websocket]["message_count"] += 1
        except Exception as e:
            logger.error(f"Failed to send personal message to {id(websocket)}: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSocket clients"""
        disconnected_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
                if connection in self.connection_data:
                    self.connection_data[connection]["message_count"] += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast message to {id(connection)}: {e}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)
        
        logger.info(f"Broadcast message sent to {len(self.active_connections)} connections")
    
    async def broadcast_json(self, data: Dict[str, Any]):
        """Broadcast a JSON message to all connected WebSocket clients"""
        message = json.dumps(data)
        await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections"""
        info = []
        for websocket, data in self.connection_data.items():
            info.append({
                "id": data["id"],
                "connected_at": data["connected_at"].isoformat(),
                "message_count": data["message_count"],
                "is_active": websocket in self.active_connections
            })
        return info
    
    async def ping_all_connections(self):
        """Send ping message to all connections to check if they're alive"""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Server ping"
        }
        await self.broadcast_json(ping_message) 