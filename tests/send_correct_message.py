"""Send the correct cleanup message to Cursor IDE"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_correct_cleanup_message():
    """Send the correct cleanup message to Cursor IDE"""
    
    print("Sending Correct Cleanup Message to Cursor IDE")
    print("=" * 50)
    
    try:
        # Connect to remote control
        remote_controller = RemoteController()
        await remote_controller.connect("cleanup_sender")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("No target client found")
            return False
        
        print(f"Connected to client: {target_client}")
        
        # The correct cleanup message
        cleanup_message = """请帮我清理backup/目录，具体要求：

1. 删除超过7天的备份文件
2. 保留最新的3个备份
3. 清理临时文件(.tmp, .log, .cache等)
4. 显示清理前后的目录大小对比
5. 生成详细的清理报告

请生成相应的脚本(Python或Shell)来完成这个任务，并确保安全性。"""
        
        print("Cleanup message to send:")
        print("-" * 30)
        print(cleanup_message)
        print("-" * 30)
        
        # First, clear any existing content in the dialog
        print("Clearing existing content...")
        await remote_controller.execute_command('send_keys', {'keys': '^a'})
        await asyncio.sleep(0.3)
        await remote_controller.execute_command('send_keys', {'keys': '{DELETE}'})
        await asyncio.sleep(0.5)
        
        # Set the correct message to clipboard
        print("Setting correct message to clipboard...")
        result = await remote_controller.execute_command('set_clipboard', {
            'text': cleanup_message
        })
        print(f"Clipboard set result: {result}")
        await asyncio.sleep(0.5)
        
        # Paste the correct message
        print("Pasting correct message...")
        result = await remote_controller.execute_command('send_keys', {'keys': '^v'})
        print(f"Paste result: {result}")
        await asyncio.sleep(1)
        
        # Send the message
        print("Sending message...")
        result = await remote_controller.execute_command('send_keys', {'keys': '{ENTER}'})
        print(f"Send result: {result}")
        await asyncio.sleep(1)
        
        print("SUCCESS! Correct cleanup message sent to Cursor IDE!")
        print("Please check Cursor IDE for the backup cleanup script response.")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    async def main():
        print("This will send the CORRECT cleanup message to Cursor IDE")
        print("(replacing the previous 'testmessageforcleanup')")
        
        await asyncio.sleep(2)  # Brief delay
        
        success = await send_correct_cleanup_message()
        
        if success:
            print("\nSUCCESS! The correct message has been sent!")
            print("Expected result: Cursor should generate a backup cleanup script")
            print("This validates our improved interaction system works!")
        else:
            print("\nFailed to send correct message")
    
    asyncio.run(main())