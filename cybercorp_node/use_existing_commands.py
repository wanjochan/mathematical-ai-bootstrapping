"""Use existing commands to interact with Cursor"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def interact_with_cursor():
    """Interact with Cursor using existing commands"""
    server_url = 'ws://localhost:9998'
    
    async with websockets.connect(server_url) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_existing",
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
        
        # Step 1: Activate Cursor window using hwnd
        cursor_hwnd = 5898916
        print(f"\n[1] Activating Cursor window (hwnd: {cursor_hwnd})...")
        
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
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=5.0)
            print("Window activated")
        except:
            print("Activation timeout")
            
        await asyncio.sleep(2)  # Wait for window to be ready
        
        # Step 2: Since Chat is on the right side, click on the right side of the window
        print("\n[2] Clicking on the right side where Chat should be...")
        
        # Click at approximately 75% width to hit the right panel
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_mouse_click',
                'params': {
                    'x': 1440,  # 75% of 1920
                    'y': 600    # Middle height
                }
            }
        }))
        
        await ws.recv()  # ack
        try:
            await asyncio.wait_for(ws.recv(), timeout=2.0)
            print("Clicked on chat area")
        except:
            pass
            
        await asyncio.sleep(1)
        
        # Step 3: Clear existing text and type new text
        print("\n[3] Clearing and typing text...")
        
        # Clear with Ctrl+A and Delete
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '^a{DELETE}'}
            }
        }))
        
        await ws.recv()  # ack
        await asyncio.sleep(0.5)
        
        # Type the text
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
            
            # Add line break with Shift+Enter (except last line)
            if i < len(lines) - 1:
                await ws.send(json.dumps({
                    'type': 'forward_command',
                    'target_client': client_id,
                    'command': {
                        'type': 'command',
                        'command': 'send_keys',
                        'params': {'keys': '+{ENTER}'}  # Shift+Enter
                    }
                }))
                await ws.recv()  # ack
            
            await asyncio.sleep(0.2)
        
        print("\n[4] Text typed successfully!")
        
        # Step 4: Send with Enter
        await asyncio.sleep(1)
        print("\n[5] Sending message...")
        
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
        
        print("\n[SUCCESS] Message sent to Cursor Chat!")
        
        # Take a screenshot to verify
        print("\n[6] Taking screenshot...")
        await asyncio.sleep(3)
        
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'take_screenshot'
            }
        }))
        
        await ws.recv()  # ack
        try:
            screenshot_result = await asyncio.wait_for(ws.recv(), timeout=5.0)
            print("Screenshot taken")
        except:
            print("Screenshot timeout")
        
        # Monitor progress
        print("\n[7] Monitoring Cursor's progress...")
        start_time = datetime.now()
        
        while True:
            try:
                elapsed = (datetime.now() - start_time).seconds
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Monitoring... ({elapsed}s elapsed)", end='')
                await asyncio.sleep(30)
            except KeyboardInterrupt:
                print("\n\nStopped by user")
                break

if __name__ == "__main__":
    asyncio.run(interact_with_cursor())