"""
Monitor process and window changes during Cursor launch
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('MonitorCursor')

async def monitor_cursor_launch(host='localhost', port=9998, client_id='client_108'):
    """Monitor process and window changes"""
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
        
        # Get initial processes
        logger.info("\n=== Getting initial Cursor processes ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'get_processes'
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=10.0)
        data = json.loads(result)
        
        initial_cursor_pids = set()
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                processes = result_data.get('data', {}).get('processes', [])
                cursor_processes = [p for p in processes if 'cursor' in p.get('name', '').lower()]
                initial_cursor_pids = set(p['pid'] for p in cursor_processes)
                logger.info(f"Initial Cursor processes: {len(cursor_processes)}")
                for p in cursor_processes:
                    logger.info(f"  - {p['name']} (PID: {p['pid']})")
        
        # Try different launch methods
        logger.info("\n=== Trying to launch Cursor with quotes ===")
        
        # Method 1: Win+R with quotes
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {
                    'keys': '#r'  # Win+R
                }
            }
        }))
        
        await ws.recv()  # ack
        await asyncio.wait_for(ws.recv(), timeout=5.0)
        await asyncio.sleep(1)
        
        # Type with quotes
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {
                    'keys': '"d:\\cursor\\Cursor.exe"'
                }
            }
        }))
        
        await ws.recv()  # ack
        await asyncio.wait_for(ws.recv(), timeout=5.0)
        logger.info('Typed: "d:\\cursor\\Cursor.exe"')
        
        # Press Enter
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {
                    'keys': '{ENTER}'
                }
            }
        }))
        
        await ws.recv()  # ack
        await asyncio.wait_for(ws.recv(), timeout=5.0)
        
        # Wait and check
        logger.info("\nWaiting 5 seconds for Cursor to start...")
        await asyncio.sleep(5)
        
        # Check processes again
        logger.info("\n=== Checking for new Cursor processes ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'get_processes'
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=10.0)
        data = json.loads(result)
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                processes = result_data.get('data', {}).get('processes', [])
                cursor_processes = [p for p in processes if 'cursor' in p.get('name', '').lower()]
                new_cursor_pids = set(p['pid'] for p in cursor_processes)
                
                new_pids = new_cursor_pids - initial_cursor_pids
                
                if new_pids:
                    logger.info(f"✓ New Cursor processes started: {len(new_pids)}")
                    for p in cursor_processes:
                        if p['pid'] in new_pids:
                            logger.info(f"  - {p['name']} (PID: {p['pid']})")
                else:
                    logger.warning("No new Cursor processes found")
        
        # Now check for windows
        logger.info("\n=== Checking for Cursor windows ===")
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
                cursor_data = result_data.get('data', {})
                cursor_windows = cursor_data.get('cursor_windows', [])
                
                if cursor_windows:
                    logger.info(f"✓ Found {len(cursor_windows)} Cursor window(s)!")
                    for w in cursor_windows:
                        logger.info(f"  - {w['title']}")
                        logger.info(f"    HWND: {w['hwnd']}")
                        logger.info(f"    PID: {w['pid']}")
                else:
                    logger.warning("Still no Cursor windows found")
                    
                    # Let's wait a bit more and check again
                    logger.info("\nWaiting 5 more seconds...")
                    await asyncio.sleep(5)
                    
                    # Check one more time
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
                            cursor_data = result_data.get('data', {})
                            cursor_windows = cursor_data.get('cursor_windows', [])
                            
                            if cursor_windows:
                                logger.info(f"✓ Now found {len(cursor_windows)} Cursor window(s)!")
                                for w in cursor_windows:
                                    logger.info(f"  - {w['title']}")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    logger.info("Monitoring Cursor launch process")
    logger.info("This will track process and window creation")
    logger.info("")
    
    asyncio.run(monitor_cursor_launch())

if __name__ == '__main__':
    main()