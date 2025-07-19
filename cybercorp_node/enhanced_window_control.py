"""Enhanced window control for robust RPA"""

import asyncio
import websockets
import json
import os
import time
from datetime import datetime

class EnhancedWindowController:
    """Enhanced controller with better window management"""
    
    def __init__(self, username: str):
        self.username = username
        self.server_url = 'ws://localhost:9998'
        self.client_id = None
        self.websocket = None
        
    async def connect(self) -> bool:
        """Connect to server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            await self.websocket.send(json.dumps({
                'type': 'register',
                'user_session': f"{os.environ.get('USERNAME', 'unknown')}_enhanced_rpa",
                'client_start_time': datetime.now().isoformat(),
                'capabilities': {'management': True, 'control': True}
            }))
            
            await self.websocket.recv()
            
            # Find client
            await self.websocket.send(json.dumps({
                'type': 'request',
                'command': 'list_clients'
            }))
            
            response = await self.websocket.recv()
            data = json.loads(response)
            
            for client in data.get('clients', []):
                if client.get('user_session') == self.username:
                    self.client_id = client['id']
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    async def get_window_info(self) -> dict:
        """Get detailed window information"""
        
        # First get all windows
        await self.websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'get_windows'
            }
        }))
        
        await self.websocket.recv()
        
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=3.0)
            result = json.loads(response)
            
            if result.get('type') == 'command_result':
                windows = result.get('result', [])
                
                # Find VSCode window
                for window in windows:
                    if 'Visual Studio Code' in window.get('title', ''):
                        return {
                            'found': True,
                            'hwnd': window.get('hwnd'),
                            'title': window.get('title'),
                            'class': window.get('class')
                        }
                
                return {'found': False, 'windows': windows}
                
        except asyncio.TimeoutError:
            return {'found': False, 'error': 'timeout'}
    
    async def activate_vscode_multiple_methods(self) -> bool:
        """Try multiple methods to activate VSCode"""
        
        print("\nAttempting to activate VSCode window...")
        
        # Method 1: Standard activate_window
        print("  Method 1: Standard activation")
        await self.websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'activate_window'
            }
        }))
        
        await self.websocket.recv()
        await asyncio.sleep(1)
        
        # Method 2: Click on window title bar
        window_info = await self.get_window_info()
        if window_info.get('found'):
            print(f"  Found VSCode: {window_info.get('title')}")
            
            # Try clicking on the window
            print("  Method 2: Click on window")
            await self.websocket.send(json.dumps({
                'type': 'forward_command',
                'target_client': self.client_id,
                'command': {
                    'type': 'command',
                    'command': 'send_mouse_click',
                    'params': {'x': 400, 'y': 20}  # Title bar area
                }
            }))
            
            await self.websocket.recv()
            await asyncio.sleep(0.5)
        
        # Method 3: Alt+Tab to switch
        print("  Method 3: Alt+Tab switching")
        await self.websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '%{TAB}'}  # Alt+Tab
            }
        }))
        
        await self.websocket.recv()
        await asyncio.sleep(1)
        
        # Verify activation
        structure = await self.get_vscode_structure()
        if structure:
            is_active = structure.get('is_active', False)
            print(f"  Window active status: {is_active}")
            
            # Even if not marked as active, try to proceed
            # as the window might be ready for input
            return True
        
        return False
    
    async def get_vscode_structure(self) -> dict:
        """Get VSCode structure"""
        await self.websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'vscode_get_content'
            }
        }))
        
        await self.websocket.recv()
        
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=3.0)
            result = json.loads(response)
            if result.get('type') == 'command_result':
                return result.get('result', {})
        except:
            pass
            
        return {}
    
    async def type_in_roo_code(self, message: str) -> bool:
        """Type message in Roo Code with focus management"""
        
        print(f"\nTyping message: {message}")
        
        # Click in the general area of Roo Code input
        # Based on the structure, it's likely in the right panel
        print("  Clicking on Roo Code area")
        await self.websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'send_mouse_click',
                'params': {'x': 600, 'y': 500}  # Approximate Roo Code area
            }
        }))
        
        await self.websocket.recv()
        await asyncio.sleep(0.5)
        
        # Clear existing text
        print("  Clearing input")
        await self.websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '^a'}
            }
        }))
        
        await self.websocket.recv()
        await asyncio.sleep(0.2)
        
        # Type message
        print("  Typing text")
        await self.websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'vscode_type_text',
                'params': {'text': message}
            }
        }))
        
        await self.websocket.recv()
        result = await asyncio.wait_for(self.websocket.recv(), timeout=3.0)
        
        # Send message
        print("  Sending Enter")
        await self.websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '{ENTER}'}
            }
        }))
        
        await self.websocket.recv()
        
        return True

async def main():
    """Main function with enhanced control"""
    
    controller = EnhancedWindowController("wjchk")
    
    if not await controller.connect():
        print("Failed to connect")
        return
    
    print("Connected successfully")
    
    # Get window info first
    window_info = await controller.get_window_info()
    print(f"\nWindow search result: {window_info}")
    
    # Try activation
    if await controller.activate_vscode_multiple_methods():
        # Type message
        await controller.type_in_roo_code("分析一下当前的产品设计")
        print("\n[DONE] Message sent")
    else:
        print("\n[ERROR] Could not activate window")
    
    if controller.websocket:
        await controller.websocket.close()

if __name__ == "__main__":
    asyncio.run(main())