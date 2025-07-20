"""Get Cursor UI structure using UIA"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def get_cursor_ui():
    """Get Cursor UI structure"""
    server_url = 'ws://localhost:9998'
    
    async with websockets.connect(server_url) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_ui_getter",
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
        
        # Get Cursor UI structure
        print("\nGetting Cursor UI structure...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'get_window_ui_structure',
                'params': {'hwnd': cursor_hwnd}
            }
        }))
        
        await ws.recv()  # ack
        
        # Wait for result
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=10.0)
            ui_data = json.loads(result)
            
            if ui_data.get('type') == 'command_result':
                structure = ui_data.get('result', {})
                
                # Save full structure
                filename = f"cursor_full_ui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(structure, f, indent=2, ensure_ascii=False)
                    
                print(f"\nSaved full UI structure to: {filename}")
                
                # Analyze for chat elements
                print("\nAnalyzing UI structure for chat elements...")
                
                def find_elements(data, keywords, path=""):
                    """Recursively find elements containing keywords"""
                    found = []
                    
                    if isinstance(data, dict):
                        # Check current element
                        name = data.get('Name', '').lower()
                        control_type = data.get('ControlType', '')
                        automation_id = data.get('AutomationId', '')
                        
                        for keyword in keywords:
                            if keyword in name or keyword in automation_id.lower():
                                found.append({
                                    'path': path,
                                    'name': data.get('Name'),
                                    'type': control_type,
                                    'automationId': automation_id,
                                    'className': data.get('ClassName', ''),
                                    'isEnabled': data.get('IsEnabled', False)
                                })
                                break
                        
                        # Check children
                        children = data.get('Children', {})
                        if isinstance(children, dict):
                            for key, child in children.items():
                                child_path = f"{path}/{key}" if path else key
                                found.extend(find_elements(child, keywords, child_path))
                                
                    return found
                
                # Look for chat-related elements
                chat_keywords = ['chat', 'message', 'type', 'input', 'composer', 'send', 'prompt', 'ask']
                chat_elements = find_elements(structure, chat_keywords)
                
                print(f"\nFound {len(chat_elements)} chat-related elements:")
                for elem in chat_elements:
                    print(f"\n  Path: {elem['path']}")
                    print(f"  Name: {elem['name']}")
                    print(f"  Type: {elem['type']}")
                    print(f"  AutomationId: {elem['automationId']}")
                    print(f"  Enabled: {elem['isEnabled']}")
                    
                # Also look for editable elements
                print("\n\nLooking for editable elements...")
                
                def find_editable(data, path=""):
                    """Find editable elements"""
                    editable = []
                    
                    if isinstance(data, dict):
                        control_type = data.get('ControlType', '')
                        is_enabled = data.get('IsEnabled', False)
                        
                        if control_type in ['Edit', 'ComboBox'] and is_enabled:
                            editable.append({
                                'path': path,
                                'name': data.get('Name', ''),
                                'type': control_type,
                                'automationId': data.get('AutomationId', ''),
                                'value': data.get('Value', ''),
                                'isKeyboardFocusable': data.get('IsKeyboardFocusable', False)
                            })
                        
                        # Check children
                        children = data.get('Children', {})
                        if isinstance(children, dict):
                            for key, child in children.items():
                                child_path = f"{path}/{key}" if path else key
                                editable.extend(find_editable(child, child_path))
                                
                    return editable
                
                editable_elements = find_editable(structure)
                
                print(f"\nFound {len(editable_elements)} editable elements:")
                for elem in editable_elements:
                    print(f"\n  Path: {elem['path']}")
                    print(f"  Name: {elem['name']}")
                    print(f"  Type: {elem['type']}")
                    print(f"  AutomationId: {elem['automationId']}")
                    print(f"  Value: {elem['value']}")
                    print(f"  KeyboardFocusable: {elem['isKeyboardFocusable']}")
                    
        except asyncio.TimeoutError:
            print("Timeout getting UI structure")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(get_cursor_ui())