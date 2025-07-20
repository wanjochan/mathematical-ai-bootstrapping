"""
Restart the client to load new commands
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('RestartClient')

async def restart_client(host='localhost', port=9998, client_id='client_108'):
    """Restart client"""
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
        
        # Send restart command
        logger.info(f"\nSending restart command to client {client_id}...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'restart_client',
                'params': {
                    'delay': 2,
                    'reason': 'Loading new execute_program command'
                }
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data = json.loads(result)
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                logger.info("✓ Client restart initiated")
                logger.info("Waiting for client to restart...")
                
                # Wait for restart
                await asyncio.sleep(5)
                
                # Check if client is back online
                logger.info("\nChecking if client is back online...")
                await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
                response = await ws.recv()
                data = json.loads(response)
                
                clients = data.get('clients', [])
                new_client = None
                
                # Look for the restarted client (might have new ID)
                for client in clients:
                    if client.get('user') == 'wjc2022':  # Your username
                        new_client = client
                        break
                
                if new_client:
                    new_client_id = new_client['id']
                    logger.info(f"✓ Client restarted with ID: {new_client_id}")
                    
                    # Test execute_program
                    logger.info("\nTesting execute_program command...")
                    await ws.send(json.dumps({
                        'type': 'forward_command',
                        'target_client': new_client_id,
                        'command': {
                            'type': 'command',
                            'command': 'execute_program',
                            'params': {
                                'program': 'cmd',
                                'args': ['/c', 'echo', 'Execute program works!'],
                                'wait': True,
                                'shell': False
                            }
                        }
                    }))
                    
                    await ws.recv()  # ack
                    result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(result)
                    
                    if data.get('type') == 'command_result':
                        result_data = data.get('result', {})
                        if isinstance(result_data, dict) and result_data.get('success'):
                            stdout = result_data.get('data', {}).get('stdout', '')
                            logger.info(f"✓ Command output: {stdout.strip()}")
                            logger.info("\n✓ New command successfully loaded!")
                        else:
                            logger.error("Command still not working after restart")
                else:
                    logger.warning("Client not found after restart")
            else:
                logger.error(f"Restart failed: {result_data}")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    logger.info("Restarting client to load new execute_program command")
    asyncio.run(restart_client())

if __name__ == '__main__':
    main()