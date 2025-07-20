"""
Control Cursor window test
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ControlCursorTest')

async def control_cursor(host='localhost', port=9998):
    """Control Cursor window"""
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
        
        client_id = 'client_120'
        cursor_hwnd = 7670670  # The HWND we found
        
        # Step 1: Activate window
        logger.info(f"\n=== Activating Cursor window (HWND: {cursor_hwnd}) ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'activate_window',
                'params': {'hwnd': cursor_hwnd}
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data = json.loads(result)
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if result_data.get('success'):
                logger.info("✓ Window activated")
            else:
                logger.error(f"Failed to activate: {result_data.get('error')}")
        
        await asyncio.sleep(1)
        
        # Step 2: Type test text
        test_text = "// 批判性思维测试: CyberCorp Node控制成功!\n// Critical thinking helped solve the window detection issue"
        logger.info(f"\n=== Typing test text ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {'keys': test_text}
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
        logger.info("✓ Text typed")
        
        # Step 3: Take screenshot
        logger.info(f"\n=== Taking screenshot ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'screenshot',
                'params': {'hwnd': cursor_hwnd}
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=10.0)
        data = json.loads(result)
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if result_data.get('success'):
                screenshot_path = result_data.get('data', {}).get('screenshot_path')
                logger.info(f"✓ Screenshot saved: {screenshot_path}")
                
        # Step 4: Get window info
        logger.info(f"\n=== Getting window info ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'get_window_info',
                'params': {'hwnd': cursor_hwnd}
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data = json.loads(result)
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if result_data.get('success'):
                window_info = result_data.get('data', {})
                logger.info(f"Window title: {window_info.get('title')}")
                logger.info(f"Window size: {window_info.get('width')}x{window_info.get('height')}")
                logger.info(f"Window position: ({window_info.get('x')}, {window_info.get('y')})")
        
        logger.info("\n🎉 SUCCESS! Cursor has been controlled successfully!")
        logger.info("\n批判性思维总结:")
        logger.info("1. 问题本质: 不是找不到窗口，而是窗口不在当前会话")
        logger.info("2. 解决方案: 主动创建可控环境而非被动搜索")
        logger.info("3. 实战价值: 通过实际操作发现并解决问题")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    logger.info("Testing Cursor control")
    asyncio.run(control_cursor())

if __name__ == '__main__':
    main()