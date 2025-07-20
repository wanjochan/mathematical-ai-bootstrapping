"""
Test controlling Chrome browser as an alternative
"""

import asyncio
import json
import websockets
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestChrome')

async def test_chrome_control(host='localhost', port=9998):
    """Test controlling Chrome browser"""
    url = f'ws://{host}:{port}'
    
    try:
        ws = await websockets.connect(url)
        
        # Register
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
        if not clients:
            logger.warning("No clients found")
            return
        
        # Test first client
        client_id = clients[0]['id']
        logger.info(f"\nTesting Chrome control on client: {client_id}")
        
        # Get windows
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
                
                # Find Chrome window
                chrome_windows = [w for w in windows if 'Chrome' in w.get('title', '') and w.get('class') == 'Chrome_WidgetWin_1']
                
                if chrome_windows:
                    chrome_window = chrome_windows[0]
                    logger.info(f"\n✓ Found Chrome window: {chrome_window['title']}")
                    chrome_hwnd = chrome_window['hwnd']
                    
                    # Activate Chrome
                    await ws.send(json.dumps({
                        'type': 'forward_command',
                        'target_client': client_id,
                        'command': {
                            'type': 'command',
                            'command': 'activate_window',
                            'params': {'hwnd': chrome_hwnd}
                        }
                    }))
                    
                    await ws.recv()  # ack
                    result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    logger.info("✓ Chrome window activated")
                    
                    # Type in address bar (Ctrl+L then type)
                    await asyncio.sleep(1)
                    
                    # Focus address bar
                    await ws.send(json.dumps({
                        'type': 'forward_command',
                        'target_client': client_id,
                        'command': {
                            'type': 'command',
                            'command': 'send_keys',
                            'params': {'keys': '^l'}  # Ctrl+L
                        }
                    }))
                    
                    await ws.recv()  # ack
                    await asyncio.wait_for(ws.recv(), timeout=5.0)
                    logger.info("✓ Focused address bar")
                    
                    # Type test URL
                    await asyncio.sleep(0.5)
                    test_url = "https://www.google.com/search?q=CyberCorp+Node+Test"
                    
                    await ws.send(json.dumps({
                        'type': 'forward_command',
                        'target_client': client_id,
                        'command': {
                            'type': 'command',
                            'command': 'type_text',
                            'params': {'text': test_url}
                        }
                    }))
                    
                    await ws.recv()  # ack
                    result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    logger.info(f"✓ Typed URL: {test_url}")
                    
                    logger.info("\n✓ Chrome control test completed successfully!")
                else:
                    logger.warning("No Chrome windows found")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Test Chrome control')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    
    args = parser.parse_args()
    
    logger.info("Testing Chrome browser control...")
    logger.info("")
    
    asyncio.run(test_chrome_control(args.host, args.port))

if __name__ == '__main__':
    main()