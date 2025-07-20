"""Analyze Cursor IDE structure"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def analyze_cursor():
    """Analyze Cursor window structure"""
    server_url = 'ws://localhost:9998'
    
    async with websockets.connect(server_url) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_analyzer",
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
        
        # Get VSCode/Cursor content structure
        print("\nGetting Cursor content structure...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'vscode_get_content'
            }
        }))
        
        # Wait for ack
        ack = await ws.recv()
        print(f"Command sent: {json.loads(ack).get('status')}")
        
        # Wait for result
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=10.0)
            content_data = json.loads(result)
            
            if content_data.get('type') == 'command_result':
                content = content_data.get('result', {})
                
                # Save the structure
                filename = f"cursor_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
                    
                print(f"\nSaved structure to: {filename}")
                
                # Analyze the structure
                if isinstance(content, dict):
                    print("\nCursor UI Structure Analysis:")
                    print(f"- Total elements: {len(content)}")
                    
                    # Look for input areas
                    input_elements = []
                    for key, value in content.items():
                        if isinstance(value, dict):
                            name = value.get('Name', '').lower()
                            control_type = value.get('ControlType', '')
                            
                            if any(keyword in name for keyword in ['input', 'edit', 'type', 'message', 'chat', 'prompt']):
                                input_elements.append({
                                    'key': key,
                                    'name': value.get('Name'),
                                    'type': control_type,
                                    'automationId': value.get('AutomationId')
                                })
                                
                    print(f"\nFound {len(input_elements)} potential input areas:")
                    for elem in input_elements:
                        print(f"  - {elem['name']} (Type: {elem['type']})")
                        
        except asyncio.TimeoutError:
            print("Timeout getting content")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_cursor())