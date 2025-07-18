"""WebSocket router for CyberCorp Server."""

import json
from typing import Dict, Any, Optional, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from pydantic import BaseModel

from ..models.auth import User, PermissionScope
from ..models.events import EventType, EventMessage
from ..auth import get_current_user, require_permission
from ..websocket import websocket_manager
from ..logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None


class WebSocketSubscribe(BaseModel):
    """WebSocket subscription model."""
    event_types: list[str]
    filters: Optional[Dict[str, Any]] = None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    try:
        # Accept WebSocket connection
        await websocket.accept()
        
        # Authenticate user
        token = websocket.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
        
        try:
            user = await get_current_user(token)
        except Exception:
            await websocket.close(code=1008, reason="Invalid authentication token")
            return
        
        # Add client to manager
        client_id = await websocket_manager.add_client(websocket, user)
        logger.info(f"WebSocket client connected: {client_id} ({user.username})")
        
        try:
            # Send welcome message
            welcome_message = WebSocketMessage(
                type="welcome",
                data={
                    "client_id": client_id,
                    "user": user.username,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            await websocket.send_text(welcome_message.json())
            
            # Handle messages
            while True:
                try:
                    # Receive message
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Process message
                    await process_websocket_message(client_id, message, user)
                    
                except json.JSONDecodeError:
                    error_message = WebSocketMessage(
                        type="error",
                        data={"message": "Invalid JSON format"}
                    )
                    await websocket.send_text(error_message.json())
                    
                except Exception as e:
                    logger.error(f"WebSocket message processing error: {e}")
                    error_message = WebSocketMessage(
                        type="error",
                        data={"message": str(e)}
                    )
                    await websocket.send_text(error_message.json())
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket client disconnected: {client_id}")
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@router.websocket("/ws/system")
async def websocket_system_endpoint(websocket: WebSocket):
    """WebSocket endpoint for system events."""
    try:
        # Accept WebSocket connection
        await websocket.accept()
        
        # Authenticate user
        token = websocket.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
        
        try:
            user = await get_current_user(token)
            if not user.has_permission(PermissionScope.SYSTEM_READ):
                await websocket.close(code=1008, reason="Insufficient permissions")
                return
        except Exception:
            await websocket.close(code=1008, reason="Invalid authentication token")
            return
        
        # Add client to system events
        client_id = await websocket_manager.add_client(
            websocket, user, event_types=[EventType.SYSTEM_METRICS]
        )
        logger.info(f"System WebSocket client connected: {client_id} ({user.username})")
        
        try:
            # Send welcome message
            welcome_message = WebSocketMessage(
                type="system_welcome",
                data={
                    "client_id": client_id,
                    "user": user.username,
                    "subscribed_events": [EventType.SYSTEM_METRICS.value]
                }
            )
            await websocket.send_text(welcome_message.json())
            
            # Keep connection alive
            while True:
                try:
                    # Receive ping
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        pong_message = WebSocketMessage(
                            type="pong",
                            data={"timestamp": datetime.utcnow().isoformat()}
                        )
                        await websocket.send_text(pong_message.json())
                        
                except json.JSONDecodeError:
                    pass
                    
        except WebSocketDisconnect:
            logger.info(f"System WebSocket client disconnected: {client_id}")
            
    except Exception as e:
        logger.error(f"System WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@router.websocket("/ws/windows")
async def websocket_windows_endpoint(websocket: WebSocket):
    """WebSocket endpoint for windows events."""
    try:
        # Accept WebSocket connection
        await websocket.accept()
        
        # Authenticate user
        token = websocket.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
        
        try:
            user = await get_current_user(token)
            if not user.has_permission(PermissionScope.WINDOWS_READ):
                await websocket.close(code=1008, reason="Insufficient permissions")
                return
        except Exception:
            await websocket.close(code=1008, reason="Invalid authentication token")
            return
        
        # Add client to windows events
        client_id = await websocket_manager.add_client(
            websocket, user, event_types=[EventType.WINDOWS_CHANGED]
        )
        logger.info(f"Windows WebSocket client connected: {client_id} ({user.username})")
        
        try:
            # Send welcome message
            welcome_message = WebSocketMessage(
                type="windows_welcome",
                data={
                    "client_id": client_id,
                    "user": user.username,
                    "subscribed_events": [EventType.WINDOWS_CHANGED.value]
                }
            )
            await websocket.send_text(welcome_message.json())
            
            # Keep connection alive
            while True:
                try:
                    # Receive ping
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        pong_message = WebSocketMessage(
                            type="pong",
                            data={"timestamp": datetime.utcnow().isoformat()}
                        )
                        await websocket.send_text(pong_message.json())
                        
                except json.JSONDecodeError:
                    pass
                    
        except WebSocketDisconnect:
            logger.info(f"Windows WebSocket client disconnected: {client_id}")
            
    except Exception as e:
        logger.error(f"Windows WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@router.websocket("/ws/processes")
async def websocket_processes_endpoint(websocket: WebSocket):
    """WebSocket endpoint for processes events."""
    try:
        # Accept WebSocket connection
        await websocket.accept()
        
        # Authenticate user
        token = websocket.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
        
        try:
            user = await get_current_user(token)
            if not user.has_permission(PermissionScope.PROCESSES_READ):
                await websocket.close(code=1008, reason="Insufficient permissions")
                return
        except Exception:
            await websocket.close(code=1008, reason="Invalid authentication token")
            return
        
        # Add client to processes events
        client_id = await websocket_manager.add_client(
            websocket, user, event_types=[EventType.PROCESSES_CHANGED]
        )
        logger.info(f"Processes WebSocket client connected: {client_id} ({user.username})")
        
        try:
            # Send welcome message
            welcome_message = WebSocketMessage(
                type="processes_welcome",
                data={
                    "client_id": client_id,
                    "user": user.username,
                    "subscribed_events": [EventType.PROCESSES_CHANGED.value]
                }
            )
            await websocket.send_text(welcome_message.json())
            
            # Keep connection alive
            while True:
                try:
                    # Receive ping
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        pong_message = WebSocketMessage(
                            type="pong",
                            data={"timestamp": datetime.utcnow().isoformat()}
                        )
                        await websocket.send_text(pong_message.json())
                        
                except json.JSONDecodeError:
                    pass
                    
        except WebSocketDisconnect:
            logger.info(f"Processes WebSocket client disconnected: {client_id}")
            
    except Exception as e:
        logger.error(f"Processes WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """WebSocket endpoint for all events."""
    try:
        # Accept WebSocket connection
        await websocket.accept()
        
        # Authenticate user
        token = websocket.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
        
        try:
            user = await get_current_user(token)
        except Exception:
            await websocket.close(code=1008, reason="Invalid authentication token")
            return
        
        # Add client to all events
        client_id = await websocket_manager.add_client(websocket, user)
        logger.info(f"Events WebSocket client connected: {client_id} ({user.username})")
        
        try:
            # Send welcome message
            welcome_message = WebSocketMessage(
                type="events_welcome",
                data={
                    "client_id": client_id,
                    "user": user.username,
                    "subscribed_events": "all"
                }
            )
            await websocket.send_text(welcome_message.json())
            
            # Handle messages
            while True:
                try:
                    # Receive message
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Process message
                    await process_websocket_message(client_id, message, user)
                    
                except json.JSONDecodeError:
                    error_message = WebSocketMessage(
                        type="error",
                        data={"message": "Invalid JSON format"}
                    )
                    await websocket.send_text(error_message.json())
                    
                except Exception as e:
                    logger.error(f"Events WebSocket message processing error: {e}")
                    error_message = WebSocketMessage(
                        type="error",
                        data={"message": str(e)}
                    )
                    await websocket.send_text(error_message.json())
                    
        except WebSocketDisconnect:
            logger.info(f"Events WebSocket client disconnected: {client_id}")
            
    except Exception as e:
        logger.error(f"Events WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


async def process_websocket_message(client_id: str, message: Dict[str, Any], user: User):
    """Process WebSocket message."""
    try:
        message_type = message.get("type")
        message_data = message.get("data", {})
        
        if message_type == "subscribe":
            # Subscribe to events
            event_types = message_data.get("event_types", [])
            filters = message_data.get("filters", {})
            
            await websocket_manager.subscribe_client(client_id, event_types, filters)
            
            response = WebSocketMessage(
                type="subscribed",
                data={
                    "event_types": event_types,
                    "filters": filters
                }
            )
            await websocket_manager.send_to_client(client_id, response.json())
            
        elif message_type == "unsubscribe":
            # Unsubscribe from events
            event_types = message_data.get("event_types", [])
            
            await websocket_manager.unsubscribe_client(client_id, event_types)
            
            response = WebSocketMessage(
                type="unsubscribed",
                data={"event_types": event_types}
            )
            await websocket_manager.send_to_client(client_id, response.json())
            
        elif message_type == "ping":
            # Respond to ping
            response = WebSocketMessage(
                type="pong",
                data={"timestamp": datetime.utcnow().isoformat()}
            )
            await websocket_manager.send_to_client(client_id, response.json())
            
        elif message_type == "get_clients":
            # Get connected clients (admin only)
            if user.has_permission(PermissionScope.ADMIN):
                clients = await websocket_manager.get_clients()
                response = WebSocketMessage(
                    type="clients",
                    data={"clients": clients}
                )
                await websocket_manager.send_to_client(client_id, response.json())
            else:
                response = WebSocketMessage(
                    type="error",
                    data={"message": "Insufficient permissions"}
                )
                await websocket_manager.send_to_client(client_id, response.json())
                
        else:
            # Unknown message type
            response = WebSocketMessage(
                type="error",
                data={"message": f"Unknown message type: {message_type}"}
            )
            await websocket_manager.send_to_client(client_id, response.json())
            
    except Exception as e:
        logger.error(f"WebSocket message processing error: {e}")
        response = WebSocketMessage(
            type="error",
            data={"message": str(e)}
        )
        await websocket_manager.send_to_client(client_id, response.json())


@router.get("/clients", response_model=Dict[str, Any])
async def get_websocket_clients(
    current_user: User = Depends(require_permission(PermissionScope.ADMIN))
) -> Dict[str, Any]:
    """Get WebSocket clients."""
    try:
        logger.info(f"WebSocket clients request by: {current_user.username}")
        
        # Get clients
        clients = await websocket_manager.get_clients()
        
        return {
            "data": clients,
            "count": len(clients)
        }
        
    except Exception as e:
        logger.error(f"WebSocket clients error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve WebSocket clients"
        )


@router.delete("/clients/{client_id}", response_model=Dict[str, Any])
async def disconnect_websocket_client(
    client_id: str,
    current_user: User = Depends(require_permission(PermissionScope.ADMIN))
) -> Dict[str, Any]:
    """Disconnect WebSocket client."""
    try:
        logger.info(
            f"WebSocket client disconnect request for {client_id} "
            f"by: {current_user.username}"
        )
        
        # Disconnect client
        result = await websocket_manager.disconnect_client(client_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "Client not found")
            )
        
        logger.info(
            f"WebSocket client {client_id} disconnected successfully "
            f"by {current_user.username}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WebSocket client disconnect error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect WebSocket client"
        )


@router.post("/broadcast", response_model=Dict[str, Any])
async def broadcast_websocket_message(
    message: Dict[str, Any],
    event_type: str = Query(..., description="Event type"),
    current_user: User = Depends(require_permission(PermissionScope.ADMIN))
) -> Dict[str, Any]:
    """Broadcast message to all WebSocket clients."""
    try:
        logger.info(
            f"WebSocket broadcast request for event {event_type} "
            f"by: {current_user.username}"
        )
        
        # Create event message
        event_message = EventMessage(
            type=EventType(event_type),
            data=message,
            source="admin",
            timestamp=datetime.utcnow()
        )
        
        # Broadcast message
        result = await websocket_manager.broadcast(event_message)
        
        logger.info(
            f"WebSocket broadcast completed successfully "
            f"by {current_user.username}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"WebSocket broadcast error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast WebSocket message"
        )