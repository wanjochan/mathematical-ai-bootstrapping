"""Direct input to Cursor using mouse and keyboard"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def direct_cursor_input():
    """Direct input to Cursor"""
    server_url = 'ws://localhost:9998'
    
    async with websockets.connect(server_url) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_direct",
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
        
        # Step 1: Activate Cursor window
        cursor_hwnd = 5898916
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
        await asyncio.sleep(2)
        
        # Step 2: Click on the right side where chat usually is
        # Assuming 1920x1080 resolution, chat is typically on the right
        print("\n[2] Clicking on chat area (right side)...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'mouse_click',
                'params': {
                    'x': 1600,  # Right side of screen
                    'y': 600,   # Middle height
                    'button': 'left'
                }
            }
        }))
        
        await ws.recv()  # ack
        await asyncio.sleep(1)
        
        # Step 3: Clear any existing text with Ctrl+A and Delete
        print("\n[3] Clearing input area...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '^a{DELETE}'}  # Ctrl+A then Delete
            }
        }))
        
        await ws.recv()  # ack
        await asyncio.sleep(0.5)
        
        # Step 4: Type the text
        print("\n[4] Typing text...")
        text = """阅读workflow.md了解工作流；
启动新job(work_id=cybercorp_dashboard)，在现有的cybercorp_web/里面加入dashboard功能，用来观察所有的受控端信息
做好之后打开网站测试看看效果"""
        
        # Send text line by line
        lines = text.split('\n')
        for i, line in enumerate(lines):
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
            
            # Add line break except for last line
            if i < len(lines) - 1:
                await ws.send(json.dumps({
                    'type': 'forward_command',
                    'target_client': client_id,
                    'command': {
                        'type': 'command',
                        'command': 'send_keys',
                        'params': {'keys': '+{ENTER}'}  # Shift+Enter for new line in chat
                    }
                }))
                await ws.recv()  # ack
            
            await asyncio.sleep(0.2)
        
        print("\n[5] Text typed!")
        
        # Step 5: Send with Enter
        print("\n[6] Sending message...")
        await asyncio.sleep(1)
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '{ENTER}'}  # Enter to send
            }
        }))
        
        await ws.recv()  # ack
        
        print("\n[SUCCESS] Message sent to Cursor!")
        print("\nNow let's take a screenshot to see the result...")
        
        # Take screenshot
        await asyncio.sleep(3)  # Wait for Cursor to process
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'take_screenshot'
            }
        }))
        
        await ws.recv()  # ack
        
        print("\nMonitoring Cursor's progress...")
        
        # Keep monitoring
        start_time = datetime.now()
        while True:
            try:
                elapsed = (datetime.now() - start_time).seconds
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Monitoring... ({elapsed}s elapsed)", end='')
                await asyncio.sleep(30)
            except KeyboardInterrupt:
                print("\n\nStopping monitor...")
                break

if __name__ == "__main__":
    asyncio.run(direct_cursor_input())