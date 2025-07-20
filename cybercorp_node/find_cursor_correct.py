"""Find the correct Cursor window"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def find_cursor():
    """Find Cursor window correctly"""
    server_url = 'ws://localhost:9998'
    
    async with websockets.connect(server_url) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_finder",
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
        
        # Get all windows
        print("\nGetting all windows...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'get_windows'
            }
        }))
        
        # Wait for ack
        ack = await ws.recv()
        
        # Wait for result
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=5.0)
            windows_data = json.loads(result)
            
            if windows_data.get('type') == 'command_result':
                windows = windows_data.get('result', [])
                
                print(f"\nTotal windows: {len(windows)}")
                print("\nAll windows:")
                
                cursor_windows = []
                vscode_windows = []
                
                for w in windows:
                    title = w.get('title', '')
                    title_lower = title.lower()
                    
                    # Print all windows
                    print(f"  - {title} (hwnd: {w.get('hwnd')}, class: {w.get('class')})")
                    
                    # Categorize
                    if 'cursor' in title_lower:
                        cursor_windows.append(w)
                    elif 'visual studio code' in title_lower or 'vscode' in title_lower:
                        vscode_windows.append(w)
                        
                print(f"\nFound {len(cursor_windows)} Cursor windows")
                print(f"Found {len(vscode_windows)} VSCode windows")
                
                # If we found Cursor, use it
                if cursor_windows:
                    cursor = cursor_windows[0]
                    print(f"\nSelected Cursor window: {cursor['title']}")
                    
                    # Try to click on the Chat tab or Toggle Chat button
                    print("\nLooking for Chat interface...")
                    await ws.send(json.dumps({
                        'type': 'forward_command',
                        'target_client': client_id,
                        'command': {
                            'type': 'command',
                            'command': 'vscode_get_content',
                            'params': {'hwnd': cursor['hwnd']}
                        }
                    }))
                    
                    ack2 = await ws.recv()
                    content_result = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    content_data = json.loads(content_result)
                    
                    if content_data.get('type') == 'command_result':
                        content = content_data.get('result', {})
                        
                        # Look for Chat-related elements
                        chat_elements = []
                        for key, value in content.items():
                            if isinstance(value, dict):
                                name = value.get('Name', '')
                                if any(word in name.lower() for word in ['chat', 'toggle chat', 'composer', 'message', 'type']):
                                    chat_elements.append({
                                        'name': name,
                                        'type': value.get('ControlType'),
                                        'automationId': value.get('AutomationId')
                                    })
                                    
                        print(f"\nFound {len(chat_elements)} chat-related elements:")
                        for elem in chat_elements:
                            print(f"  - {elem['name']} (Type: {elem['type']})")
                            
        except asyncio.TimeoutError:
            print("Timeout getting windows")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(find_cursor())