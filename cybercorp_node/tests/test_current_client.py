"""
Test the current user's client
"""

import asyncio
import json
import websockets
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestCurrentClient')

async def test_current_client(host='localhost', port=9998, client_id='client_108'):
    """Test the current user's client"""
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
        logger.info(f"Registration: {response}")
        
        # Get client list
        await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
        response = await ws.recv()
        data = json.loads(response)
        
        clients = data.get('clients', [])
        logger.info(f"Found {len(clients)} clients")
        
        # Find our client
        our_client = None
        for client in clients:
            if client['id'] == client_id:
                our_client = client
                break
        
        if not our_client:
            logger.error(f"Client {client_id} not found!")
            logger.info("Available clients:")
            for client in clients:
                logger.info(f"  - {client['id']} (user: {client.get('user', 'unknown')})")
            return
        
        logger.info(f"\nTesting client: {client_id} (user: {our_client.get('user', 'unknown')})")
        
        # Test 1: Get windows
        logger.info("\n1. Getting windows...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'get_windows'
            }
        }))
        
        await ws.recv()  # ack
        
        result = await asyncio.wait_for(ws.recv(), timeout=10.0)
        data = json.loads(result)
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                windows = result_data.get('data', {}).get('windows', [])
                logger.info(f"✓ Found {len(windows)} windows")
                
                # Show some windows
                for i, window in enumerate(windows[:10]):
                    logger.info(f"  {i+1}. {window['title'][:60]}... (Class: {window['class']})")
                
                # Look for Cursor
                cursor_windows = [w for w in windows if 'cursor' in w.get('title', '').lower()]
                if cursor_windows:
                    logger.info(f"\n✓ Found {len(cursor_windows)} Cursor window(s):")
                    for w in cursor_windows:
                        logger.info(f"  - {w['title']} (hwnd: {w['hwnd']})")
                else:
                    logger.info("\n✗ No Cursor windows found in title search")
        
        # Test 2: Find Cursor windows specifically
        logger.info("\n2. Using find_cursor_windows command...")
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
                chrome_windows = cursor_data.get('all_chrome_windows', [])
                
                if cursor_windows:
                    logger.info(f"✓ Found {len(cursor_windows)} Cursor window(s) by process:")
                    for w in cursor_windows:
                        logger.info(f"  - {w['title']} (Process: {w['process_name']}, PID: {w['pid']})")
                else:
                    logger.info("✗ No Cursor windows found by process")
                    
                    if chrome_windows:
                        logger.info(f"\nFound {len(chrome_windows)} Chrome_WidgetWin_1 windows:")
                        for w in chrome_windows[:5]:
                            logger.info(f"  - {w['title'][:50]}... (Process: {w['process_name']})")
        
        # Test 3: System info
        logger.info("\n3. Getting system status...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'status'
            }
        }))
        
        await ws.recv()  # ack
        
        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data = json.loads(result)
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict):
                logger.info("✓ System status received")
                if 'data' in result_data:
                    status_data = result_data['data']
                    if isinstance(status_data, dict):
                        logger.info(f"  Platform: {status_data.get('platform', 'unknown')}")
                        logger.info(f"  User: {status_data.get('user', 'unknown')}")
        
        await ws.close()
        logger.info("\n✓ Test completed!")
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Test current client')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    parser.add_argument('--client-id', default='client_108', help='Client ID to test')
    
    args = parser.parse_args()
    
    logger.info(f"Testing current user's client: {args.client_id}")
    logger.info("")
    
    asyncio.run(test_current_client(args.host, args.port, args.client_id))

if __name__ == '__main__':
    main()