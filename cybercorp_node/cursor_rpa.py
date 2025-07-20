"""RPA script to control Cursor IDE"""

import asyncio
import websockets
import json
import os
import time
from datetime import datetime

class CursorController:
    """Controller for Cursor IDE"""
    
    def __init__(self):
        self.server_url = 'ws://localhost:9998'
        self.websocket = None
        self.target_username = 'wjchk'
        self.client_id = None
        
    async def connect(self) -> bool:
        """Connect to server and find target client"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            # Register as management client
            await self.websocket.send(json.dumps({
                'type': 'register',
                'user_session': f"{os.environ.get('USERNAME', 'unknown')}_cursor_rpa",
                'client_start_time': datetime.now().isoformat(),
                'capabilities': {'management': True, 'control': True},
                'system_info': {
                    'platform': 'Windows',
                    'hostname': os.environ.get('COMPUTERNAME', 'unknown')
                }
            }))
            
            # Wait for welcome
            welcome = await self.websocket.recv()
            print(f"Connected: {json.loads(welcome)['client_id']}")
            
            # Request client list
            await self.websocket.send(json.dumps({
                'type': 'request',
                'command': 'list_clients'
            }))
            
            # Wait for client list
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'client_list':
                print(f"Found {len(data['clients'])} clients")
                for client in data['clients']:
                    print(f"  - {client.get('user_session', 'unknown')} (ID: {client['id']})")
                    if client.get('user_session') == self.target_username:
                        self.client_id = client['id']
                        print(f"[OK] Found target client: {self.client_id}")
                        return True
                        
            print(f"[ERROR] Client '{self.target_username}' not found")
            return False
            
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    async def send_to_cursor(self, text: str):
        """Send text to Cursor IDE"""
        if not self.client_id:
            print("[ERROR] No client connected")
            return False
            
        try:
            # Step 1: Get windows to find Cursor
            print("\n[STEP 1] Finding Cursor window...")
            await self.websocket.send(json.dumps({
                'type': 'forward_command',
                'target_client': self.client_id,
                'command': {
                    'type': 'command',
                    'command': 'get_windows'
                }
            }))
            
            # Get acknowledgment
            ack = await self.websocket.recv()
            print(f"Command sent: {json.loads(ack).get('status')}")
            
            # Wait for windows result
            result = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            windows_data = json.loads(result)
            
            if windows_data.get('type') != 'command_result':
                print(f"[ERROR] Unexpected response: {windows_data}")
                return False
                
            windows = windows_data.get('result', [])
            print(f"Found {len(windows)} windows")
            
            # Find Cursor window
            cursor_window = None
            for w in windows:
                title = w.get('title', '').lower()
                if 'cursor' in title:
                    cursor_window = w
                    print(f"[OK] Found Cursor: {w['title']}")
                    break
                    
            if not cursor_window:
                print("[ERROR] Cursor window not found")
                print("Available windows (first 10):")
                for w in windows[:10]:
                    print(f"  - {w.get('title', 'No title')}")
                return False
                
            # Step 2: Activate Cursor window
            print("\n[STEP 2] Activating Cursor window...")
            await self.websocket.send(json.dumps({
                'type': 'forward_command',
                'target_client': self.client_id,
                'command': {
                    'type': 'command',
                    'command': 'activate_window',
                    'params': {'hwnd': cursor_window['hwnd']}
                }
            }))
            
            # Wait for activation
            await self.websocket.recv()  # ack
            await asyncio.wait_for(self.websocket.recv(), timeout=2.0)  # result
            print("[OK] Window activated")
            
            # Wait for window to be ready
            await asyncio.sleep(1)
            
            # Step 3: Send text
            print("\n[STEP 3] Sending text to Cursor...")
            await self.websocket.send(json.dumps({
                'type': 'forward_command',
                'target_client': self.client_id,
                'command': {
                    'type': 'command',
                    'command': 'send_keys',
                    'params': {'keys': text}
                }
            }))
            
            await self.websocket.recv()  # ack
            await asyncio.wait_for(self.websocket.recv(), timeout=5.0)  # result
            print("[OK] Text sent")
            
            # Step 4: Send Enter key
            print("\n[STEP 4] Sending Enter key...")
            await self.websocket.send(json.dumps({
                'type': 'forward_command',
                'target_client': self.client_id,
                'command': {
                    'type': 'command',
                    'command': 'send_keys',
                    'params': {'keys': '{ENTER}'}
                }
            }))
            
            await self.websocket.recv()  # ack
            await asyncio.wait_for(self.websocket.recv(), timeout=2.0)  # result
            print("[OK] Enter key sent")
            
            return True
            
        except asyncio.TimeoutError:
            print("[ERROR] Command timed out")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to send to Cursor: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    async def close(self):
        """Close connection"""
        if self.websocket:
            await self.websocket.close()
            
async def main():
    """Main function"""
    controller = CursorController()
    
    # Connect to server
    if not await controller.connect():
        print("Failed to connect")
        return
        
    # The text to send
    text = """阅读workflow.md了解工作流；
启动新job(work_id=cybercorp_dashboard)，在现有的cybercorp_web/里面加入dashboard功能，用来观察所有的受控端信息
做好之后打开网站测试看看效果"""
    
    # Send to Cursor
    success = await controller.send_to_cursor(text)
    
    if success:
        print("\n[SUCCESS] Text sent to Cursor successfully!")
        print("Now monitoring Cursor's progress...")
        
        # Keep connection alive for monitoring
        try:
            while True:
                await asyncio.sleep(30)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring...")
        except KeyboardInterrupt:
            print("\nStopping monitor...")
    else:
        print("\n[FAILED] Could not send text to Cursor")
        
    await controller.close()

if __name__ == "__main__":
    asyncio.run(main())