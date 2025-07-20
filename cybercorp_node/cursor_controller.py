"""Universal Cursor IDE controller with dynamic monitoring"""

import asyncio
import websockets
import json
import os
import sys
import argparse
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

class CursorController:
    def __init__(self, target_user, server_url='ws://localhost:9998'):
        self.target_user = target_user
        self.server_url = server_url
        self.client_id = None
        self.cursor_hwnd = None
        self.ws = None
        
    async def connect(self):
        """Connect to server and find target client"""
        self.ws = await websockets.connect(self.server_url)
        
        # Register
        await self.ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_cursor_ctrl",
            'client_start_time': datetime.now().isoformat(),
            'capabilities': {'management': True}
        }))
        
        welcome = await self.ws.recv()
        safe_print(f"Connected as: {json.loads(welcome)['client_id']}")
        
        # Get client list
        await self.ws.send(json.dumps({
            'type': 'request',
            'command': 'list_clients'
        }))
        
        response = await self.ws.recv()
        data = json.loads(response)
        
        # Find target user
        safe_print(f"\nLooking for user: {self.target_user}")
        for client in data.get('clients', []):
            if client.get('user_session') == self.target_user:
                self.client_id = client['id']
                safe_print(f"Found {self.target_user}: {self.client_id}")
                break
                
        if not self.client_id:
            raise Exception(f"Client '{self.target_user}' not found")
            
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
                    return True
                    
        return False
        
    async def get_uia_structure(self):
        """Get Cursor UIA structure"""
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
        
    async def send_to_chat(self, text):
        """Send text to Cursor chat"""
        safe_print(f"\nSending: {text}")
        
        # Activate window
        await self.ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'activate_window',
                'params': {'hwnd': self.cursor_hwnd}
            }
        }))
        await self.ws.recv()
        await asyncio.sleep(1)
        
        # Click on chat area
        await self.ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'send_mouse_click',
                'params': {'x': 1600, 'y': 700}
            }
        }))
        await self.ws.recv()
        await asyncio.sleep(0.5)
        
        # Clear and type
        await self.ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '^a{DELETE}'}
            }
        }))
        await self.ws.recv()
        await asyncio.sleep(0.3)
        
        # Send text
        for line in text.split('\n'):
            await self.ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': self.client_id,
                'command': {
                    'type': 'command',
                    'command': 'send_keys',
                    'params': {'keys': line}
                }
            }))
            await self.ws.recv()
            
            # Add line break if needed
            if '\n' in text and line != text.split('\n')[-1]:
                await self.ws.send(json.dumps({
                    'type': 'forward_command',
                    'target_client': self.client_id,
                    'command': {
                        'type': 'command',
                        'command': 'send_keys',
                        'params': {'keys': '+{ENTER}'}
                    }
                }))
                await self.ws.recv()
            
            await asyncio.sleep(0.1)
        
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
        await self.ws.recv()
        safe_print("Message sent!")
        
    async def monitor_content(self, interval=10):
        """Monitor Cursor content changes"""
        safe_print(f"\nMonitoring Cursor every {interval} seconds...")
        
        check_count = 0
        while True:
            try:
                await asyncio.sleep(interval)
                check_count += 1
                
                safe_print(f"\n[Check #{check_count}] Getting Cursor state...")
                
                structure = await self.get_uia_structure()
                if structure:
                    # Extract visible texts
                    texts = []
                    
                    def extract_texts(node):
                        if isinstance(node, dict):
                            if 'Name' in node and node['Name']:
                                texts.append(node['Name'])
                            if 'Texts' in node:
                                texts.extend(node['Texts'])
                            for child in node.get('Children', {}).values():
                                extract_texts(child)
                                
                    extract_texts(structure)
                    
                    # Show meaningful content
                    meaningful = [t for t in texts if len(t) > 20 and not t.startswith('(')]
                    if meaningful:
                        safe_print("Current content:")
                        for text in meaningful[:10]:
                            if len(text) > 100:
                                safe_print(f"  {text[:100]}...")
                            else:
                                safe_print(f"  {text}")
                                
                    # Save snapshot periodically
                    if check_count % 5 == 0:
                        filename = f"cursor_snapshot_{self.target_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(structure, f, indent=2, ensure_ascii=False)
                        safe_print(f"Saved snapshot: {filename}")
                        
            except KeyboardInterrupt:
                safe_print("\nMonitoring stopped")
                break
            except Exception as e:
                safe_print(f"Monitor error: {e}")
                
    async def run(self, command=None, monitor=False):
        """Main execution"""
        try:
            await self.connect()
            
            if not await self.find_cursor_window():
                safe_print("Cursor window not found!")
                return
                
            if command:
                await self.send_to_chat(command)
                
            if monitor:
                await self.monitor_content()
                
        finally:
            if self.ws:
                await self.ws.close()

def main():
    parser = argparse.ArgumentParser(description='Control and monitor Cursor IDE')
    parser.add_argument('username', help='Target username (e.g., wjchk)')
    parser.add_argument('-c', '--command', help='Command to send to Cursor')
    parser.add_argument('-m', '--monitor', action='store_true', help='Monitor Cursor content')
    parser.add_argument('-i', '--interval', type=int, default=10, help='Monitor interval in seconds')
    parser.add_argument('-s', '--server', default='ws://localhost:9998', help='Server URL')
    
    args = parser.parse_args()
    
    controller = CursorController(args.username, args.server)
    
    # Run the controller
    asyncio.run(controller.run(command=args.command, monitor=args.monitor))

if __name__ == "__main__":
    main()