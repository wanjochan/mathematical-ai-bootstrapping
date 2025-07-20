"""Test UIA structure locally"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def test_uia_local():
    """Test UIA structure with local client"""
    server_url = 'ws://localhost:9998'
    
    async with websockets.connect(server_url) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_test_uia",
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
        
        print(f"\nClients found: {len(data.get('clients', []))}")
        for client in data.get('clients', []):
            print(f"  - {client.get('user_session')} (ID: {client['id']})")
        
        # Find our test client
        test_client_id = None
        for client in data.get('clients', []):
            if client.get('user_session') == 'wjc2022':
                test_client_id = client['id']
                break
                
        if not test_client_id:
            print("Test client not found")
            return
            
        print(f"\nUsing test client: {test_client_id}")
        
        # First get list of windows
        print("\nGetting windows list...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': test_client_id,
            'command': {
                'type': 'command',
                'command': 'get_windows'
            }
        }))
        
        await ws.recv()  # ack
        
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=5.0)
            windows_data = json.loads(result)
            
            if windows_data.get('type') == 'command_result':
                windows = windows_data.get('result', [])
                print(f"\nFound {len(windows)} windows")
                
                # Find a test window (e.g., Notepad or any simple app)
                test_window = None
                for w in windows[:10]:  # Show first 10
                    try:
                        print(f"  - {w['title']} (hwnd: {w['hwnd']})")
                    except UnicodeEncodeError:
                        # Handle special characters
                        safe_title = w['title'].encode('ascii', 'replace').decode('ascii')
                        print(f"  - {safe_title} (hwnd: {w['hwnd']})")
                    if 'notepad' in w['title'].lower() or 'text' in w['title'].lower():
                        test_window = w
                        
                if not test_window and windows:
                    # Use first window if no notepad found
                    test_window = windows[0]
                    
                if test_window:
                    print(f"\nTesting UIA structure on: {test_window['title']}")
                    hwnd = test_window['hwnd']
                    
                    # Test the new UIA structure command
                    await ws.send(json.dumps({
                        'type': 'forward_command',
                        'target_client': test_client_id,
                        'command': {
                            'type': 'command',
                            'command': 'get_window_uia_structure',
                            'params': {'hwnd': hwnd}
                        }
                    }))
                    
                    await ws.recv()  # ack
                    
                    uia_result = await asyncio.wait_for(ws.recv(), timeout=30.0)
                    uia_data = json.loads(uia_result)
                    
                    if uia_data.get('type') == 'command_result':
                        structure = uia_data.get('result', {})
                        
                        if 'error' not in structure:
                            # Save structure
                            filename = f"test_uia_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(structure, f, indent=2, ensure_ascii=False)
                                
                            print(f"\nSaved UIA structure to: {filename}")
                            print(f"Root element: {structure.get('Name', 'No name')}")
                            print(f"Control type: {structure.get('ControlType')}")
                            print(f"Children count: {len(structure.get('Children', {}))}")
                        else:
                            print(f"\nError getting UIA structure: {structure.get('error')}")
                            
        except asyncio.TimeoutError:
            print("Timeout getting response")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_uia_local())