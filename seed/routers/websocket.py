"""
WebSocket routes for CyberCorp Seed Server
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging
import asyncio
from datetime import datetime
from core.websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)
router = APIRouter()

# Create global connection manager
manager = ConnectionManager()


@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time communication
    Handles client connections and message routing
    """
    await manager.connect(websocket)
    try:
        # Send welcome message
        welcome_message = {
            "type": "welcome",
            "message": "Connected to CyberCorp Seed Server",
            "timestamp": datetime.utcnow().isoformat(),
            "connection_id": id(websocket)
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_message(websocket, message)
            except json.JSONDecodeError:
                error_message = {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_text(json.dumps(error_message))
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                error_message = {
                    "type": "error",
                    "message": f"Message handling error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_text(json.dumps(error_message))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client {id(websocket)} disconnected")


async def handle_message(websocket: WebSocket, message: Dict):
    """
    Handle incoming WebSocket messages
    """
    message_type = message.get("type")
    
    if message_type == "ping":
        # Handle ping message
        pong_message = {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat(),
            "original_timestamp": message.get("timestamp")
        }
        await websocket.send_text(json.dumps(pong_message))
        
    elif message_type == "broadcast":
        # Handle broadcast message to all connected clients
        broadcast_data = {
            "type": "broadcast",
            "sender": id(websocket),
            "message": message.get("message", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast(json.dumps(broadcast_data))
        
    elif message_type == "echo":
        # Handle echo message
        echo_message = {
            "type": "echo",
            "original_message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send_text(json.dumps(echo_message))
        
    elif message_type == "status":
        # Handle status request
        status_message = {
            "type": "status_response",
            "active_connections": manager.get_connection_count(),
            "server_status": "running",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send_text(json.dumps(status_message))
        
    else:
        # Handle unknown message type
        error_message = {
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send_text(json.dumps(error_message))


@router.websocket("/test")
async def websocket_test_endpoint(websocket: WebSocket):
    """
    Test WebSocket endpoint for development and debugging
    """
    await websocket.accept()
    try:
        # Send test message every 5 seconds
        counter = 0
        while True:
            counter += 1
            test_message = {
                "type": "test_message",
                "counter": counter,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Test message #{counter}"
            }
            await websocket.send_text(json.dumps(test_message))
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        logger.info("Test WebSocket client disconnected") 