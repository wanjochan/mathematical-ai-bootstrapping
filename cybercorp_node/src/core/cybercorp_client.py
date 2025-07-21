"""Base WebSocket client for CyberCorp Node system"""

import asyncio
import websockets
import json
import os
import platform
from datetime import datetime
from typing import Optional, Dict, Any


class CyberCorpClient:
    """Base WebSocket client for CyberCorp Node system
    
    Handles connection, registration, and basic communication with the server.
    """
    
    def __init__(self, client_type: str = "controller", port: int = 9998, 
                 user_session: Optional[str] = None):
        """Initialize CyberCorp client
        
        Args:
            client_type: Type of client ("controller", "worker", etc.)
            port: Server port (default: 9998)
            user_session: Custom user session name (default: auto-generated)
        """
        self.server_url = f'ws://localhost:{port}'
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.client_id: Optional[str] = None
        self.client_type = client_type
        self.user_session = user_session or self._generate_session_name()
        self.is_connected = False
        
    def _generate_session_name(self) -> str:
        """Generate default session name based on username and client type"""
        username = os.environ.get('USERNAME', 'unknown')
        return f"{username}_{self.client_type}"
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for registration"""
        return {
            'platform': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'node': platform.node()
        }
        
    async def connect(self, capabilities: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Connect to server and register client
        
        Args:
            capabilities: Client capabilities (default: based on client_type)
            
        Returns:
            Welcome message from server
            
        Raises:
            Exception: If connection or registration fails
        """
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            # Default capabilities based on client type
            if capabilities is None:
                if self.client_type == "controller":
                    capabilities = {'management': True}
                else:
                    capabilities = {
                        'vscode_control': True,
                        'system_info': True,
                        'process_management': True,
                        'ui_automation': True
                    }
            
            # Send registration
            registration = {
                'type': 'register',
                'user_session': self.user_session,
                'client_type': self.client_type,
                'client_start_time': datetime.now().isoformat(),
                'capabilities': capabilities,
                'system_info': self._get_system_info()
            }
            
            await self.websocket.send(json.dumps(registration))
            
            # Wait for welcome message
            welcome_msg = await self.websocket.recv()
            welcome_data = json.loads(welcome_msg)
            
            if welcome_data.get('type') == 'welcome':
                self.client_id = welcome_data.get('client_id')
                self.is_connected = True
                return welcome_data
            else:
                raise Exception(f"Unexpected response: {welcome_data}")
                
        except Exception as e:
            self.is_connected = False
            raise Exception(f"Failed to connect: {e}")
            
    async def disconnect(self):
        """Disconnect from server gracefully"""
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        self.is_connected = False
        self.client_id = None
        
    async def send_request(self, request_type: str, command: Optional[str] = None, 
                          params: Optional[Dict[str, Any]] = None, 
                          timeout: float = 5.0) -> Dict[str, Any]:
        """Send request and wait for response
        
        Args:
            request_type: Type of request ('request', 'forward_command', etc.)
            command: Command name (for 'request' type)
            params: Additional parameters
            timeout: Response timeout in seconds
            
        Returns:
            Response data from server
            
        Raises:
            asyncio.TimeoutError: If response times out
            Exception: If not connected or other errors
        """
        if not self.is_connected or not self.websocket:
            raise Exception("Not connected to server")
            
        # Build request
        request = {'type': request_type}
        if command:
            request['command'] = command
        if params:
            request.update(params)
            
        # Send request
        await self.websocket.send(json.dumps(request))
        
        # Wait for response with timeout
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            return json.loads(response)
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Timeout waiting for response to {request_type}")
            
    async def send_raw(self, data: Dict[str, Any]):
        """Send raw data without waiting for response
        
        Args:
            data: Data to send
            
        Raises:
            Exception: If not connected
        """
        if not self.is_connected or not self.websocket:
            raise Exception("Not connected to server")
            
        await self.websocket.send(json.dumps(data))
        
    async def receive_raw(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Receive raw data from server
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            Received data
            
        Raises:
            asyncio.TimeoutError: If timeout specified and exceeded
            Exception: If not connected
        """
        if not self.is_connected or not self.websocket:
            raise Exception("Not connected to server")
            
        if timeout:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
        else:
            response = await self.websocket.recv()
            
        return json.loads(response)
        
    async def heartbeat_loop(self, interval: float = 30.0):
        """Send periodic heartbeat to keep connection alive
        
        Args:
            interval: Heartbeat interval in seconds
        """
        while self.is_connected:
            try:
                await self.send_raw({'type': 'heartbeat'})
                await asyncio.sleep(interval)
            except Exception:
                # Connection lost
                self.is_connected = False
                break