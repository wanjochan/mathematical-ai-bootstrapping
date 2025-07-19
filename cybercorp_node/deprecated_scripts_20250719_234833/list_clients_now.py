"""List all connected clients by connecting to the server's management interface"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def list_clients():
    """Connect and immediately check for other clients"""
    port = 9998
    server_url = f'ws://localhost:{port}'
    
    print(f"Connecting to CyberCorp Server at port {port}...")
    print("=" * 60)
    
    try:
        async with websockets.connect(server_url) as websocket:
            # Register as a management client
            await websocket.send(json.dumps({
                'type': 'register',
                'user_session': f"{os.environ.get('USERNAME', 'unknown')}_management",
                'client_start_time': datetime.now().isoformat(),
                'capabilities': {
                    'management': True
                },
                'system_info': {
                    'platform': 'Windows',
                    'hostname': os.environ.get('COMPUTERNAME', 'unknown')
                }
            }))
            
            # Wait for welcome
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            
            # The server's console interface shows it tracks clients
            # Let's see what we get in the welcome message
            print(f"Connected as: {welcome_data.get('client_id')}")
            print(f"Server time: {welcome_data.get('server_time')}")
            print()
            
            # Try to request client list (even if server doesn't support it yet)
            await websocket.send(json.dumps({
                'type': 'request',
                'command': 'list_clients'
            }))
            
            # Wait for any response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(response)
                print(f"Server response: {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                print("No response for list_clients command (server may not support it yet)")
            
            # Let's also try sending a status request
            await websocket.send(json.dumps({
                'type': 'status',
                'status': 'checking_clients'
            }))
            
            # Stay connected briefly to see if server sends any info
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: The server may need to be restarted with updated code to support list_clients")

if __name__ == "__main__":
    print("CyberCorp Client List Request")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"User: {os.environ.get('USERNAME')}")
    print()
    
    asyncio.run(list_clients())