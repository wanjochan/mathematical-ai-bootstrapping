"""
Check current clients
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CheckClients')

async def check_clients(host='localhost', port=9998):
    """Check current clients"""
    url = f'ws://{host}:{port}'
    
    try:
        ws = await websockets.connect(url)
        
        # Register as admin
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': 'admin',
            'client_start_time': '2024',
            'capabilities': {'management': True}
        }))
        
        response = await ws.recv()
        logger.info("Connected to server")
        
        # Get client list
        await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
        response = await ws.recv()
        data = json.loads(response)
        
        clients = data.get('clients', [])
        logger.info(f"\nFound {len(clients)} clients:")
        
        for client in clients:
            logger.info(f"\n  Client ID: {client['id']}")
            logger.info(f"  User: {client.get('user', 'unknown')}")
            logger.info(f"  Connected: {client.get('connected_at', 'unknown')}")
            logger.info(f"  Last seen: {client.get('last_heartbeat', 'unknown')}")
        
        # Find our client - look for the newest one
        our_client = None
        # First try by username
        for client in clients:
            if client.get('user') == 'wjc2022':
                our_client = client
                break
        
        # If not found by username, use the newest client (highest ID)
        if not our_client and clients:
            # Sort by ID number and get the last one
            sorted_clients = sorted(clients, key=lambda c: int(c['id'].split('_')[1]))
            our_client = sorted_clients[-1]
        
        if our_client:
            client_id = our_client['id']
            logger.info(f"\n✓ Found our client: {client_id}")
            
            # Test execute_program
            logger.info("\nTesting execute_program command...")
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'execute_program',
                    'params': {
                        'program': 'cmd',
                        'args': ['/c', 'echo', 'Testing execute_program'],
                        'wait': True,
                        'shell': False
                    }
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result_data = data.get('result', {})
                    if isinstance(result_data, dict) and result_data.get('success'):
                        stdout = result_data.get('data', {}).get('stdout', '')
                        logger.info(f"✓ Command works! Output: {stdout.strip()}")
                    else:
                        logger.error(f"Command failed: {result_data.get('error')}")
            except asyncio.TimeoutError:
                logger.error("Command timeout")
        else:
            logger.warning("\nOur client (wjc2022) not found. It may still be restarting.")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    logger.info("Checking current clients...")
    asyncio.run(check_clients())

if __name__ == '__main__':
    main()