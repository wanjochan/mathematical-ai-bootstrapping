"""Quick test for Cursor control"""

import asyncio
import websockets
import json
from datetime import datetime

async def quick_test():
    """Direct test without framework"""
    ws = await websockets.connect('ws://localhost:9998')
    
    # Register
    await ws.send(json.dumps({
        'type': 'register',
        'user_session': 'quick_test',
        'client_start_time': datetime.now().isoformat(),
        'capabilities': {'management': True}
    }))
    
    await ws.recv()
    print("Connected")
    
    # Direct command to wjchk
    print("Taking screenshot of Cursor...")
    await ws.send(json.dumps({
        'type': 'forward_command',
        'target_client': 'client_79',
        'command': {
            'type': 'command',
            'command': 'screenshot',
            'params': {'hwnd': 5898916}
        }
    }))
    
    await ws.recv()  # ack
    result = await ws.recv()
    data = json.loads(result)
    
    if data.get('type') == 'command_result':
        res = data.get('result', {})
        if res.get('success'):
            print(f"Screenshot: {res.get('path')}")
    
    # Activate window
    print("\nActivating Cursor...")
    await ws.send(json.dumps({
        'type': 'forward_command',
        'target_client': 'client_79',
        'command': {
            'type': 'command',
            'command': 'activate_window',
            'params': {'hwnd': 5898916}
        }
    }))
    await ws.recv()
    await ws.recv()
    
    # Click on chat input
    print("Clicking chat input...")
    await ws.send(json.dumps({
        'type': 'forward_command',
        'target_client': 'client_79',
        'command': {
            'type': 'command',
            'command': 'send_mouse_click',
            'params': {'x': 1495, 'y': 112}
        }
    }))
    await ws.recv()
    await ws.recv()
    
    await asyncio.sleep(0.5)
    
    # Clear and type
    print("Typing command...")
    await ws.send(json.dumps({
        'type': 'forward_command',
        'target_client': 'client_79',
        'command': {
            'type': 'command',
            'command': 'send_keys',
            'params': {'keys': '^a{DELETE}'}
        }
    }))
    await ws.recv()
    await ws.recv()
    
    await asyncio.sleep(0.3)
    
    # Type text
    await ws.send(json.dumps({
        'type': 'forward_command',
        'target_client': 'client_79',
        'command': {
            'type': 'command',
            'command': 'send_keys',
            'params': {'keys': '打开docs/workflow.md文件，将其中过于谄媚的措辞修改得更加中立专业'}
        }
    }))
    await ws.recv()
    await ws.recv()
    
    await asyncio.sleep(0.5)
    
    # Send Enter
    print("Sending Enter...")
    await ws.send(json.dumps({
        'type': 'forward_command',
        'target_client': 'client_79',
        'command': {
            'type': 'command',
            'command': 'send_keys',
            'params': {'keys': '{ENTER}'}
        }
    }))
    await ws.recv()
    await ws.recv()
    
    print("Done!")
    
    # Final screenshot
    await asyncio.sleep(3)
    print("\nTaking final screenshot...")
    await ws.send(json.dumps({
        'type': 'forward_command',
        'target_client': 'client_79',
        'command': {
            'type': 'command',
            'command': 'screenshot',
            'params': {'hwnd': 5898916}
        }
    }))
    await ws.recv()
    result = await ws.recv()
    data = json.loads(result)
    
    if data.get('type') == 'command_result':
        res = data.get('result', {})
        if res.get('success'):
            print(f"Final screenshot: {res.get('path')}")
    
    await ws.close()

if __name__ == "__main__":
    asyncio.run(quick_test())