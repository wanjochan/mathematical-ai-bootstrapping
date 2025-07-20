"""Test controlling Cursor IDE"""

import asyncio
import sys
from utils.remote_control import RemoteController, WindowController, BatchExecutor
import logging

# Set UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def control_cursor_workflow():
    """Control Cursor to open and modify workflow.md"""
    controller = RemoteController()
    
    try:
        # Connect
        await controller.connect("cursor_test")
        
        # Find wjchk client
        await controller.find_client("wjchk")
        
        # Find Cursor window
        window = await controller.find_window("mathematical-ai-bootstrapping - Cursor")
        if not window:
            print("Cursor window not found!")
            return
            
        cursor = WindowController(controller, window['hwnd'], window['title'])
        print(f"Found Cursor: {window['title']} (hwnd: {window['hwnd']})")
        
        # Take initial screenshot
        print("\nTaking initial screenshot...")
        screenshot_path = await cursor.screenshot("cursor_before.png")
        if screenshot_path:
            print(f"Screenshot saved: {screenshot_path}")
            
        # Activate and send command
        print("\nSending command to Cursor chat...")
        
        # Based on the screenshot, the chat input is at approximately x=1495, y=112
        success = await cursor.send_command(
            "打开docs/workflow.md文件，将其中过于谄媚的措辞修改得更加中立专业",
            input_coords=(1495, 112)
        )
        
        if success:
            print("Command sent successfully!")
            
            # Wait a bit for Cursor to process
            await asyncio.sleep(5)
            
            # Take another screenshot
            print("\nTaking verification screenshot...")
            screenshot_path = await cursor.screenshot("cursor_after.png")
            if screenshot_path:
                print(f"Screenshot saved: {screenshot_path}")
        else:
            print("Failed to send command")
            
    finally:
        await controller.close()


async def test_batch_control():
    """Test batch command execution"""
    controller = RemoteController()
    
    try:
        await controller.connect("batch_test")
        await controller.find_client("wjchk")
        
        # Create batch executor
        batch = BatchExecutor(controller)
        
        # Add commands
        batch.add_command('activate_window', {'hwnd': 5898916})
        batch.add_wait(1)
        batch.add_click(1495, 112)
        batch.add_wait(0.5)
        batch.add_keys('^a{DELETE}')
        batch.add_wait(0.3)
        batch.add_keys('测试批处理命令')
        batch.add_wait(0.5)
        batch.add_command('screenshot', {'hwnd': 5898916})
        
        # Execute all
        print("Executing batch commands...")
        results = await batch.execute()
        
        for i, result in enumerate(results):
            print(f"Command {i+1}: {result}")
            
    finally:
        await controller.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Cursor control')
    parser.add_argument('--batch', action='store_true', help='Test batch execution')
    
    args = parser.parse_args()
    
    if args.batch:
        asyncio.run(test_batch_control())
    else:
        asyncio.run(control_cursor_workflow())