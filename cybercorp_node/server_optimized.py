"""Optimized CyberCorp server with async command handling"""

import asyncio
import websockets
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from collections import defaultdict
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Client:
    """Enhanced client information"""
    id: str
    websocket: websockets.WebSocketServerProtocol
    user_session: str
    capabilities: Dict[str, Any] = field(default_factory=dict)
    connected_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    pending_commands: Dict[str, 'Command'] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=lambda: {
        'commands_sent': 0,
        'commands_completed': 0,
        'avg_response_time': 0
    })


@dataclass
class Command:
    """Command with metadata"""
    id: str
    command: str
    params: Dict[str, Any]
    priority: int = 5
    created_at: datetime = field(default_factory=datetime.now)
    status: str = 'pending'
    result: Optional[Dict[str, Any]] = None
    duration: Optional[float] = None
    target_client: Optional[str] = None


class OptimizedCyberCorpServer:
    """High-performance server with async command handling"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 9998):
        self.host = host
        self.port = port
        self.clients: Dict[str, Client] = {}
        self.management_clients: Set[str] = set()
        self.command_history: List[Command] = []
        self.max_history = 1000
        
    async def start(self):
        """Start server with maintenance tasks"""
        logger.info(f"Starting optimized server on {self.host}:{self.port}")
        
        # Start maintenance tasks
        asyncio.create_task(self._heartbeat_monitor())
        asyncio.create_task(self._cleanup_task())
        asyncio.create_task(self._stats_reporter())
        
        # Start WebSocket server
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10,
            max_size=10 * 1024 * 1024  # 10MB
        ):
            logger.info("Server started successfully")
            await asyncio.Future()  # Run forever
            
    async def handle_client(self, websocket, path):
        """Handle client connection"""
        client_id = None
        
        try:
            # Wait for registration
            message = await asyncio.wait_for(websocket.recv(), timeout=30)
            data = json.loads(message)
            
            if data.get('type') != 'register':
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'First message must be registration'
                }))
                return
                
            # Create client
            client_id = f"client_{len(self.clients)}"
            client = Client(
                id=client_id,
                websocket=websocket,
                user_session=data.get('user_session', 'unknown'),
                capabilities=data.get('capabilities', {})
            )
            
            self.clients[client_id] = client
            
            # Check if management client
            if client.capabilities.get('management'):
                self.management_clients.add(client_id)
                logger.info(f"Management client connected: {client_id}")
            
            # Send welcome
            await websocket.send(json.dumps({
                'type': 'welcome',
                'client_id': client_id,
                'server_time': datetime.now().isoformat()
            }))
            
            logger.info(f"Client {client_id} ({client.user_session}) connected")
            
            # Handle messages
            await self._handle_messages(client)
            
        except asyncio.TimeoutError:
            logger.warning("Client registration timeout")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            if client_id:
                self.clients.pop(client_id, None)
                self.management_clients.discard(client_id)
                logger.info(f"Client {client_id} removed")
                
    async def _handle_messages(self, client: Client):
        """Handle messages from client"""
        try:
            async for message in client.websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type')
                    
                    if msg_type == 'ping':
                        client.last_heartbeat = datetime.now()
                        await client.websocket.send(json.dumps({'type': 'pong'}))
                        
                    elif msg_type == 'request':
                        await self._handle_request(client, data)
                        
                    elif msg_type == 'forward_command':
                        await self._handle_forward_command(client, data)
                        
                    elif msg_type == 'command_ack':
                        await self._handle_command_ack(client, data)
                        
                    elif msg_type == 'command_result':
                        await self._handle_command_result(client, data)
                        
                    elif msg_type == 'command_error':
                        await self._handle_command_error(client, data)
                        
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                    await client.websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON'
                    }))
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            pass
            
    async def _handle_request(self, client: Client, data: Dict[str, Any]):
        """Handle direct requests"""
        command = data.get('command')
        
        if command == 'list_clients':
            # Return client list
            client_list = []
            for cid, c in self.clients.items():
                client_list.append({
                    'id': cid,
                    'user_session': c.user_session,
                    'capabilities': c.capabilities,
                    'connected_at': c.connected_at.isoformat(),
                    'last_heartbeat': c.last_heartbeat.isoformat(),
                    'stats': c.stats
                })
                
            await client.websocket.send(json.dumps({
                'type': 'response',
                'command': command,
                'clients': client_list
            }))
            
        elif command == 'get_stats':
            # Return server statistics
            stats = {
                'clients': len(self.clients),
                'management_clients': len(self.management_clients),
                'total_commands': len(self.command_history),
                'active_commands': sum(
                    len(c.pending_commands) for c in self.clients.values()
                )
            }
            
            await client.websocket.send(json.dumps({
                'type': 'response',
                'command': command,
                'stats': stats
            }))
            
    async def _handle_forward_command(self, client: Client, data: Dict[str, Any]):
        """Handle command forwarding with priority"""
        target_client_id = data.get('target_client')
        command_data = data.get('command', {})
        
        if target_client_id not in self.clients:
            await client.websocket.send(json.dumps({
                'type': 'forward_error',
                'error': 'Target client not found'
            }))
            return
            
        # Create command with metadata
        command_id = str(uuid.uuid4())
        command = Command(
            id=command_id,
            command=command_data.get('command'),
            params=command_data.get('params', {}),
            priority=data.get('priority', 5),
            target_client=target_client_id
        )
        
        # Store in target client's pending commands
        target_client = self.clients[target_client_id]
        target_client.pending_commands[command_id] = command
        
        # Update stats
        target_client.stats['commands_sent'] += 1
        
        # Forward to target client
        try:
            await target_client.websocket.send(json.dumps({
                'type': 'command',
                'command_id': command_id,
                'command': command.command,
                'params': command.params,
                'priority': command.priority
            }))
            
            # Send acknowledgment to requester
            await client.websocket.send(json.dumps({
                'type': 'forward_ack',
                'command_id': command_id,
                'target_client': target_client_id,
                'status': 'sent'
            }))
            
            # Store in history
            self.command_history.append(command)
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
                
        except Exception as e:
            logger.error(f"Error forwarding command: {e}")
            await client.websocket.send(json.dumps({
                'type': 'forward_error',
                'error': str(e)
            }))
            
    async def _handle_command_ack(self, client: Client, data: Dict[str, Any]):
        """Handle command acknowledgment"""
        command_id = data.get('command_id')
        status = data.get('status')
        
        if command_id in client.pending_commands:
            command = client.pending_commands[command_id]
            command.status = status
            logger.debug(f"Command {command_id} acknowledged: {status}")
            
    async def _handle_command_result(self, client: Client, data: Dict[str, Any]):
        """Handle command result"""
        command_id = data.get('command_id')
        result = data.get('result')
        duration = data.get('duration')
        
        if command_id in client.pending_commands:
            command = client.pending_commands.pop(command_id)
            command.status = 'completed'
            command.result = result
            command.duration = duration
            
            # Update stats
            client.stats['commands_completed'] += 1
            if duration:
                # Update average response time
                avg = client.stats['avg_response_time']
                count = client.stats['commands_completed']
                client.stats['avg_response_time'] = (
                    (avg * (count - 1) + duration) / count
                )
            
            logger.info(
                f"Command {command.command} completed in {duration:.2f}s"
            )
            
            # Forward result to management clients
            await self._broadcast_to_management({
                'type': 'command_result',
                'command_id': command_id,
                'client_id': client.id,
                'result': result,
                'duration': duration
            })
            
    async def _handle_command_error(self, client: Client, data: Dict[str, Any]):
        """Handle command error"""
        command_id = data.get('command_id')
        error = data.get('error')
        
        if command_id in client.pending_commands:
            command = client.pending_commands.pop(command_id)
            command.status = 'error'
            command.result = {'error': error}
            
            logger.error(f"Command {command_id} error: {error}")
            
            # Forward error to management clients
            await self._broadcast_to_management({
                'type': 'command_error',
                'command_id': command_id,
                'client_id': client.id,
                'error': error
            })
            
    async def _broadcast_to_management(self, data: Dict[str, Any]):
        """Broadcast message to all management clients"""
        message = json.dumps(data)
        
        for client_id in self.management_clients:
            if client_id in self.clients:
                try:
                    await self.clients[client_id].websocket.send(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    
    async def _heartbeat_monitor(self):
        """Monitor client heartbeats"""
        while True:
            try:
                await asyncio.sleep(30)
                
                now = datetime.now()
                timeout = timedelta(seconds=60)
                
                for client_id, client in list(self.clients.items()):
                    if now - client.last_heartbeat > timeout:
                        logger.warning(f"Client {client_id} heartbeat timeout")
                        await client.websocket.close()
                        
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                
    async def _cleanup_task(self):
        """Cleanup old data"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Cleanup old commands from history
                cutoff_time = datetime.now() - timedelta(hours=1)
                self.command_history = [
                    cmd for cmd in self.command_history
                    if cmd.created_at > cutoff_time
                ]
                
                logger.debug(f"Cleaned up, {len(self.command_history)} commands in history")
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                
    async def _stats_reporter(self):
        """Report server statistics"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                
                active_clients = len(self.clients)
                total_pending = sum(
                    len(c.pending_commands) for c in self.clients.values()
                )
                
                logger.info(
                    f"Stats - Clients: {active_clients}, "
                    f"Pending commands: {total_pending}"
                )
                
            except Exception as e:
                logger.error(f"Stats reporter error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimized CyberCorp Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=9998, help='Port to bind to')
    
    args = parser.parse_args()
    
    server = OptimizedCyberCorpServer(args.host, args.port)
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")