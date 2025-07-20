"""Test UIA structure with safe encoding"""

import asyncio
import websockets
import json
import os
import sys
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def safe_print(text):
    """Safe print that handles encoding issues"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback to ASCII with replacement
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text)

async def test_uia_safe():
    """Test UIA structure with safe encoding"""
    server_url = 'ws://localhost:9998'
    
    async with websockets.connect(server_url) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_uia_safe",
            'client_start_time': datetime.now().isoformat(),
            'capabilities': {'management': True}
        }))
        
        welcome = await ws.recv()
        safe_print(f"Connected: {json.loads(welcome)['client_id']}")
        
        # Get client list
        await ws.send(json.dumps({
            'type': 'request',
            'command': 'list_clients'
        }))
        
        response = await ws.recv()
        data = json.loads(response)
        
        safe_print(f"\nClients found: {len(data.get('clients', []))}")
        
        # Find our test client (use the newest one)
        test_client_id = None
        for client in data.get('clients', []):
            if client.get('user_session') == 'wjc2022' and client['id'] == 'client_54':
                test_client_id = client['id']
                break
                
        if not test_client_id:
            safe_print("Test client not found")
            return
            
        safe_print(f"\nUsing test client: {test_client_id}")
        
        # Get windows
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
                safe_print(f"\nFound {len(windows)} windows")
                
                # Find CMD window or first available
                test_window = None
                for w in windows:
                    if 'cmd' in w['title'].lower() or test_window is None:
                        test_window = w
                        if 'cmd' in w['title'].lower():
                            break
                            
                if test_window:
                    safe_print(f"\nTesting UIA on window hwnd: {test_window['hwnd']}")
                    
                    # Test UIA structure
                    await ws.send(json.dumps({
                        'type': 'forward_command',
                        'target_client': test_client_id,
                        'command': {
                            'type': 'command',
                            'command': 'get_window_uia_structure',
                            'params': {'hwnd': test_window['hwnd']}
                        }
                    }))
                    
                    await ws.recv()  # ack
                    
                    uia_result = await asyncio.wait_for(ws.recv(), timeout=30.0)
                    uia_data = json.loads(uia_result)
                    
                    if uia_data.get('type') == 'command_result':
                        safe_print(f"Command result received")
                        safe_print(f"Has error: {uia_data.get('error')}")
                        
                        structure = uia_data.get('result')
                        safe_print(f"Structure type: {type(structure)}")
                        
                        if structure and isinstance(structure, dict) and 'error' not in structure:
                            # Save structure
                            filename = f"uia_structure_{test_window['hwnd']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(structure, f, indent=2, ensure_ascii=False)
                                
                            safe_print(f"\nSuccess! Saved UIA structure to: {filename}")
                            safe_print(f"Control type: {structure.get('ControlType', 'Unknown')}")
                            safe_print(f"Children count: {len(structure.get('Children', {}))}")
                            
                            # Show some child elements
                            children = structure.get('Children', {})
                            if children:
                                safe_print("\nFirst few children:")
                                for i, (key, child) in enumerate(list(children.items())[:5]):
                                    safe_print(f"  - {key}: {child.get('ControlType')} - {child.get('Name', '')[:50]}")
                        else:
                            if structure and isinstance(structure, dict):
                                safe_print(f"\nError in structure: {structure.get('error', 'Unknown error')}")
                            else:
                                safe_print(f"\nNo valid structure returned")
                            
        except asyncio.TimeoutError:
            safe_print("Timeout getting response")
        except Exception as e:
            safe_print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_uia_safe())