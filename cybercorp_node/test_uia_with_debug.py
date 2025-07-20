"""Test UIA with debug info"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def test_uia_debug():
    """Test UIA with debug"""
    server_url = 'ws://localhost:9998'
    
    async with websockets.connect(server_url) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_debug",
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
        
        # First check if client is still connected
        cursor_hwnd = 5898916
        
        print(f"\nSending get_window_uia_structure command...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'get_window_uia_structure',
                'params': {'hwnd': cursor_hwnd}
            }
        }))
        
        # Get acknowledgment
        ack = await ws.recv()
        print(f"Ack received: {ack}")
        
        # Wait for result
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=30.0)
            print(f"\nRaw result: {result[:200]}...")  # Show first 200 chars
            
            uia_data = json.loads(result)
            print(f"\nResult type: {uia_data.get('type')}")
            
            if uia_data.get('type') == 'command_result':
                print(f"Has error: {'error' in uia_data}")
                print(f"Has result: {'result' in uia_data}")
                
                if 'error' in uia_data and uia_data['error']:
                    print(f"Error: {uia_data['error']}")
                    
                structure = uia_data.get('result')
                print(f"Structure type: {type(structure)}")
                
                if structure:
                    print(f"Structure keys: {list(structure.keys())[:10] if isinstance(structure, dict) else 'Not a dict'}")
                else:
                    print("Structure is None or empty")
                    
        except asyncio.TimeoutError:
            print("Timeout waiting for result")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_uia_debug())