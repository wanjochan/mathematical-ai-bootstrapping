"""Get and analyze VSCode window structure from a client"""

import asyncio
import websockets
import json
import sys
import os
from datetime import datetime

async def get_vscode_structure(username):
    """Get VSCode window content and extract structure"""
    
    server_url = 'ws://localhost:9998'
    
    try:
        websocket = await websockets.connect(server_url)
        
        # Register as controller
        await websocket.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_vscode_analyzer",
            'client_start_time': datetime.now().isoformat(),
            'capabilities': {'management': True, 'control': True},
            'system_info': {
                'platform': 'Windows',
                'hostname': os.environ.get('COMPUTERNAME', 'unknown')
            }
        }))
        
        # Wait for welcome
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
            await websocket.close()
            return
        
        print(f"Getting VSCode content from {username} (ID: {target_client_id})...")
        
        # Send vscode_get_content command
        await websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': target_client_id,
            'command': {
                'type': 'command',
                'command': 'vscode_get_content',
                'params': {}
            }
        }))
        
        # Wait for ack
        ack = await websocket.recv()
        
        # Wait for result
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                result = json.loads(response)
                
                if result.get('type') == 'command_result' and result.get('from_client') == target_client_id:
                    
                    if result.get('error'):
                        print(f"Error: {result['error']}")
                    else:
                        vscode_data = result.get('result', {})
                        
                        # Extract and display structure
                        print("\nVSCode Window Structure")
                        print("=" * 80)
                        
                        if isinstance(vscode_data, dict):
                            # Window information
                            if 'window_title' in vscode_data:
                                print(f"\nWindow Title: {vscode_data['window_title']}")
                            
                            # UI Structure
                            if 'ui_structure' in vscode_data:
                                print("\nUI Elements Found:")
                                analyze_ui_structure(vscode_data['ui_structure'])
                            
                            # Content
                            if 'content' in vscode_data:
                                print("\nContent Preview:")
                                content = vscode_data['content']
                                if isinstance(content, str):
                                    # Show first 500 chars
                                    preview = content[:500].replace('\n', '\\n')
                                    print(f"  {preview}...")
                                elif isinstance(content, list):
                                    print(f"  Content items: {len(content)}")
                                    for i, item in enumerate(content[:5]):
                                        print(f"    [{i}]: {str(item)[:100]}")
                            
                            # Raw structure
                            print("\nRaw Structure Keys:")
                            for key in vscode_data.keys():
                                value = vscode_data[key]
                                if isinstance(value, (str, int, float, bool)):
                                    print(f"  {key}: {value}")
                                elif isinstance(value, list):
                                    print(f"  {key}: [list with {len(value)} items]")
                                elif isinstance(value, dict):
                                    print(f"  {key}: {{dict with {len(value)} keys}}")
                                else:
                                    print(f"  {key}: {type(value).__name__}")
                        
                        else:
                            # If it's not a dict, show what we got
                            print(f"\nReceived data type: {type(vscode_data).__name__}")
                            if isinstance(vscode_data, str):
                                # Try to parse as JSON
                                try:
                                    parsed = json.loads(vscode_data)
                                    print("Parsed JSON structure:")
                                    print(json.dumps(parsed, indent=2, ensure_ascii=False)[:1000])
                                except:
                                    print("Raw content (first 1000 chars):")
                                    print(vscode_data[:1000])
                            else:
                                print(f"Data: {str(vscode_data)[:1000]}")
                    
                    break
                    
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                break
        
        await websocket.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def analyze_ui_structure(ui_data):
    """Analyze UI structure data"""
    if isinstance(ui_data, dict):
        for key, value in ui_data.items():
            if isinstance(value, list):
                print(f"  - {key}: {len(value)} items")
            elif isinstance(value, dict):
                print(f"  - {key}: {len(value)} properties")
            else:
                print(f"  - {key}: {value}")
    elif isinstance(ui_data, list):
        print(f"  Total UI elements: {len(ui_data)}")
        # Group by type if elements have 'type' field
        types = {}
        for elem in ui_data:
            if isinstance(elem, dict) and 'type' in elem:
                elem_type = elem['type']
                types[elem_type] = types.get(elem_type, 0) + 1
        
        if types:
            print("  Element types:")
            for elem_type, count in types.items():
                print(f"    - {elem_type}: {count}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_vscode_structure.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    asyncio.run(get_vscode_structure(username))