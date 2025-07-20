"""Test the new UIA structure command"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def test_uia_structure():
    """Test getting Cursor UIA structure"""
    server_url = 'ws://localhost:9998'
    
    async with websockets.connect(server_url) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_uia_test",
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
        
        # Use the new command to get Cursor UIA structure
        cursor_hwnd = 5898916  # Cursor window hwnd
        
        print(f"\nGetting UIA structure for Cursor (hwnd: {cursor_hwnd})...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'get_window_uia_structure',
                'params': {'hwnd': cursor_hwnd}
            }
        }))
        
        await ws.recv()  # ack
        
        # Wait for result with longer timeout
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=30.0)
            uia_data = json.loads(result)
            
            if uia_data.get('type') == 'command_result':
                structure = uia_data.get('result', {})
                
                if 'error' in structure:
                    print(f"Error: {structure['error']}")
                else:
                    # Save full structure
                    filename = f"cursor_uia_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(structure, f, indent=2, ensure_ascii=False)
                        
                    print(f"\nSaved UIA structure to: {filename}")
                    
                    # Analyze structure
                    print(f"\nRoot element: {structure.get('Name', 'No name')}")
                    print(f"Control type: {structure.get('ControlType')}")
                    print(f"Children count: {len(structure.get('Children', {}))}")
                    
                    # Find chat-related elements
                    def find_elements(node, keywords, path="", results=None):
                        if results is None:
                            results = []
                            
                        if isinstance(node, dict):
                            name = node.get('Name', '').lower()
                            control_type = node.get('ControlType', '')
                            automation_id = node.get('AutomationId', '').lower()
                            
                            for keyword in keywords:
                                if keyword in name or keyword in automation_id:
                                    results.append({
                                        'path': path,
                                        'name': node.get('Name'),
                                        'type': control_type,
                                        'automationId': node.get('AutomationId'),
                                        'enabled': node.get('IsEnabled'),
                                        'value': node.get('Value', '')
                                    })
                                    break
                            
                            # Check children
                            children = node.get('Children', {})
                            for child_key, child_node in children.items():
                                child_path = f"{path}/{child_key}" if path else child_key
                                find_elements(child_node, keywords, child_path, results)
                                
                        return results
                    
                    # Look for chat/input elements
                    chat_keywords = ['chat', 'message', 'type', 'input', 'composer', 'send', 'prompt', 'ask']
                    chat_elements = find_elements(structure, chat_keywords)
                    
                    print(f"\nFound {len(chat_elements)} chat-related elements:")
                    for elem in chat_elements[:10]:  # Show first 10
                        print(f"\n  Path: {elem['path']}")
                        print(f"  Name: {elem['name']}")
                        print(f"  Type: {elem['type']}")
                        print(f"  Enabled: {elem['enabled']}")
                        if elem['value']:
                            print(f"  Value: {elem['value'][:50]}...")
                    
                    # Find all editable elements
                    def find_editable(node, path="", results=None):
                        if results is None:
                            results = []
                            
                        if isinstance(node, dict):
                            control_type = node.get('ControlType', '')
                            if control_type == 'Edit' and node.get('IsEnabled'):
                                results.append({
                                    'path': path,
                                    'name': node.get('Name', ''),
                                    'automationId': node.get('AutomationId', ''),
                                    'value': node.get('Value', ''),
                                    'focusable': node.get('IsKeyboardFocusable', False)
                                })
                            
                            # Check children
                            children = node.get('Children', {})
                            for child_key, child_node in children.items():
                                child_path = f"{path}/{child_key}" if path else child_key
                                find_editable(child_node, child_path, results)
                                
                        return results
                    
                    editable_elements = find_editable(structure)
                    
                    print(f"\n\nFound {len(editable_elements)} editable elements:")
                    for elem in editable_elements[:10]:  # Show first 10
                        print(f"\n  Path: {elem['path']}")
                        print(f"  Name: {elem['name']}")
                        print(f"  AutomationId: {elem['automationId']}")
                        print(f"  Focusable: {elem['focusable']}")
                        if elem['value']:
                            print(f"  Current value: {elem['value'][:50]}...")
                            
        except asyncio.TimeoutError:
            print("Timeout getting UIA structure")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_uia_structure())