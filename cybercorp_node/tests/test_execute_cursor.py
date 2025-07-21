"""
Test execute_program command to launch Cursor
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestExecuteCursor')

async def test_execute_cursor(host='localhost', port=9998):
    """Test launching Cursor"""
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
        logger.info(f"Found {len(clients)} clients")
        
        # Use client_120 (our newly started client)
        client_id = 'client_120'
        logger.info(f"Using client: {client_id}")
        
        # Execute Cursor
        cursor_path = r"d:\cursor\Cursor.exe"
        logger.info(f"Launching: {cursor_path}")
        
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'execute_program',
                'params': {
                    'program': cursor_path,
                    'args': [],
                    'wait': False,
                    'shell': False
                }
            }
        }))
        
        await ws.recv()  # ack
        
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(result)
            
            if data.get('type') == 'command_result':
                result_data = data.get('result', {})
                if isinstance(result_data, dict) and result_data.get('success'):
                    pid = result_data.get('data', {}).get('pid')
                    logger.info(f"✓ Cursor launched! PID: {pid}")
                    logger.info("Waiting for Cursor to fully start...")
                    await asyncio.sleep(10)
                    
                    # Find Cursor windows
                    logger.info("\nFinding Cursor windows...")
                    await ws.send(json.dumps({
                        'type': 'forward_command',
                        'target_client': client_id,
                        'command': {
                            'type': 'command',
                            'command': 'find_cursor_windows'
                        }
                    }))
                    
                    await ws.recv()  # ack
                    result = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    data = json.loads(result)
                    
                    if data.get('type') == 'command_result':
                        result_data = data.get('result', {})
                        if isinstance(result_data, dict) and result_data.get('success'):
                            cursor_windows = result_data.get('data', {}).get('cursor_windows', [])
                            logger.info(f"Found {len(cursor_windows)} Cursor windows")
                            for w in cursor_windows:
                                logger.info(f"  - {w['title']} (HWND: {w['hwnd']})")
                else:
                    error = result_data.get('error', {})
                    logger.error(f"Failed to launch: {error}")
                    
                    if 'Unknown command' in str(error):
                        logger.error("execute_program command not found!")
                        logger.info("The client needs to be restarted to load new commands")
        except asyncio.TimeoutError:
            logger.error("Command timeout")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    logger.info("Testing execute_program command to launch Cursor")
    asyncio.run(test_execute_cursor())

if __name__ == '__main__':
    main()