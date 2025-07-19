"""Send a message to Roo Code in VSCode"""

import asyncio
import websockets
import json
import sys
import os
from datetime import datetime

async def send_to_roo_code(username, message):
    """Send a message to Roo Code"""
    
    server_url = 'ws://localhost:9998'
    
    try:
        websocket = await websockets.connect(server_url)
        
        # Register
        await websocket.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_roo_sender",
            'client_start_time': datetime.now().isoformat(),
            'capabilities': {'management': True, 'control': True},
            'system_info': {
                'platform': 'Windows',
                'hostname': os.environ.get('COMPUTERNAME', 'unknown')
            }
        }))
        
        welcome = await websocket.recv()
        
        # Get client
        await websocket.send(json.dumps({
            'type': 'request',
            'command': 'list_clients'
        }))
        
        response = await websocket.recv()
        data = json.loads(response)
        
        target_client_id = None
        if data['type'] == 'client_list':
            for client in data['clients']:
                if client.get('user_session') == username:
                    target_client_id = client['id']
                    break
        
        if not target_client_id:
            print(f"Client '{username}' not found")
            return
        
        print(f"Connected to {username} (ID: {target_client_id})")
        
        # Step 1: Activate VSCode window first
        print("\n[1] Activating VSCode window...")
        
        await websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': target_client_id,
            'command': {
                'type': 'command',
                'command': 'activate_window',
                'params': {}
            }
        }))
        
        ack = await websocket.recv()
        await asyncio.sleep(1)
        
        # Step 2: Clear any existing text in the input field
        print("\n[2] Clearing input field...")
        
        # Select all text first
        await websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': target_client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {
                    'keys': '^a'  # Ctrl+A to select all
                }
            }
        }))
        
        await websocket.recv()
        await asyncio.sleep(0.5)
        
        # Step 3: Type the message
        print(f"\n[3] Typing message: {message}")
        
        await websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': target_client_id,
            'command': {
                'type': 'command',
                'command': 'vscode_type_text',
                'params': {
                    'text': message
                }
            }
        }))
        
        await websocket.recv()
        result = await asyncio.wait_for(websocket.recv(), timeout=3.0)
        print(f"Type result: {json.loads(result).get('result', 'OK')}")
        await asyncio.sleep(1)
        
        # Step 4: Send the message (press Enter)
        print("\n[4] Sending message (Enter key)...")
        
        await websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': target_client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {
                    'keys': '{ENTER}'
                }
            }
        }))
        
        await websocket.recv()
        await asyncio.sleep(0.5)
        
        print("\n[SUCCESS] Message sent to Roo Code!")
        print("The AI assistant should now be processing your request.")
        
        # Optional: Get updated content to see if message was sent
        print("\n[5] Verifying (getting updated content)...")
        
        await websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': target_client_id,
            'command': {
                'type': 'command',
                'command': 'vscode_get_content',
                'params': {}
            }
        }))
        
        await websocket.recv()
        
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
            result = json.loads(response)
            if result.get('type') == 'command_result':
                # Save updated structure
                var_dir = os.path.join(os.path.dirname(__file__), 'var')
                os.makedirs(var_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'vscode_after_send_{timestamp}.json'
                filepath = os.path.join(var_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result.get('result', {}), f, indent=2, ensure_ascii=False)
                
                print(f"Updated structure saved to: {filepath}")
        except asyncio.TimeoutError:
            print("Timeout getting updated content")
        
        await websocket.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    username = "wjchk"
    message = "分析一下当前的产品设计"
    
    print("=== Roo Code Message Sender ===")
    print(f"Target user: {username}")
    print(f"Message: {message}")
    print("=" * 50)
    
    asyncio.run(send_to_roo_code(username, message))