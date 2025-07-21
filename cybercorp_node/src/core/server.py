"""
CyberCorp Control Server - Stable Version
Designed for cross-user session control of VSCode and development environments
"""

import asyncio
import websockets
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import os
import configparser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CyberCorpServer')

class CommandType(Enum):
    # Window operations
    GET_WINDOWS = "get_windows"
    GET_WINDOW_CONTENT = "get_window_content"
    ACTIVATE_WINDOW = "activate_window"
    
    # Input operations
    SEND_KEYS = "send_keys"
    SEND_MOUSE_CLICK = "send_mouse_click"
    SEND_MOUSE_MOVE = "send_mouse_move"
    
    # Screen operations
    TAKE_SCREENSHOT = "take_screenshot"
    GET_SCREEN_SIZE = "get_screen_size"
    
    # System operations
    GET_PROCESSES = "get_processes"
    GET_SYSTEM_INFO = "get_system_info"
    
    # VSCode specific
    VSCODE_GET_CONTENT = "vscode_get_content"
    VSCODE_SEND_COMMAND = "vscode_send_command"
    VSCODE_TYPE_TEXT = "vscode_type_text"

@dataclass
class Client:
    id: str
    websocket: Any  # WebSocket connection object
    ip: str
    connected_at: datetime
    last_heartbeat: datetime
    user_session: Optional[str] = None
    capabilities: Dict[str, bool] = None
    hostname: Optional[str] = None
    platform: Optional[str] = None
    client_start_time: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip': self.ip,
            'connected_at': self.connected_at.isoformat(),
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'connection_duration': str(datetime.now() - self.connected_at),
            'user_session': self.user_session,
            'hostname': self.hostname,
            'platform': self.platform,
            'client_start_time': self.client_start_time.isoformat() if self.client_start_time else None,
            'capabilities': self.capabilities or {}
        }

