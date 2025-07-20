"""
Restart client_120 specifically
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('RestartClient120')

async def restart_client_120(host='localhost', port=9998):
    """Restart client 120"""
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
        
        # Try to restart client_120
        client_id = 'client_120'
        logger.info(f"Attempting to restart {client_id}...")
        
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'restart_client',
                'params': {
                    'delay': 2,
                    'reason': 'Loading cursor_automation module'
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
                    logger.info("✓ Restart command sent successfully")
                else:
                    logger.error(f"Restart failed: {result_data}")
        except asyncio.TimeoutError:
            logger.info("Client may have already restarted")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    logger.info("Restarting client_120")
    asyncio.run(restart_client_120())

if __name__ == '__main__':
    main()