"""Remote control test to send cleanup message to Cursor IDE"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController
from cybercorp_node.utils.cursor_ide_controller import CursorIDEController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def execute_cursor_cleanup_test():
    """Execute the actual Cursor IDE cleanup test via remote control"""
    
    print("🚀 Remote Cursor IDE Cleanup Test")
    print("=" * 50)
    
    try:
        # Initialize remote controller
        print("📡 Connecting to remote control server...")
        remote_controller = RemoteController()
        
        # Connect to the remote control server
        await remote_controller.connect("cursor_test_controller")
        
        # Find a suitable target client
        print("🔍 Looking for available clients...")
        # Try to find a client (you might need to adjust the session name)
        target_client = await remote_controller.find_client("wjc2022")  # Use the actual username 
        if not target_client:
            print("⚠️ No target client found, trying to use any available client...")
            # Get list of clients and use the first one
            windows = await remote_controller.get_windows()
            if windows:
                print("✅ Found target client via window enumeration")
            else:
                print("❌ No clients available - make sure a cybercorp_node client is running")
                return False
        
        print("✅ Connected to remote control server")
        
        # Initialize Cursor IDE controller with improved capabilities
        print("🎯 Initializing enhanced Cursor IDE controller...")
        cursor_controller = CursorIDEController(remote_controller)
        
        # Enable detailed logging for this test
        logging.getLogger('cybercorp_node.utils.cursor_ide_controller').setLevel(logging.DEBUG)
        
        # Step 1: Find Cursor IDE window
        print("\n=== Step 1: Finding Cursor IDE Window ===")
        hwnd = await cursor_controller.find_cursor_window()
        if not hwnd:
            print("❌ Could not find Cursor IDE window")
            print("Please ensure Cursor IDE is running and visible")
            return False
        
        print(f"✅ Found Cursor IDE window: {hwnd}")
        
        # Step 2: Enhanced UI detection
        print("\n=== Step 2: Enhanced UI Element Detection ===")
        elements = await cursor_controller.detect_dialog_elements(hwnd)
        
        print("Detection Results:")
        print(f"  📥 Input box detected: {bool(elements.input_box)}")
        if elements.input_box:
            print(f"      Position: {elements.input_box['center']}")
            print(f"      Source: {elements.input_box.get('source', 'unknown')}")
            print(f"      Confidence: {elements.detection_confidence:.2f}")
        
        print(f"  🔘 Send button detected: {bool(elements.send_button)}")
        if elements.send_button:
            print(f"      Position: {elements.send_button['center']}")
            print(f"      Source: {elements.send_button.get('source', 'unknown')}")
        
        print(f"  📄 Response area detected: {bool(elements.response_area)}")
        
        # Step 3: Send the actual cleanup message
        print("\n=== Step 3: Sending Backup Cleanup Request ===")
        
        cleanup_message = """请帮我清理一下backup/目录，具体要求：

1. 删除超过7天的备份文件
2. 保留最新的3个备份
3. 清理临时文件(.tmp, .log, .cache等)
4. 显示清理前后的目录大小对比
5. 生成详细的清理报告

请生成相应的脚本(Python或Shell)来完成这个任务，并确保安全性(先备份重要文件)。"""
        
        print("Message to send:")
        print(f'"{cleanup_message[:100]}..."')
        
        print("\n🚀 Executing improved send_prompt with validation...")
        success = await cursor_controller.send_prompt(cleanup_message)
        
        if success:
            print("✅ Message sent successfully!")
            print("📝 Cursor IDE should now be processing the backup cleanup request")
            
            # Step 4: Check adaptive learning results
            print("\n=== Step 4: Adaptive Learning Results ===")
            memory = cursor_controller.position_memory
            print(f"📚 Learning Status:")
            print(f"   Success count: {memory.success_count}")
            print(f"   Failure count: {memory.failure_count}")
            print(f"   Learned input positions: {len(memory.successful_input_positions)}")
            print(f"   Window layout hash: {memory.window_layout_hash}")
            
            if memory.successful_input_positions:
                print(f"   Recent successful positions: {memory.successful_input_positions[-3:]}")
            
            # Step 5: Wait a moment and get response (optional)
            print("\n=== Step 5: Waiting for Response ===")
            print("⏳ Waiting for Cursor to process the request...")
            
            response_ready = await cursor_controller.wait_for_response(timeout=30)
            if response_ready:
                print("✅ Response appears ready")
                
                # Try to get response text
                response_text = await cursor_controller.get_response_text()
                if response_text:
                    print(f"📋 Response preview: {response_text[:200]}...")
                else:
                    print("⚠️ Could not extract response text automatically")
            else:
                print("⏰ Timeout waiting for response, but message was sent")
                
        else:
            print("❌ Failed to send message")
            print("This might indicate UI detection issues")
        
        print("\n" + "=" * 50)
        print("🎯 Test Summary:")
        print(f"   Window found: ✅")
        print(f"   UI elements detected: {'✅' if elements.input_box else '❌'}")
        print(f"   Message sent: {'✅' if success else '❌'}")
        print(f"   Detection confidence: {elements.detection_confidence:.2f}")
        
        if success:
            print("\n🎉 ACTUAL CURSOR INTERACTION SUCCESSFUL!")
            print("Check Cursor IDE to see the generated backup cleanup script.")
        
        return success
        
    except Exception as e:
        logger.error(f"Remote test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    async def main():
        print("Starting remote-controlled Cursor IDE cleanup test...")
        print("This will actually send the cleanup request to Cursor IDE!")
        
        success = await execute_cursor_cleanup_test()
        
        if success:
            print("\n🎉 SUCCESS! The improved system successfully:")
            print("   • Found Cursor IDE window via remote control")
            print("   • Used enhanced UI detection with confidence scoring")
            print("   • Sent the backup cleanup message with validation")
            print("   • Learned from the successful interaction")
            print("\nCheck Cursor IDE for the backup cleanup script!")
        else:
            print("\n❌ Test failed. Check the logs for details.")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏸️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()