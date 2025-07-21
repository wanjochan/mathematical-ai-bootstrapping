"""
Test Cursor IDE automation
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestCursorAutomation')

async def test_cursor_automation(host='localhost', port=9998):
    """Test Cursor automation functionality"""
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
        
        # Test 1: Simple code generation
        logger.info("\n=== Test 1: Generate Python function ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'execute_cursor_task',
                'params': {
                    'task_type': 'generate',
                    'prompt': 'Create a Python function that calculates fibonacci numbers recursively',
                    'timeout': 20
                }
            }
        }))
        
        await ws.recv()  # ack
        
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=30.0)
            data = json.loads(result)
            
            if data.get('type') == 'command_result':
                result_data = data.get('result', {})
                if isinstance(result_data, dict) and result_data.get('success'):
                    task_data = result_data.get('data', {})
                    logger.info(f"✓ Task completed in {task_data.get('duration', 0):.1f}s")
                    logger.info(f"Task ID: {task_data.get('task_id')}")
                    logger.info(f"Result: {task_data.get('result')}")
                else:
                    error = result_data.get('error', {})
                    logger.error(f"Task failed: {error}")
                    
                    # Check if we need to restart client
                    if 'Unknown command' in str(error):
                        logger.info("\n!!! Client needs to be restarted to load cursor_automation module !!!")
                        logger.info("Please restart the client and run this test again")
                        return
        except asyncio.TimeoutError:
            logger.error("Task timeout")
        
        # Test 2: Open file and edit
        logger.info("\n=== Test 2: Open file and edit ===")
        test_file = r"d:\dev\mathematical-ai-bootstrapping\cybercorp_node\test_cursor_target.py"
        
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'execute_cursor_task',
                'params': {
                    'file_path': test_file,
                    'task_type': 'edit',
                    'prompt': 'Add a docstring to the main function explaining what it does',
                    'timeout': 20
                }
            }
        }))
        
        await ws.recv()  # ack
        
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=30.0)
            data = json.loads(result)
            
            if data.get('type') == 'command_result':
                result_data = data.get('result', {})
                if isinstance(result_data, dict) and result_data.get('success'):
                    logger.info("✓ File editing task completed")
                else:
                    logger.error(f"File editing failed: {result_data.get('error')}")
        except asyncio.TimeoutError:
            logger.error("File editing timeout")
        
        # Test 3: Explain code
        logger.info("\n=== Test 3: Explain code ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'execute_cursor_task',
                'params': {
                    'task_type': 'explain',
                    'prompt': 'Explain how the CyberCorp client-server architecture works',
                    'timeout': 20
                }
            }
        }))
        
        await ws.recv()  # ack
        
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=30.0)
            data = json.loads(result)
            
            if data.get('type') == 'command_result':
                result_data = data.get('result', {})
                if isinstance(result_data, dict) and result_data.get('success'):
                    logger.info("✓ Code explanation completed")
                else:
                    logger.error(f"Explanation failed: {result_data.get('error')}")
        except asyncio.TimeoutError:
            logger.error("Explanation timeout")
        
        logger.info("\n🎉 Cursor automation tests completed!")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    logger.info("Testing Cursor IDE automation")
    logger.info("This will test various Cursor AI capabilities")
    logger.info("")
    
    asyncio.run(test_cursor_automation())

if __name__ == '__main__':
    main()