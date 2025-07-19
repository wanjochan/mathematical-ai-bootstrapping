"""Test script to list all connected clients"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def list_clients():
    """Connect to server and request client list"""
    port = int(os.environ.get('CYBERCORP_PORT', '9998'))
    server_url = f'ws://localhost:{port}'
    
    print(f"Connecting to server at {server_url}...")
    
    try:
        async with websockets.connect(server_url) as websocket:
            # Register as a management client
            await websocket.send(json.dumps({
                'type': 'register',
                'user_session': os.environ.get('USERNAME', 'unknown'),
                'client_start_time': datetime.now().isoformat(),
                'capabilities': {
                    'vscode_control': False,
                    'management': True
                },
                'system_info': {
                    'platform': 'Windows',
                    'hostname': os.environ.get('COMPUTERNAME', 'unknown'),
                    'python_version': '3.x'
                }
            }))
            
            # Wait for welcome
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"Connected as client: {welcome_data.get('client_id', 'unknown')}")
            
            # Request client list
            await websocket.send(json.dumps({
                'type': 'request',
                'command': 'list_clients'
            }))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            
            if data['type'] == 'client_list':
                print("\nConnected Clients:")
                print("=" * 80)
                for client in data['clients']:
                    print(f"Client ID: {client['id']}")
                    print(f"  User: {client.get('user_session', 'unknown')}")
                    print(f"  Hostname: {client.get('hostname', 'unknown')}")
                    print(f"  IP: {client.get('ip', 'unknown')}")
                    print(f"  Connected: {client.get('connected_at', 'unknown')}")
                    print(f"  Started: {client.get('client_start_time', 'unknown')}")
                    print(f"  Capabilities: {client.get('capabilities', {})}")
                    print()
                print(f"Total clients: {len(data['clients'])}")
            else:
                print(f"Unexpected response: {data}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("CyberCorp Client List")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    asyncio.run(list_clients())