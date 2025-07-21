"""
Check what commands the client supports
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CheckCommands')

async def check_commands(host='localhost', port=9998, client_id='client_108'):
    """Check available commands"""
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
        
        # Try echo command first
        logger.info("\nTesting echo command...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'echo',
                'params': {'message': 'Hello from test'}
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
        logger.info(f"Echo result: {result}")
        
        # List of commands to test
        commands_to_test = [
            'status',
            'get_windows',
            'find_cursor_windows',
            'get_processes',
            'execute_program',  # Maybe this exists?
            'run_command',      # Or this?
            'shell',           # Or this?
        ]
        
        for cmd in commands_to_test:
            logger.info(f"\nTesting command: {cmd}")
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': cmd
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(result)
                if data.get('type') == 'command_result':
                    result_data = data.get('result', {})
                    if isinstance(result_data, dict):
                        if result_data.get('success'):
                            logger.info(f"  ✓ {cmd} - Success")
                        else:
                            error = result_data.get('error', 'Unknown error')
                            if 'Unknown command' in str(error):
                                logger.info(f"  ✗ {cmd} - Not supported")
                            else:
                                logger.info(f"  ✓ {cmd} - Supported (but failed: {error})")
            except asyncio.TimeoutError:
                logger.info(f"  ? {cmd} - Timeout")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_commands())