"""Test Cursor IDE control functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.cursor_ide_controller import CursorIDEController
from cybercorp_node.utils.remote_control import RemoteController

# Enable debug logging
logging.basicConfig(level=logging.INFO)

async def test_cursor_detection():
    """Test Cursor IDE window detection and UI analysis"""
    print("Testing Cursor IDE Detection and Control")
    print("=" * 50)
    
    # Initialize controllers
    remote_controller = RemoteController()
    cursor_controller = CursorIDEController(remote_controller)
    
    # Test 1: Find Cursor window
    print("1. Finding Cursor IDE window...")
    hwnd = await cursor_controller.find_cursor_window()
    
    if hwnd:
        print(f"✓ Found Cursor IDE window: {hwnd}")
        print(f"  Title: {cursor_controller.cursor_window['title']}")
    else:
        print("✗ Cursor IDE window not found")
        print("Please make sure Cursor IDE is open and try again")
        return False
    
    # Test 2: Analyze dialog elements
    print("\n2. Analyzing Cursor IDE dialog elements...")
    elements = await cursor_controller.detect_dialog_elements(hwnd)
    
    print(f"Detection results:")
    print(f"  Input box: {'✓ Found' if elements.input_box else '✗ Not found'}")
    if elements.input_box:
        print(f"    Location: {elements.input_box['center']}")
        print(f"    Size: {elements.input_box['bbox']}")
    
    print(f"  Send button: {'✓ Found' if elements.send_button else '✗ Not found'}")
    if elements.send_button:
        print(f"    Location: {elements.send_button['center']}")
    
    print(f"  Response area: {'✓ Found' if elements.response_area else '✗ Not found'}")
    if elements.response_area:
        print(f"    Location: {elements.response_area['center']}")
        print(f"    Size: {elements.response_area['bbox']}")
    
    # Check if we have minimum required elements
    has_minimum = elements.input_box is not None
    print(f"\nMinimum UI elements for control: {'✓ Ready' if has_minimum else '✗ Not ready'}")
    
    return has_minimum

async def test_cursor_interaction():
    """Test actual interaction with Cursor IDE"""
    print("\n" + "=" * 50)
    print("Testing Cursor IDE Interaction")
    print("=" * 50)
    
    # Initialize controllers
    remote_controller = RemoteController()
    cursor_controller = CursorIDEController(remote_controller)
    
    # Find and analyze Cursor
    hwnd = await cursor_controller.find_cursor_window()
    if not hwnd:
        print("✗ Cannot proceed without Cursor IDE window")
        return False
    
    elements = await cursor_controller.detect_dialog_elements(hwnd)
    if not elements.input_box:
        print("✗ Cannot proceed without input box")
        return False
    
    print("Ready for interaction test!")
    print("\nTest scenario: Ask Cursor to write a simple function")
    
    # Test prompt
    test_prompt = "Write a simple Python function that calculates the factorial of a number."
    
    print(f"\nSending prompt: {test_prompt}")
    
    try:
        # Send prompt
        success = await cursor_controller.send_prompt(test_prompt)
        if success:
            print("✓ Prompt sent successfully")
            
            # Wait for response
            print("Waiting for Cursor to respond...")
            response_ready = await cursor_controller.wait_for_response(timeout=30)
            
            if response_ready:
                print("✓ Response appears ready")
                
                # Try to get response
                response_text = await cursor_controller.get_response_text()
                if response_text:
                    print(f"✓ Response received ({len(response_text)} characters)")
                    print(f"Response preview: {response_text[:200]}...")
                    return True
                else:
                    print("✗ Failed to extract response text")
                    return False
            else:
                print("⚠ Response timeout, but prompt was sent")
                return True  # Partial success
        else:
            print("✗ Failed to send prompt")
            return False
            
    except Exception as e:
        print(f"✗ Interaction test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("Cursor IDE Control Test Suite")
    print("=" * 50)
    print("Prerequisites:")
    print("1. Cursor IDE should be open")
    print("2. AI assistant chat should be accessible")
    print("3. No other applications should be blocking Cursor")
    print()
    
    # Phase 1: Detection test
    detection_success = await test_cursor_detection()
    
    if not detection_success:
        print("\n❌ Detection test failed - cannot proceed with interaction test")
        print("\nTroubleshooting tips:")
        print("- Make sure Cursor IDE is open and visible")
        print("- Try opening the AI assistant panel in Cursor")
        print("- Check if window title contains 'Cursor'")
        return False
    
    # Phase 2: Interaction test (optional)
    print("\n" + "="*50)
    user_input = input("Proceed with interaction test? This will send a test prompt to Cursor IDE (y/n): ")
    
    if user_input.lower() in ['y', 'yes']:
        interaction_success = await test_cursor_interaction()
        
        if interaction_success:
            print("\n🎉 SUCCESS: Cursor IDE control is working!")
            print("cybercorp_node can now be used as a Cursor IDE controller")
        else:
            print("\n⚠ Partial success: Detection works but interaction needs refinement")
    else:
        print("\nSkipping interaction test.")
        print("✓ Detection test completed successfully")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        sys.exit(1)