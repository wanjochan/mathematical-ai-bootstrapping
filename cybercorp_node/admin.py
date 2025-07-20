"""Admin tool for CyberCorp Node management"""

# This file will be renamed to admin.py and include all admin functions

import asyncio
import websockets
import json
import argparse
from datetime import datetime

async def list_clients():
    """List all connected clients with details"""
    ws = await websockets.connect('ws://localhost:9998')
    
    await ws.send(json.dumps({
        'type': 'register',
        'user_session': 'admin',
        'client_start_time': datetime.now().isoformat(),
        'capabilities': {'management': True}
    }))
    
    await ws.recv()  # welcome
    
    # Get client list
    await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
    response = await ws.recv()
    data = json.loads(response)
    
    print(f"\n{'='*80}")
    print(f"Connected Clients: {len(data.get('clients', []))}")
    print(f"{'='*80}")
    
    for client in data.get('clients', []):
        print(f"\nID: {client['id']}")
        print(f"  User: {client['user_session']}")
        print(f"  Connected: {client.get('connected_at', 'Unknown')}")
        print(f"  Last heartbeat: {client.get('last_heartbeat', 'Unknown')}")
        print(f"  Capabilities: {client.get('capabilities', {})}")
    
    await ws.close()

async def test_client(client_id):
    """Test if a specific client is responsive"""
    ws = await websockets.connect('ws://localhost:9998')
    
    await ws.send(json.dumps({
        'type': 'register',
        'user_session': 'admin',
        'client_start_time': datetime.now().isoformat(),
        'capabilities': {'management': True}
    }))
    
    await ws.recv()  # welcome
    
    print(f"\nTesting client {client_id}...")
    
    # Send simple command
    await ws.send(json.dumps({
        'type': 'forward_command',
        'target_client': client_id,
        'command': {
            'type': 'command',
            'command': 'get_windows'
        }
    }))
    
    # Check ack
    ack = await ws.recv()
    print(f"Ack: {ack}")
    
    # Check result with timeout
    try:
        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data = json.loads(result)
        if data.get('type') == 'command_result':
            print(f"Client responsive! Got {len(data.get('result', []))} windows")
        else:
            print(f"Unexpected response: {data}")
    except asyncio.TimeoutError:
        print(f"Client {client_id} NOT RESPONSIVE (timeout)")
    
    await ws.close()

async def cleanup_stale_clients():
    """Request server to cleanup stale clients"""
    ws = await websockets.connect('ws://localhost:9998')
    
    await ws.send(json.dumps({
        'type': 'register',
        'user_session': 'admin',
        'client_start_time': datetime.now().isoformat(),
        'capabilities': {'management': True}
    }))
    
    await ws.recv()  # welcome
    
    # First get client list
    await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
    response = await ws.recv()
    data = json.loads(response)
    
    stale_clients = []
    
    # Test each client
    for client in data.get('clients', []):
        client_id = client['id']
        if client_id.startswith('client_') and client['user_session'] != 'admin':
            print(f"\nTesting {client_id} ({client['user_session']})...")
            
            # Send test command
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'get_windows'
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"  [OK] Responsive")
            except asyncio.TimeoutError:
                print(f"  [FAIL] NOT RESPONSIVE")
                stale_clients.append(client_id)
    
    print(f"\n{'='*80}")
    print(f"Found {len(stale_clients)} stale clients: {stale_clients}")
    print("Note: Server should automatically clean these up on next heartbeat check")
    
    await ws.close()

def check_clients_main():
    """Check clients functionality"""
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == 'simple':
        # Simple list for other scripts
        asyncio.run(list_clients_simple())
    else:
        asyncio.run(list_clients())

async def list_clients_simple():
    """Simple client list for scripts"""
    ws = await websockets.connect('ws://localhost:9998')
    await ws.send(json.dumps({'type': 'register', 'user_session': 'checker', 'client_start_time': '2024', 'capabilities': {}}))
    await ws.recv()
    await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
    response = await ws.recv()
    data = json.loads(response)
    print(f"Total clients: {len(data.get('clients', []))}")
    for client in data.get('clients', []):
        print(f"- {client.get('user_session')} (ID: {client['id']})")
    await ws.close()

def main():
    parser = argparse.ArgumentParser(description='CyberCorp Node Admin Tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List clients
    subparsers.add_parser('list', help='List all connected clients')
    
    # Test client
    test_parser = subparsers.add_parser('test', help='Test if client is responsive')
    test_parser.add_argument('client_id', help='Client ID to test')
    
    # Cleanup
    subparsers.add_parser('cleanup', help='Find and report stale clients')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        asyncio.run(list_clients())
    elif args.command == 'test':
        asyncio.run(test_client(args.client_id))
    elif args.command == 'cleanup':
        asyncio.run(cleanup_stale_clients())
    else:
        parser.print_help()

if __name__ == "__main__":
    main()