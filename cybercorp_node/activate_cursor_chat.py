"""Activate Cursor Chat and send text"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def activate_cursor_chat():
    """Activate Cursor chat interface and send text"""
    server_url = 'ws://localhost:9998'
    
    async with websockets.connect(server_url) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_cursor_chat",
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
        
        # The Cursor window hwnd we found earlier
        cursor_hwnd = 5898916
        
        # Step 1: Activate Cursor window
        print("\n[STEP 1] Activating Cursor window...")
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
            await asyncio.wait_for(ws.recv(), timeout=2.0)  # result
            print("[OK] Window activated")
        except asyncio.TimeoutError:
            print("[WARN] Activation timeout")
            
        await asyncio.sleep(1)
        
        # Step 2: Open Command Palette with Ctrl+Shift+P
        print("\n[STEP 2] Opening Command Palette...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '^+p'}  # Ctrl+Shift+P
            }
        }))
        
        await ws.recv()  # ack
        try:
            await asyncio.wait_for(ws.recv(), timeout=2.0)
            print("[OK] Command Palette opened")
        except asyncio.TimeoutError:
            print("[WARN] Command Palette timeout")
            
        await asyncio.sleep(0.5)
        
        # Step 3: Type "Cursor Chat" to open chat
        print("\n[STEP 3] Opening Cursor Chat...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': 'Cursor Chat'}
            }
        }))
        
        await ws.recv()  # ack
        try:
            await asyncio.wait_for(ws.recv(), timeout=2.0)
            print("[OK] Typed 'Cursor Chat'")
        except asyncio.TimeoutError:
            print("[WARN] Type timeout")
            
        await asyncio.sleep(0.5)
        
        # Step 4: Press Enter to execute
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
        try:
            await asyncio.wait_for(ws.recv(), timeout=2.0)
            print("[OK] Chat opened")
        except asyncio.TimeoutError:
            print("[WARN] Enter timeout")
            
        await asyncio.sleep(2)  # Wait for chat to open
        
        # Step 5: Send the actual text
        print("\n[STEP 5] Sending text to Chat...")
        text = """阅读workflow.md了解工作流；
启动新job(work_id=cybercorp_dashboard)，在现有的cybercorp_web/里面加入dashboard功能，用来观察所有的受控端信息
做好之后打开网站测试看看效果"""
        
        # Use clipboard method for multi-line text
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'copy_to_clipboard',
                'params': {'text': text}
            }
        }))
        
        await ws.recv()  # ack
        try:
            await asyncio.wait_for(ws.recv(), timeout=2.0)
            print("[OK] Text copied to clipboard")
        except asyncio.TimeoutError:
            print("[WARN] Copy timeout, continuing...")
            
        await asyncio.sleep(0.5)
        
        # Paste with Ctrl+V
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': '^v'}  # Ctrl+V
            }
        }))
        
        await ws.recv()  # ack
        try:
            await asyncio.wait_for(ws.recv(), timeout=2.0)
            print("[OK] Text pasted")
        except asyncio.TimeoutError:
            print("[WARN] Paste timeout")
            
        await asyncio.sleep(0.5)
        
        # Step 6: Send Enter to submit
        print("\n[STEP 6] Submitting to Chat...")
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
        try:
            await asyncio.wait_for(ws.recv(), timeout=2.0)
            print("[OK] Text submitted to Cursor Chat!")
        except asyncio.TimeoutError:
            print("[WARN] Submit timeout")
            
        print("\n[SUCCESS] Task completed! Cursor should now be processing the request.")
        print("\nNow monitoring progress...")
        
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
    asyncio.run(activate_cursor_chat())