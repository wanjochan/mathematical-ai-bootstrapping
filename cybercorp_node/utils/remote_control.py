"""Remote control utilities for CyberCorp Node"""

import asyncio
import websockets
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from .window_cache import WindowCache

logger = logging.getLogger(__name__)


class RemoteController:
    """High-level remote control interface"""
    
    def __init__(self, server_url: str = 'ws://localhost:9998'):
        self.server_url = server_url
        self.ws = None
        self.client_id = None
        self.target_client = None
        self.window_cache = WindowCache(ttl=120)  # 2 minutes cache
        
    async def connect(self, session_name: str = None):
        """Connect to server"""
        if session_name is None:
            session_name = f"controller_{datetime.now().strftime('%H%M%S')}"
            
        self.ws = await websockets.connect(self.server_url)
        
        await self.ws.send(json.dumps({
            'type': 'register',
            'user_session': session_name,
            'client_start_time': datetime.now().isoformat(),
            'capabilities': {'management': True}
        }))
        
        welcome = await self.ws.recv()
        data = json.loads(welcome)
        self.client_id = data.get('client_id')
        logger.info(f"Connected as: {self.client_id}")
        
    async def find_client(self, user_session: str) -> Optional[str]:
        """Find client by user session"""
        await self.ws.send(json.dumps({
            'type': 'request',
            'command': 'list_clients'
        }))
        
        response = await self.ws.recv()
        data = json.loads(response)
        
        for client in data.get('clients', []):
            if client.get('user_session') == user_session:
                self.target_client = client['id']
                logger.info(f"Found {user_session}: {self.target_client}")
                return self.target_client
                
        logger.warning(f"Client {user_session} not found")
        return None
        
    async def execute_command(self, command: str, params: Dict[str, Any] = None, timeout: float = 10.0) -> Dict[str, Any]:
        """Execute command on target client"""
        if not self.target_client:
            raise RuntimeError("No target client set")
            
        await self.ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.target_client,
            'command': {
                'type': 'command',
                'command': command,
                'params': params or {}
            }
        }))
        
        # Get acknowledgment
        ack = await self.ws.recv()
        
        # Get result with timeout
        try:
            result = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            data = json.loads(result)
            
            if data.get('type') == 'command_result':
                return data.get('result', {})
            else:
                logger.warning(f"Unexpected response type: {data.get('type')}")
                return {'success': False, 'error': 'Unexpected response'}
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for command result")
            return {'success': False, 'error': 'Timeout'}
            
    async def get_windows(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get all windows"""
        result = await self.execute_command('get_windows')
        windows = result if isinstance(result, list) else []
        
        # Update cache if we got windows
        if windows and self.target_client:
            self.window_cache.set_windows(self.target_client, windows)
            
        return windows
        
    async def find_window(self, title_contains: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Find window by partial title match"""
        # Try cache first
        if use_cache and self.target_client:
            cached = self.window_cache.find_window(self.target_client, title_contains)
            if cached:
                logger.info(f"Found window in cache: {cached.get('title')}")
                return cached
                
        # Fall back to real lookup
        windows = await self.get_windows(use_cache=False)
        
        for window in windows:
            if title_contains.lower() in window.get('title', '').lower():
                return window
                
        return None
        
    async def activate_window(self, hwnd: int) -> bool:
        """Activate window"""
        result = await self.execute_command('activate_window', {'hwnd': hwnd})
        return result.get('success', False)
        
    async def click(self, x: int, y: int) -> bool:
        """Send mouse click"""
        result = await self.execute_command('send_mouse_click', {'x': x, 'y': y})
        return result.get('success', False)
        
    async def send_keys(self, keys: str, delay: float = 0.01) -> bool:
        """Send keyboard input"""
        result = await self.execute_command('send_keys', {'keys': keys, 'delay': delay})
        return result.get('success', False)
        
    async def screenshot(self, hwnd: int = None, save_path: str = None) -> Optional[str]:
        """Take screenshot"""
        params = {}
        if hwnd:
            params['hwnd'] = hwnd
        if save_path:
            params['save_path'] = save_path
            
        result = await self.execute_command('screenshot', params, timeout=15.0)
        
        if result.get('success'):
            return result.get('path')
        else:
            logger.error(f"Screenshot failed: {result.get('error')}")
            return None
            
    async def get_uia_structure(self, hwnd: int) -> Optional[Dict[str, Any]]:
        """Get UIA structure of window"""
        result = await self.execute_command('get_window_uia_structure', {'hwnd': hwnd}, timeout=30.0)
        
        if isinstance(result, dict) and 'error' not in result:
            return result
        else:
            logger.error(f"Failed to get UIA structure: {result}")
            return None
            
    async def close(self):
        """Close connection"""
        if self.ws:
            await self.ws.close()
            

class WindowController:
    """Control specific window"""
    
    def __init__(self, controller: RemoteController, hwnd: int, title: str = None):
        self.controller = controller
        self.hwnd = hwnd
        self.title = title or f"Window {hwnd}"
        
    async def activate(self) -> bool:
        """Activate this window"""
        return await self.controller.activate_window(self.hwnd)
        
    async def screenshot(self, filename: str = None) -> Optional[str]:
        """Take screenshot of this window"""
        if not filename:
            filename = f"{self.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
        return await self.controller.screenshot(self.hwnd, filename)
        
    async def click_at(self, x: int, y: int) -> bool:
        """Click at coordinates in this window"""
        # First activate window
        await self.activate()
        await asyncio.sleep(0.5)
        
        # Then click
        return await self.controller.click(x, y)
        
    async def type_text(self, text: str, clear_first: bool = True) -> bool:
        """Type text in this window"""
        if clear_first:
            # Clear existing text
            await self.controller.send_keys('^a{DELETE}')
            await asyncio.sleep(0.3)
            
        # Type new text
        return await self.controller.send_keys(text)
        
    async def send_command(self, text: str, input_coords: Tuple[int, int], clear_first: bool = True) -> bool:
        """Send command to specific input area"""
        # Click on input area
        success = await self.click_at(input_coords[0], input_coords[1])
        if not success:
            return False
            
        await asyncio.sleep(0.5)
        
        # Type text
        success = await self.type_text(text, clear_first)
        if not success:
            return False
            
        await asyncio.sleep(0.5)
        
        # Send Enter
        return await self.controller.send_keys('{ENTER}')
        

class BatchExecutor:
    """Execute commands in batch for efficiency"""
    
    def __init__(self, controller: RemoteController):
        self.controller = controller
        self.commands = []
        
    def add_command(self, command: str, params: Dict[str, Any] = None):
        """Add command to batch"""
        self.commands.append((command, params or {}))
        
    def add_click(self, x: int, y: int):
        """Add click command"""
        self.add_command('send_mouse_click', {'x': x, 'y': y})
        
    def add_keys(self, keys: str, delay: float = 0.01):
        """Add send keys command"""
        self.add_command('send_keys', {'keys': keys, 'delay': delay})
        
    def add_wait(self, seconds: float):
        """Add wait between commands"""
        self.commands.append(('wait', {'seconds': seconds}))
        
    async def execute(self) -> List[Dict[str, Any]]:
        """Execute all commands in sequence"""
        results = []
        
        for command, params in self.commands:
            if command == 'wait':
                await asyncio.sleep(params['seconds'])
                results.append({'success': True, 'waited': params['seconds']})
            else:
                result = await self.controller.execute_command(command, params)
                results.append(result)
                
        return results


# Convenience functions
async def quick_control(user_session: str, window_title: str) -> Tuple[RemoteController, WindowController]:
    """Quick setup for controlling a window"""
    controller = RemoteController()
    await controller.connect()
    
    # Find target client
    client_id = await controller.find_client(user_session)
    if not client_id:
        raise RuntimeError(f"Client {user_session} not found")
        
    # Find target window
    window = await controller.find_window(window_title)
    if not window:
        raise RuntimeError(f"Window containing '{window_title}' not found")
        
    window_ctrl = WindowController(controller, window['hwnd'], window['title'])
    return controller, window_ctrl