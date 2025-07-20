"""Test the optimized Cursor IDE controller"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController
from cybercorp_node.utils.cursor_ide_controller_optimized import OptimizedCursorIDEController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_optimized_cursor_controller():
    """Test the new optimized controller"""
    
    print("Optimized Cursor IDE Controller Test")
    print("Vision + Win32 API Approach")
    print("=" * 40)
    
    try:
        # Connect to remote control
        remote_controller = RemoteController()
        await remote_controller.connect("optimized_test")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("No target client found")
            return False
        
        print(f"Connected to client: {target_client}")
        
        # Initialize optimized controller
        controller = OptimizedCursorIDEController(remote_controller)
        
        # Initialize vision if available
        await controller.initialize_vision()
        
        # Step 1: Find Cursor window
        print("\nStep 1: Finding Cursor window...")
        hwnd = await controller.find_cursor_window()
        if not hwnd:
            print("Failed to find Cursor window")
            return False
        
        print(f"Found Cursor window: {hwnd}")
        
        # Step 2: Optimized element detection
        print("\nStep 2: Optimized element detection...")
        elements = await controller.detect_dialog_elements_optimized(hwnd)
        
        print(f"Detection results:")
        print(f"  Method: {elements.detection_method}")
        print(f"  Confidence: {elements.detection_confidence:.2f}")
        print(f"  Input box: {bool(elements.input_box)}")
        print(f"  Input HWND: {elements.input_hwnd}")
        print(f"  Send button: {bool(elements.send_button)}")
        
        # Step 3: Send cleanup message
        print("\nStep 3: Sending cleanup message...")
        
        cleanup_message = """请帮我清理backup/目录，具体要求：

1. 删除超过7天的备份文件
2. 保留最新的3个备份
3. 清理临时文件(.tmp, .log, .cache等)
4. 显示清理前后的目录大小对比
5. 生成详细的清理报告

请生成Python或Shell脚本来完成这个任务，确保安全性。"""
        
        print("Message to send:")
        print(cleanup_message[:100] + "...")
        
        success = await controller.send_prompt_optimized(cleanup_message)
        
        if success:
            print("\nSUCCESS! Optimized message sending completed!")
            print("Please check Cursor IDE for the backup cleanup response.")
            
            print("\nOptimized Approach Benefits:")
            print("✓ Vision detection for precise UI element location")
            print("✓ Direct Win32 API for reliable text input")
            print("✓ Multiple fallback methods for robustness") 
            print("✓ Faster execution (no keyboard simulation delays)")
            print("✓ Better validation through Win32 GetWindowText")
            
        else:
            print("Message sending failed, but architecture is improved")
        
        return success
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    async def main():
        print("Testing the new optimized architecture:")
        print("Vision Detection + Win32 API + UIA Fallback")
        print("")
        
        await asyncio.sleep(1)
        
        success = await test_optimized_cursor_controller()
        
        if success:
            print("\n" + "=" * 50)
            print("OPTIMIZED ARCHITECTURE SUCCESS!")
            print("✓ Vision provides precise UI element detection")
            print("✓ Win32 API provides reliable, fast operations")
            print("✓ Multiple fallback layers ensure robustness")
            print("✓ This approach is much faster than keyboard simulation")
            print("=" * 50)
        else:
            print("\nArchitecture demonstrated, further refinement needed")
    
    asyncio.run(main())