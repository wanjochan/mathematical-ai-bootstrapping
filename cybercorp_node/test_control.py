"""Test controlling a specific client by username"""

import asyncio
import websockets
import json
import os
import sys
from datetime import datetime

async def control_client(target_username):
    """Connect to server and control a client by username"""
    port = 9998
    server_url = f'ws://localhost:{port}'
    
    print(f"Connecting to CyberCorp Control Server at port {port}...")
    print("=" * 80)
    
    try:
        async with websockets.connect(server_url) as websocket:
            # Register as a control client
            await websocket.send(json.dumps({
                'type': 'register',
                'user_session': f"{os.environ.get('USERNAME', 'unknown')}_controller",
                'client_start_time': datetime.now().isoformat(),
                'capabilities': {
                    'management': True,
                    'control': True
                },
                'system_info': {
                    'platform': 'Windows',
                    'hostname': os.environ.get('COMPUTERNAME', 'unknown')
                }
            }))
            
            # Wait for welcome
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            my_id = welcome_data.get('client_id')
            print(f"Connected as controller: {my_id}")
            
            # Request client list first
            await websocket.send(json.dumps({
                'type': 'request',
                'command': 'list_clients'
            }))
            
            # Wait for client list
            response = await websocket.recv()
            data = json.loads(response)
            
            if data['type'] == 'client_list':
                print("\nConnected Clients:")
                print("-" * 80)
                
                target_client_id = None
                for client in data['clients']:
                    is_target = client.get('user_session') == target_username
                    marker = " [TARGET]" if is_target else ""
                    print(f"  {client['id']}: {client.get('user_session', 'unknown')} @ {client.get('hostname', 'unknown')}{marker}")
                    
                    if is_target and client.get('capabilities', {}).get('vscode_control'):
                        target_client_id = client['id']
                
                if target_client_id:
                    print(f"\nFound target client: {target_username} (ID: {target_client_id})")
                    print("Sending process info request...")
                    
                    # Send command to get process info
                    command_message = {
                        'type': 'forward_command',
                        'target_client': target_client_id,
                        'command': {
                            'type': 'command',
                            'command': 'get_processes',
                            'params': {
                                'filter': 'current_session'
                            }
                        }
                    }
                    
                    await websocket.send(json.dumps(command_message))
                    
                    # Wait for acknowledgment
                    ack = await websocket.recv()
                    ack_data = json.loads(ack)
                    if ack_data.get('type') == 'forward_ack':
                        print(f"Command forwarded successfully")
                    
                    # Wait for the result from target client
                    print("Waiting for response from target client...")
                    
                    # Keep listening for responses
                    while True:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            result = json.loads(response)
                            
                            # Check if this is the response we're waiting for
                            if result.get('type') == 'command_result' and result.get('from_client') == target_client_id:
                                print(f"\nReceived process info from {target_username}:")
                                print("-" * 80)
                                
                                # The result is directly an array of processes
                                processes = result.get('result', [])
                                if isinstance(processes, list):
                                    print(f"Total processes: {len(processes)}")
                                else:
                                    print("Unexpected result format")
                                    processes = []
                                
                                # Show top 10 processes
                                print("\nTop 10 processes by memory:")
                                for i, proc in enumerate(processes[:10], 1):
                                    print(f"{i}. {proc.get('name', 'unknown')} (PID: {proc.get('pid')}) - Memory: {proc.get('memory_mb', 0):.1f} MB")
                                
                                break
                            else:
                                # Some other message, ignore
                                pass
                                
                        except asyncio.TimeoutError:
                            print("\nTimeout waiting for response from target client.")
                            print("The client might not be responding or the server needs update.")
                            break
                else:
                    print(f"\nNo controllable client found for user: {target_username}")
                    print("Make sure the client is connected and has vscode_control capability.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_control.py <username>")
        print("Example: python test_control.py wjchk")
        sys.exit(1)
    
    target_username = sys.argv[1]
    
    print(f"CyberCorp Control Test - Control {target_username}")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Controller: {os.environ.get('USERNAME')}@{os.environ.get('COMPUTERNAME')}")
    print(f"Target: {target_username}")
    print()
    
    asyncio.run(control_client(target_username))

if __name__ == "__main__":
    main()