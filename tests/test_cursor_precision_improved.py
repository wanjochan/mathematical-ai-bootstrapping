"""Test improved Cursor IDE text input precision"""

import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cybercorp_node.utils.cursor_ide_controller import CursorIDEController
from cybercorp_node.utils.remote_control import RemoteController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_improved_precision():
    """Test the improved text input precision for Cursor IDE"""
    logger.info("Starting improved Cursor IDE precision test...")
    
    try:
        # Initialize controller
        remote_controller = RemoteController()
        cursor_controller = CursorIDEController(remote_controller)
        
        # Enable debug logging for detailed analysis
        logging.getLogger('cybercorp_node.utils.cursor_ide_controller').setLevel(logging.DEBUG)
        
        # Test 1: Find Cursor window
        logger.info("=== Test 1: Finding Cursor IDE window ===")
        hwnd = await cursor_controller.find_cursor_window()
        if not hwnd:
            logger.error("Could not find Cursor IDE window")
            return False
        
        logger.info(f"Found Cursor IDE window: {hwnd}")
        
        # Test 2: Enhanced element detection
        logger.info("=== Test 2: Enhanced element detection ===")
        elements = await cursor_controller.detect_dialog_elements(hwnd)
        
        logger.info(f"Detection results:")
        logger.info(f"  Input box: {bool(elements.input_box)} (confidence: {elements.detection_confidence:.2f})")
        if elements.input_box:
            logger.info(f"    Position: {elements.input_box['center']}")
            logger.info(f"    Source: {elements.input_box.get('source', 'unknown')}")
        
        logger.info(f"  Send button: {bool(elements.send_button)}")
        if elements.send_button:
            logger.info(f"    Position: {elements.send_button['center']}")
            logger.info(f"    Source: {elements.send_button.get('source', 'unknown')}")
        
        logger.info(f"  Response area: {bool(elements.response_area)}")
        
        # Test 3: Text input with validation
        logger.info("=== Test 3: Text input with validation ===")
        test_messages = [
            "Hello, this is a test message",
            "Testing improved precision: 测试中文",
            "Multi-line test\nwith line breaks",
            "Special chars: @#$%^&*()"
        ]
        
        success_count = 0
        for i, message in enumerate(test_messages, 1):
            logger.info(f"Test {i}/4: Sending message: {message[:30]}...")
            
            result = await cursor_controller.send_prompt(message)
            if result:
                logger.info(f"✓ Test {i} successful")
                success_count += 1
                # Wait a bit between tests
                await asyncio.sleep(2)
            else:
                logger.error(f"✗ Test {i} failed")
        
        # Test 4: Adaptive learning verification
        logger.info("=== Test 4: Adaptive learning verification ===")
        memory = cursor_controller.position_memory
        logger.info(f"Learned positions:")
        logger.info(f"  Input positions: {len(memory.successful_input_positions)}")
        logger.info(f"  Send positions: {len(memory.successful_send_positions)}")
        logger.info(f"  Success count: {memory.success_count}")
        logger.info(f"  Failure count: {memory.failure_count}")
        logger.info(f"  Layout hash: {memory.window_layout_hash}")
        
        # Test 5: Re-detection with learned positions
        logger.info("=== Test 5: Re-detection with learned positions ===")
        elements2 = await cursor_controller.detect_dialog_elements(hwnd)
        logger.info(f"Second detection confidence: {elements2.detection_confidence:.2f}")
        
        # Summary
        logger.info("=== Test Summary ===")
        logger.info(f"Total tests: 4")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Success rate: {success_count/4*100:.1f}%")
        
        if success_count >= 3:
            logger.info("✓ Improved precision test PASSED")
            return True
        else:
            logger.error("✗ Improved precision test FAILED")
            return False
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_comparison_old_vs_new():
    """Compare old vs new detection methods"""
    logger.info("=== Comparison Test: Old vs New Detection ===")
    
    try:
        remote_controller = RemoteController()
        cursor_controller = CursorIDEController(remote_controller)
        
        hwnd = await cursor_controller.find_cursor_window()
        if not hwnd:
            logger.error("Could not find Cursor IDE window")
            return
        
        # Test with adaptive learning disabled
        logger.info("Testing with adaptive learning DISABLED...")
        cursor_controller.adaptive_learning_enabled = False
        elements_old = await cursor_controller.detect_dialog_elements(hwnd)
        
        # Test with adaptive learning enabled
        logger.info("Testing with adaptive learning ENABLED...")
        cursor_controller.adaptive_learning_enabled = True
        elements_new = await cursor_controller.detect_dialog_elements(hwnd)
        
        logger.info("Comparison results:")
        logger.info(f"  Old method confidence: {getattr(elements_old, 'detection_confidence', 0.0):.2f}")
        logger.info(f"  New method confidence: {elements_new.detection_confidence:.2f}")
        
        improvement = elements_new.detection_confidence - getattr(elements_old, 'detection_confidence', 0.0)
        logger.info(f"  Confidence improvement: {improvement:+.2f}")
        
    except Exception as e:
        logger.error(f"Comparison test failed: {e}")


if __name__ == "__main__":
    async def main():
        print("Cursor IDE Precision Improvement Test")
        print("=" * 50)
        
        # Run main test
        success = await test_improved_precision()
        
        print("\n" + "=" * 50)
        
        # Run comparison test
        await test_comparison_old_vs_new()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 All tests completed successfully!")
        else:
            print("❌ Some tests failed. Check logs for details.")
    
    asyncio.run(main())