class CyberCorpServer:
    def __init__(self, host=None, port=None):
        # Load configuration
        self.config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        
        if os.path.exists(config_path):
            self.config.read(config_path)
            logger.info(f"Loaded configuration from {config_path}")
        else:
            logger.warning(f"Config file not found at {config_path}, using defaults")
        
        # Server configuration with fallbacks
        self.host = host or self.config.get('server', 'host', fallback='0.0.0.0')
        self.port = port or self.config.getint('server', 'port', fallback=9998)  # Changed default port
        self.clients: Dict[str, Client] = {}
        self.client_counter = 0
        self.command_queue: Dict[str, list] = {}  # Client ID -> Command queue
        self.command_results: Dict[str, dict] = {}  # Command ID -> Result
        
    async def start(self):
        """Start the WebSocket server"""
        logger.info(f"Starting CyberCorp Control Server on {self.host}:{self.port}")
        
        # Start maintenance tasks
        asyncio.create_task(self._heartbeat_monitor())
        asyncio.create_task(self._command_processor())
        
        # Start WebSocket server with compatibility options
        async with websockets.serve(
            self.handle_client, 
            self.host, 
            self.port,
            compression=None  # Disable compression for compatibility
        ):
            logger.info(f"Server listening on {self.host}:{self.port}")
            
            # Start console interface
            await self._console_interface()
    
    async def handle_client(self, websocket, path):
        """Handle a new client connection"""
        client_id = f"client_{self.client_counter}"
        self.client_counter += 1
        
        client = Client(
            id=client_id,
            websocket=websocket,
            ip=websocket.remote_address[0],
            connected_at=datetime.now(),
            last_heartbeat=datetime.now()
        )
        
        self.clients[client_id] = client
        self.command_queue[client_id] = []
        
        logger.info(f"Client {client_id} connected from {client.ip}")
        
        try:
            # Send welcome message
            await self._send_message(client, {
                'type': 'welcome',
                'client_id': client_id,
                'server_time': datetime.now().isoformat()
            })
            
            # Handle messages
            async for message in websocket:
                await self._handle_message(client, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            # Cleanup
            del self.clients[client_id]
            del self.command_queue[client_id]
    
    async def _handle_message(self, client: Client, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'heartbeat':
                client.last_heartbeat = datetime.now()
                await self._send_message(client, {'type': 'heartbeat_ack'})
                
            elif msg_type == 'register':
                # Client registration with enhanced info
                client.user_session = data.get('user_session')
                client.capabilities = data.get('capabilities', {})
                client.hostname = data.get('system_info', {}).get('hostname')
                client.platform = data.get('system_info', {}).get('platform')
                client.client_start_time = datetime.fromisoformat(data.get('client_start_time')) if data.get('client_start_time') else None
                logger.info(f"Client {client.id} registered: user={client.user_session}, host={client.hostname}")
                
            elif msg_type == 'command_result':
                # Store command result
                command_id = data.get('command_id')
                if command_id:
                    self.command_results[command_id] = data.get('result')
                    logger.info(f"Received result for command {command_id}")
                
                # Forward result back to requesting client if it was a forwarded command
                # Check if there's a from_client field in the original message
                # For now, broadcast to all management clients
                for cid, c in self.clients.items():
                    if c.capabilities and c.capabilities.get('management'):
                        result_msg = {
                            'type': 'command_result',
                            'from_client': client.id,
                            'command_id': command_id,
                            'result': data.get('result'),
                            'error': data.get('error'),
                            'timestamp': data.get('timestamp')
                        }
                        await self._send_message(c, result_msg)
                    
            elif msg_type == 'status':
                # Client status update
                logger.info(f"Client {client.id} status: {data.get('status')}")
                
            elif msg_type == 'request':
                # Handle client requests
                command = data.get('command')
                if command == 'list_clients':
                    # Send list of all connected clients
                    client_list = []
                    for cid, c in self.clients.items():
                        client_info = {
                            'id': c.id,
                            'ip': c.ip,
                            'connected_at': c.connected_at.isoformat(),
                            'user_session': c.user_session,
                            'hostname': c.hostname,
                            'platform': c.platform,
                            'capabilities': c.capabilities or {},
                            'client_start_time': c.client_start_time.isoformat() if c.client_start_time else None
                        }
                        client_list.append(client_info)
                    
                    await self._send_message(client, {
                        'type': 'client_list',
                        'clients': client_list
                    })
                    logger.info(f"Sent client list to {client.id}: {len(client_list)} clients")
                
            elif msg_type == 'forward_command':
                # Forward command from one client to another
                target_client_id = data.get('target_client')
                command_data = data.get('command')
                
                if target_client_id and command_data:
                    if target_client_id in self.clients:
                        target_client = self.clients[target_client_id]
                        # Add source client info
                        command_data['from_client'] = client.id
                        await self._send_message(target_client, command_data)
                        logger.info(f"Forwarded command from {client.id} to {target_client_id}")
                        
                        # Send acknowledgment
                        await self._send_message(client, {
                            'type': 'forward_ack',
                            'target_client': target_client_id,
                            'status': 'sent'
                        })
                    else:
                        await self._send_message(client, {
                            'type': 'error',
                            'message': f'Target client {target_client_id} not found'
                        })
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client {client.id}")
        except Exception as e:
            logger.error(f"Error handling message from {client.id}: {e}")
    
    async def _send_message(self, client: Client, message: dict):
        """Send message to client"""
        try:
            await client.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to {client.id}: {e}")
    
    async def send_command(self, client_id: str, command: CommandType, params: dict = None):
        """Send command to specific client"""
        if client_id not in self.clients:
            logger.error(f"Client {client_id} not found")
            return None
            
        client = self.clients[client_id]
        command_id = f"cmd_{int(time.time() * 1000)}"
        
        message = {
            'type': 'command',
            'command_id': command_id,
            'command': command.value,
            'params': params or {}
        }
        
        await self._send_message(client, message)
        logger.info(f"Sent command {command.value} to {client_id}")
        
        return command_id
    
    async def _heartbeat_monitor(self):
        """Monitor client heartbeats"""
        while True:
            try:
                now = datetime.now()
                disconnected = []
                
                for client_id, client in self.clients.items():
                    if (now - client.last_heartbeat).total_seconds() > 60:
                        logger.warning(f"Client {client_id} heartbeat timeout")
                        disconnected.append(client_id)
                
                # Close timed out connections
                for client_id in disconnected:
                    if client_id in self.clients:
                        await self.clients[client_id].websocket.close()
                        
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                
            await asyncio.sleep(30)
    
    async def _command_processor(self):
        """Process queued commands"""
        while True:
            try:
                for client_id, queue in self.command_queue.items():
                    if queue and client_id in self.clients:
                        command = queue.pop(0)
                        await self.send_command(client_id, command['type'], command.get('params'))
                        
            except Exception as e:
                logger.error(f"Command processor error: {e}")
                
            await asyncio.sleep(0.1)
    
    async def _console_interface(self):
        """Interactive console for server control"""
        print("\n=== CyberCorp Control Server ===")
        print("Commands:")
        print("  list - List connected clients")
        print("  info <client_id> - Show client info")
        print("  cmd <client_id> <command> [params] - Send command")
        print("  vscode <client_id> - Control VSCode")
        print("  help - Show this help")
        print("  exit - Stop server")
        print()
        
        while True:
            try:
                # Non-blocking input
                command = await asyncio.get_event_loop().run_in_executor(
                    None, input, "server> "
                )
                
                parts = command.strip().split()
                if not parts:
                    continue
                    
                cmd = parts[0].lower()
                
                if cmd == 'exit':
                    logger.info("Server shutdown requested")
                    break
                    
                elif cmd == 'list':
                    print(f"\nConnected clients ({len(self.clients)}):")
                    print("-" * 80)
                    for client_id, client in self.clients.items():
                        info = client.to_dict()
                        print(f"  ID: {client_id}")
                        print(f"    User: {info['user_session']} @ {info['hostname']}")
                        print(f"    IP: {info['ip']}")
                        print(f"    Connected: {info['connection_duration']} ago")
                        print(f"    Platform: {info['platform']}")
                        print(f"    Capabilities: {', '.join(k for k, v in info['capabilities'].items() if v)}")
                        print()
                        
                elif cmd == 'info' and len(parts) > 1:
                    client_id = parts[1]
                    if client_id in self.clients:
                        client = self.clients[client_id]
                        print(f"\nClient {client_id}:")
                        print(f"  IP: {client.ip}")
                        print(f"  Connected: {client.connected_at}")
                        print(f"  Session: {client.user_session}")
                        print(f"  Capabilities: {client.capabilities}")
                    else:
                        print(f"Client {client_id} not found")
                        
                elif cmd == 'cmd' and len(parts) >= 3:
                    client_id = parts[1]
                    command_name = parts[2]
                    params = ' '.join(parts[3:]) if len(parts) > 3 else None
                    
                    try:
                        command_type = CommandType(command_name)
                        cmd_id = await self.send_command(client_id, command_type, {'data': params})
                        print(f"Command sent with ID: {cmd_id}")
                    except ValueError:
                        print(f"Unknown command: {command_name}")
                        
                elif cmd == 'vscode' and len(parts) > 1:
                    client_id = parts[1]
                    await self._vscode_control(client_id)
                    
                elif cmd == 'help':
                    print("\nAvailable commands:")
                    for cmd_type in CommandType:
                        print(f"  {cmd_type.value}")
                        
                else:
                    print("Unknown command. Type 'help' for help.")
                    
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Console error: {e}")
    
    async def _vscode_control(self, client_id: str):
        """Interactive VSCode control mode"""
        print("\n=== VSCode Control Mode ===")
        print("Commands:")
        print("  content - Get current VSCode content")
        print("  type <text> - Type text in VSCode")
        print("  cmd <command> - Send VSCode command")
        print("  back - Return to main menu")
        print()
        
        while True:
            try:
                command = await asyncio.get_event_loop().run_in_executor(
                    None, input, "vscode> "
                )
                
                parts = command.strip().split()
                if not parts:
                    continue
                    
                cmd = parts[0].lower()
                
                if cmd == 'back':
                    break
                    
                elif cmd == 'content':
                    await self.send_command(client_id, CommandType.VSCODE_GET_CONTENT)
                    
                elif cmd == 'type' and len(parts) > 1:
                    text = ' '.join(parts[1:])
                    await self.send_command(client_id, CommandType.VSCODE_TYPE_TEXT, {'text': text})
                    
                elif cmd == 'cmd' and len(parts) > 1:
                    vscode_cmd = ' '.join(parts[1:])
                    await self.send_command(client_id, CommandType.VSCODE_SEND_COMMAND, {'command': vscode_cmd})
                    
            except Exception as e:
                logger.error(f"VSCode control error: {e}")

if __name__ == "__main__":
    server = CyberCorpServer()
    asyncio.run(server.start())