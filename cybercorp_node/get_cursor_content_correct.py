"""Get Cursor content using correct command"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def get_cursor_content():
    """Get Cursor content structure"""
    server_url = 'ws://localhost:9998'
    
    async with websockets.connect(server_url) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_content_getter",
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
        
        # First activate Cursor window
        cursor_hwnd = 5898916
        print("\nActivating Cursor window...")
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
        await asyncio.sleep(2)  # Give it time to activate
        
        # Get Cursor content
        print("\nGetting Cursor content...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'vscode_get_content'
            }
        }))
        
        await ws.recv()  # ack
        
        # Wait for result with longer timeout
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=15.0)
            content_data = json.loads(result)
            
            if content_data.get('type') == 'command_result':
                content = content_data.get('result', {})
                
                # Save full content
                filename = f"cursor_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
                    
                print(f"\nSaved content to: {filename}")
                
                # Analyze content
                if isinstance(content, dict):
                    print(f"\nTotal elements: {len(content)}")
                    
                    # Look for chat/input elements
                    chat_elements = []
                    editable_elements = []
                    
                    for key, value in content.items():
                        if isinstance(value, dict):
                            name = value.get('Name', '')
                            control_type = value.get('ControlType', '')
                            automation_id = value.get('AutomationId', '')
                            
                            # Chat related
                            if any(word in name.lower() for word in ['chat', 'message', 'type', 'composer', 'input', 'send']):
                                chat_elements.append({
                                    'key': key,
                                    'name': name,
                                    'type': control_type,
                                    'automationId': automation_id
                                })
                            
                            # Editable
                            if control_type in ['Edit', 'ComboBox'] and value.get('IsEnabled', False):
                                editable_elements.append({
                                    'key': key,
                                    'name': name,
                                    'type': control_type,
                                    'automationId': automation_id,
                                    'value': value.get('Value', '')
                                })
                    
                    print(f"\nFound {len(chat_elements)} chat-related elements:")
                    for elem in chat_elements[:5]:  # Show first 5
                        print(f"  - {elem['name']} (Key: {elem['key']}, Type: {elem['type']})")
                    
                    print(f"\nFound {len(editable_elements)} editable elements:")
                    for elem in editable_elements[:5]:  # Show first 5
                        print(f"  - {elem['name']} (Key: {elem['key']}, Type: {elem['type']})")
                        if elem['value']:
                            print(f"    Current value: {elem['value'][:50]}...")
                            
                    # Try to find the main chat input
                    print("\n\nLooking for main chat input area...")
                    
                    # Common patterns for chat inputs
                    input_patterns = [
                        'type your message',
                        'type a message',
                        'ask cursor',
                        'chat input',
                        'message composer',
                        'send message'
                    ]
                    
                    for key, value in content.items():
                        if isinstance(value, dict):
                            name = value.get('Name', '').lower()
                            if any(pattern in name for pattern in input_patterns):
                                print(f"\nFound potential chat input:")
                                print(f"  Key: {key}")
                                print(f"  Name: {value.get('Name')}")
                                print(f"  Type: {value.get('ControlType')}")
                                print(f"  AutomationId: {value.get('AutomationId')}")
                                print(f"  Enabled: {value.get('IsEnabled')}")
                                
        except asyncio.TimeoutError:
            print("Timeout getting content")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(get_cursor_content())