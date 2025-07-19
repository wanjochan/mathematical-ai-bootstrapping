"""Interact with Roo Code in VSCode"""

import asyncio
import websockets
import json
import sys
import os
from datetime import datetime

async def interact_with_roo_code(username, question):
    """Get VSCode structure and interact with Roo Code"""
    
    server_url = 'ws://localhost:9998'
    
    try:
        websocket = await websockets.connect(server_url)
        
        # Register
        await websocket.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_roo_controller",
            'client_start_time': datetime.now().isoformat(),
            'capabilities': {'management': True, 'control': True},
            'system_info': {
                'platform': 'Windows',
                'hostname': os.environ.get('COMPUTERNAME', 'unknown')
            }
        }))
        
        welcome = await websocket.recv()
        
        # Get client list
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
        
        print(f"Found {username} client: {target_client_id}")
        
        # Step 1: Get VSCode window structure
        print("\n[Step 1] Getting VSCode window structure...")
        
        await websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': target_client_id,
            'command': {
                'type': 'command',
                'command': 'vscode_get_content',
                'params': {}
            }
        }))
        
        await websocket.recv()  # ack
        
        # Wait for VSCode structure
        vscode_structure = None
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                result = json.loads(response)
                
                if result.get('type') == 'command_result' and result.get('from_client') == target_client_id:
                    if result.get('error'):
                        print(f"Error getting VSCode content: {result['error']}")
                        return
                    else:
                        vscode_structure = result.get('result', {})
                        break
                        
            except asyncio.TimeoutError:
                print("Timeout getting VSCode structure")
                return
        
        # Save structure to var directory
        var_dir = os.path.join(os.path.dirname(__file__), 'var')
        os.makedirs(var_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        structure_file = os.path.join(var_dir, f'vscode_structure_{timestamp}.json')
        with open(structure_file, 'w', encoding='utf-8') as f:
            json.dump(vscode_structure, f, indent=2, ensure_ascii=False)
        print(f"Structure saved to: {structure_file}")
        
        # Analyze structure to find Roo Code elements
        print("\n[Step 2] Analyzing structure to find Roo Code...")
        
        roo_elements = []
        input_elements = []
        button_elements = []
        
        content_areas = vscode_structure.get('content_areas', [])
        for area in content_areas:
            if isinstance(area, dict):
                name = str(area.get('name', '')).lower()
                control_type = str(area.get('control_type', '')).lower()
                
                # Find Roo Code elements
                if 'roo' in name or 'code' in name:
                    roo_elements.append(area)
                
                # Find input/text areas
                if 'edit' in control_type or 'text' in control_type or 'input' in name:
                    input_elements.append(area)
                
                # Find buttons
                if 'button' in control_type or 'send' in name or 'submit' in name:
                    button_elements.append(area)
        
        print(f"Found {len(roo_elements)} Roo Code elements")
        print(f"Found {len(input_elements)} input elements")
        print(f"Found {len(button_elements)} button elements")
        
        # Find the send message input and button
        send_input = None
        send_button = None
        
        for elem in input_elements:
            name = str(elem.get('name', ''))
            if 'send' in name.lower() or 'message' in name.lower():
                send_input = elem
                break
        
        for elem in button_elements:
            name = str(elem.get('name', ''))
            if 'send' in name.lower():
                send_button = elem
                break
        
        if not send_input:
            print("Could not find message input area")
            # Try to use any text input in Roo Code area
            for elem in input_elements:
                if any(roo.get('name') in str(elem) for roo in roo_elements):
                    send_input = elem
                    break
        
        # Step 3: Activate VSCode window
        print("\n[Step 3] Activating VSCode window...")
        
        await websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': target_client_id,
            'command': {
                'type': 'command',
                'command': 'activate_window',
                'params': {}
            }
        }))
        
        await websocket.recv()  # ack
        await asyncio.sleep(1)  # Wait for activation
        
        # Step 4: Input the question
        print(f"\n[Step 4] Typing question: {question}")
        
        await websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': target_client_id,
            'command': {
                'type': 'command',
                'command': 'vscode_type_text',
                'params': {
                    'text': question
                }
            }
        }))
        
        await websocket.recv()  # ack
        await asyncio.sleep(1)  # Wait for typing
        
        # Step 5: Send the message
        print("\n[Step 5] Sending message...")
        
        # Try multiple methods to send
        # Method 1: Send Enter key
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
        
        await websocket.recv()  # ack
        
        print("\n✓ Task completed!")
        print("- VSCode structure obtained")
        print("- Question typed in Roo Code")
        print("- Send command executed")
        
        await websocket.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    username = "wjchk"
    question = "分析一下当前的产品设计"
    
    print(f"Interacting with Roo Code for user: {username}")
    print(f"Question: {question}")
    print("=" * 80)
    
    asyncio.run(interact_with_roo_code(username, question))