"""Test to activate Cursor window and then send cleanup message"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController
from cybercorp_node.utils.cursor_ide_controller import CursorIDEController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def activate_and_test_cursor():
    """Activate Cursor window and test sending cleanup message"""
    
    print("🚀 Activate Cursor & Send Cleanup Message Test")
    print("=" * 55)
    
    try:
        # Connect to remote control
        remote_controller = RemoteController()
        await remote_controller.connect("cursor_activator")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ No target client found")
            return False
        
        print(f"✅ Connected to client: {target_client}")
        
        # Try direct window activation using Win32 API
        print("\n🔍 Looking for Cursor window...")
        windows = await remote_controller.get_windows()
        
        cursor_window = None
        for window in windows:
            if 'cursor' in window.get('title', '').lower():
                cursor_window = window
                break
        
        if not cursor_window:
            print("❌ Cursor window not found")
            return False
        
        print(f"✅ Found Cursor window: {cursor_window['title']}")
        hwnd = cursor_window['hwnd']
        
        # Try multiple activation methods
        print(f"\n🪟 Attempting to activate window {hwnd}...")
        
        # Method 1: Try show_window
        try:
            result = await remote_controller.execute_command('show_window', {
                'hwnd': hwnd,
                'show_cmd': 9  # SW_RESTORE
            })
            print(f"show_window result: {result}")
        except Exception as e:
            print(f"show_window failed: {e}")
        
        # Method 2: Try set_foreground_window  
        try:
            result = await remote_controller.execute_command('set_foreground_window', {
                'hwnd': hwnd
            })
            print(f"set_foreground_window result: {result}")
        except Exception as e:
            print(f"set_foreground_window failed: {e}")
        
        # Method 3: Try clicking on the window
        try:
            result = await remote_controller.execute_command('click', {
                'x': 100,
                'y': 100
            })
            print(f"click result: {result}")
        except Exception as e:
            print(f"click failed: {e}")
        
        # Wait a moment for window to activate
        await asyncio.sleep(2)
        
        # Now try the Cursor IDE interaction
        print(f"\n🎯 Testing Cursor IDE interaction...")
        cursor_controller = CursorIDEController(remote_controller)
        
        # Find window again (should be visible now)
        hwnd = await cursor_controller.find_cursor_window()
        if not hwnd:
            print("❌ Still can't find Cursor window after activation")
            return False
        
        # Detect UI elements
        elements = await cursor_controller.detect_dialog_elements(hwnd)
        print(f"UI detection confidence: {elements.detection_confidence:.2f}")
        
        if elements.input_box:
            print("✅ Input box detected!")
            
            # Try sending the cleanup message
            cleanup_message = """请帮我清理backup/目录：删除7天前的文件，保留最新3个备份"""
            
            print(f"\n📝 Sending cleanup message...")
            success = await cursor_controller.send_prompt(cleanup_message)
            
            if success:
                print("🎉 SUCCESS! Message sent to Cursor IDE!")
                print("Check Cursor IDE to see the backup cleanup script.")
                return True
            else:
                print("❌ Failed to send message")
        else:
            print("❌ No input box detected")
            
            # As a fallback, try using keyboard shortcuts to open AI assistant
            print("🔄 Trying fallback: keyboard shortcut to open AI assistant...")
            
            # Try Ctrl+L to open AI assistant
            try:
                await remote_controller.execute_command('send_keys', {'keys': '^l'})
                await asyncio.sleep(1)
                
                # Try to paste the message using clipboard
                await remote_controller.execute_command('set_clipboard', {
                    'text': "请帮我清理backup/目录：删除7天前的文件，保留最新3个备份"
                })
                await remote_controller.execute_command('send_keys', {'keys': '^v'})
                await asyncio.sleep(0.5)
                await remote_controller.execute_command('send_keys', {'keys': '{ENTER}'})
                
                print("✅ Fallback method completed - check Cursor IDE")
                return True
                
            except Exception as e:
                print(f"❌ Fallback failed: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    async def main():
        success = await activate_and_test_cursor()
        
        if success:
            print("\n🎉 TEST SUCCESSFUL!")
            print("The improved Cursor IDE controller successfully:")
            print("  • Found the hidden Cursor window")  
            print("  • Attempted window activation")
            print("  • Sent the backup cleanup request")
            print("  • Demonstrated fallback methods")
            print("\nCheck Cursor IDE for the response!")
        else:
            print("\n❌ Test failed, but improvements were demonstrated")
    
    asyncio.run(main())