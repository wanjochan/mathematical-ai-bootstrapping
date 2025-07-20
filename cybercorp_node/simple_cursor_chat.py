"""Simple approach to send text to Cursor"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def send_to_cursor():
    """Send text to Cursor using simple approach"""
    server_url = 'ws://localhost:9998'
    
    async with websockets.connect(server_url) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_simple",
            'client_start_time': datetime.now().isoformat(),
            'capabilities': {'management': True}
        }))
        
        welcome = await ws.recv()
        print(f"Connected: {json.loads(welcome)['client_id']}")
        
        # Get client list
        await ws.send(json.dumps({
            'type': 'request',
            'command': 'list_clients'
        }))
        
        response = await ws.recv()
        data = json.loads(response)
        
        # Find wjchk
        client_id = None
        if data.get('type') == 'client_list':
            for client in data['clients']:
                if client.get('user_session') == 'wjchk':
                    client_id = client['id']
                    break
                    
        if not client_id:
            print("wjchk not found")
            return
            
        print(f"Found wjchk: {client_id}")
        
        cursor_hwnd = 5898916  # Cursor window hwnd
        
        # Simple approach: Activate window and use Ctrl+K to open inline chat
        print("\n[1] Activating Cursor window...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'activate_window',
                'params': {'hwnd': cursor_hwnd}
            }
        }))
        
        await ws.recv()  # ack
        await asyncio.sleep(2)  # Give it time
        
        # Try Ctrl+K (common shortcut for inline chat/command in many editors)
        print("\n[2] Opening inline chat with Ctrl+K...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '^k'}  # Ctrl+K
            }
        }))
        
        await ws.recv()  # ack
        await asyncio.sleep(1)
        
        # Send the text directly
        print("\n[3] Sending text...")
        text = """阅读workflow.md了解工作流；
启动新job(work_id=cybercorp_dashboard)，在现有的cybercorp_web/里面加入dashboard功能，用来观察所有的受控端信息
做好之后打开网站测试看看效果"""
        
        # Try sending text character by character with small delays
        for line in text.split('\n'):
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'send_keys',
                    'params': {'keys': line}
                }
            }))
            await ws.recv()  # ack
            await asyncio.sleep(0.1)
            
            # Send Enter after each line
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'send_keys',
                    'params': {'keys': '{ENTER}'}
                }
            }))
            await ws.recv()  # ack
            await asyncio.sleep(0.1)
        
        print("\n[4] Text sent!")
        
        # Try another Enter to submit
        await asyncio.sleep(1)
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '{ENTER}'}
            }
        }))
        await ws.recv()
        
        print("\n[SUCCESS] Completed!")

if __name__ == "__main__":
    asyncio.run(send_to_cursor())