"""Monitor and control Cursor IDE dynamically"""

import asyncio
import websockets
import json
import os
import sys
from datetime import datetime
import time

# Set UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def safe_print(text):
    """Safe print that handles encoding issues"""
    try:
        print(text)
    except UnicodeEncodeError:
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text)

class CursorMonitor:
    def __init__(self):
        self.server_url = 'ws://localhost:9998'
        self.client_id = None
        self.cursor_hwnd = None
        self.ws = None
        self.last_content = None
        
    async def connect(self):
        """Connect to server and find wjchk client"""
        self.ws = await websockets.connect(self.server_url)
        
        # Register
        await self.ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_cursor_monitor",
            'client_start_time': datetime.now().isoformat(),
            'capabilities': {'management': True}
        }))
        
        welcome = await self.ws.recv()
        safe_print(f"Connected: {json.loads(welcome)['client_id']}")
        
        # Get client list
        await self.ws.send(json.dumps({
            'type': 'request',
            'command': 'list_clients'
        }))
        
        response = await self.ws.recv()
        data = json.loads(response)
        
        # Find wjchk
        for client in data.get('clients', []):
            if client.get('user_session') == 'wjchk':
                self.client_id = client['id']
                safe_print(f"Found wjchk: {self.client_id}")
                break
                
        if not self.client_id:
            raise Exception("wjchk client not found")
            
        # Find Cursor window
        await self.find_cursor_window()
        
    async def find_cursor_window(self):
        """Find Cursor window"""
        await self.ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'get_windows'
            }
        }))
        
        await self.ws.recv()  # ack
        result = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
        windows_data = json.loads(result)
        
        if windows_data.get('type') == 'command_result':
            windows = windows_data.get('result', [])
            for w in windows:
                if 'cursor' in w['title'].lower():
                    self.cursor_hwnd = w['hwnd']
                    safe_print(f"Found Cursor: {w['title']} (hwnd: {self.cursor_hwnd})")
                    return
                    
        raise Exception("Cursor window not found")
        
    async def get_cursor_content(self):
        """Get current Cursor UI content"""
        await self.ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'get_window_uia_structure',
                'params': {'hwnd': self.cursor_hwnd}
            }
        }))
        
        await self.ws.recv()  # ack
        
        try:
            result = await asyncio.wait_for(self.ws.recv(), timeout=30.0)
            uia_data = json.loads(result)
            
            if uia_data.get('type') == 'command_result':
                return uia_data.get('result', {})
        except:
            pass
            
        return None
        
    async def analyze_content_changes(self, current_content):
        """Analyze what changed in Cursor"""
        if not current_content:
            return
            
        # Extract all text content
        texts = []
        
        def extract_texts(node):
            if isinstance(node, dict):
                # Get node's own text
                name = node.get('Name', '')
                if name:
                    texts.append(name)
                    
                # Get texts array
                if 'Texts' in node:
                    texts.extend(node['Texts'])
                    
                # Process children
                for child in node.get('Children', {}).values():
                    extract_texts(child)
                    
        extract_texts(current_content)
        
        # Show meaningful texts (filter out UI element names)
        meaningful_texts = [t for t in texts if len(t) > 10 and not t.startswith('(') and not t.endswith(')')]
        
        if meaningful_texts:
            safe_print("\n--- Current visible content ---")
            for text in meaningful_texts[:20]:  # Show first 20
                if len(text) > 100:
                    safe_print(f"  {text[:100]}...")
                else:
                    safe_print(f"  {text}")
                    
        # Look for file paths
        file_paths = [t for t in texts if '.md' in t or '.js' in t or '.py' in t or '.json' in t]
        if file_paths:
            safe_print("\n--- Files mentioned ---")
            for path in file_paths:
                safe_print(f"  {path}")
                
    async def send_command(self, text):
        """Send a command to Cursor chat"""
        safe_print(f"\n[Sending command]: {text}")
        
        # Click on chat input area
        await self.ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'send_mouse_click',
                'params': {
                    'x': 1600,  # Right side where chat is
                    'y': 800    # Lower area for input
                }
            }
        }))
        
        await self.ws.recv()  # ack
        await asyncio.sleep(1)
        
        # Clear and type text
        await self.ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '^a{DELETE}'}
            }
        }))
        
        await self.ws.recv()  # ack
        await asyncio.sleep(0.5)
        
        # Type the command
        await self.ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': text}
            }
        }))
        
        await self.ws.recv()  # ack
        await asyncio.sleep(0.5)
        
        # Send with Enter
        await self.ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '{ENTER}'}
            }
        }))
        
        await self.ws.recv()  # ack
        safe_print("[Command sent]")
        
    async def monitor_loop(self):
        """Main monitoring loop"""
        safe_print("\n=== Starting Cursor monitoring ===\n")
        
        # First, check current state
        content = await self.get_cursor_content()
        if content:
            await self.analyze_content_changes(content)
            
        # Send the new command
        await self.send_command("打开docs/workflow.md文件，将其中过于谄媚的措辞修改得更加中立专业")
        
        # Monitor for changes
        monitor_count = 0
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                monitor_count += 1
                safe_print(f"\n[Monitor #{monitor_count}] Checking Cursor state...")
                
                # Get current content
                content = await self.get_cursor_content()
                if content:
                    await self.analyze_content_changes(content)
                    
                    # Save snapshot every 5 checks
                    if monitor_count % 5 == 0:
                        filename = f"cursor_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(content, f, indent=2, ensure_ascii=False)
                        safe_print(f"[Saved snapshot to {filename}]")
                        
            except KeyboardInterrupt:
                safe_print("\nMonitoring stopped by user")
                break
            except Exception as e:
                safe_print(f"Monitor error: {e}")
                
    async def run(self):
        """Main run method"""
        try:
            await self.connect()
            await self.monitor_loop()
        finally:
            if self.ws:
                await self.ws.close()

if __name__ == "__main__":
    monitor = CursorMonitor()
    asyncio.run(monitor.run())