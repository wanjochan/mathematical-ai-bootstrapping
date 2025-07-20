"""Debug Cursor IDE interaction step by step"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def debug_cursor_interaction():
    """Debug Cursor IDE interaction step by step"""
    
    print("🔍 Cursor IDE Interaction Debug")
    print("=" * 40)
    
    try:
        # Connect to remote control
        remote_controller = RemoteController()
        await remote_controller.connect("debug_cursor")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ No target client found")
            return False
        
        print(f"✅ Connected to client: {target_client}")
        
        # Step 1: Get current window state
        print(f"\n📋 Step 1: Check current window state")
        windows = await remote_controller.get_windows()
        
        cursor_window = None
        for window in windows:
            if 'cursor' in window.get('title', '').lower():
                cursor_window = window
                print(f"Cursor window: {window['title']}")
                print(f"  HWND: {window['hwnd']}")
                print(f"  Visible: {window.get('visible', False)}")
                print(f"  Active: {window.get('is_active', False)}")
                break
        
        if not cursor_window:
            print("❌ Cursor window not found")
            return False
        
        hwnd = cursor_window['hwnd']
        
        # Step 2: Try to bring window to foreground
        print(f"\n🪟 Step 2: Bring Cursor to foreground")
        
        # Method 1: ShowWindow with SW_RESTORE and SW_SHOW
        try:
            print("Trying ShowWindow SW_RESTORE...")
            result = await remote_controller.execute_command('win32_call', {
                'function': 'ShowWindow',
                'args': [hwnd, 9]  # SW_RESTORE
            })
            print(f"ShowWindow result: {result}")
            await asyncio.sleep(1)
            
            print("Trying ShowWindow SW_SHOW...")
            result = await remote_controller.execute_command('win32_call', {
                'function': 'ShowWindow', 
                'args': [hwnd, 5]  # SW_SHOW
            })
            print(f"ShowWindow result: {result}")
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"ShowWindow failed: {e}")
        
        # Method 2: SetForegroundWindow
        try:
            print("Trying SetForegroundWindow...")
            result = await remote_controller.execute_command('win32_call', {
                'function': 'SetForegroundWindow',
                'args': [hwnd]
            })
            print(f"SetForegroundWindow result: {result}")
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"SetForegroundWindow failed: {e}")
        
        # Step 3: Check if window became visible
        print(f"\n👀 Step 3: Check window visibility after activation")
        windows = await remote_controller.get_windows()
        for window in windows:
            if window['hwnd'] == hwnd:
                print(f"Cursor window after activation:")
                print(f"  Visible: {window.get('visible', False)}")
                print(f"  Active: {window.get('is_active', False)}")
                break
        
        # Step 4: Try different ways to open AI assistant
        print(f"\n🤖 Step 4: Open AI assistant")
        
        # First click on the window to ensure focus
        try:
            print("Clicking on window center...")
            result = await remote_controller.execute_command('click', {
                'x': 500,
                'y': 400
            })
            print(f"Click result: {result}")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Click failed: {e}")
        
        # Try multiple keyboard shortcuts
        shortcuts = [
            ('^l', 'Ctrl+L (common AI assistant)'),
            ('^+p', 'Ctrl+Shift+P (command palette)'),
            ('^j', 'Ctrl+J (panel toggle)'),
            ('^`', 'Ctrl+` (terminal toggle)'),
            ('VK_F1', 'F1 (help)'),
        ]
        
        for shortcut, description in shortcuts:
            try:
                print(f"Trying {description}...")
                result = await remote_controller.execute_command('send_keys', {
                    'keys': shortcut
                })
                print(f"  Result: {result}")
                await asyncio.sleep(2)  # Wait longer for UI to respond
                
                # Try to send a simple test message after each shortcut
                print(f"  Testing with simple message...")
                await remote_controller.execute_command('send_keys', {
                    'keys': 'test message for cleanup'
                })
                await asyncio.sleep(1)
                await remote_controller.execute_command('send_keys', {
                    'keys': '{ENTER}'
                })
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"  Failed: {e}")
        
        # Step 5: Try clipboard approach more carefully
        print(f"\n📋 Step 5: Careful clipboard approach")
        
        cleanup_message = "请清理backup/目录：删除7天前文件，保留3个最新备份，生成清理脚本"
        
        try:
            # Set clipboard
            print("Setting clipboard...")
            result = await remote_controller.execute_command('set_clipboard', {
                'text': cleanup_message
            })
            print(f"Clipboard set result: {result}")
            await asyncio.sleep(0.5)
            
            # Clear any existing content first
            print("Clearing existing content...")
            await remote_controller.execute_command('send_keys', {
                'keys': '^a'  # Select all
            })
            await asyncio.sleep(0.2)
            await remote_controller.execute_command('send_keys', {
                'keys': '{DELETE}'  # Delete
            })
            await asyncio.sleep(0.5)
            
            # Paste clipboard content
            print("Pasting from clipboard...")
            result = await remote_controller.execute_command('send_keys', {
                'keys': '^v'
            })
            print(f"Paste result: {result}")
            await asyncio.sleep(1)
            
            # Send message
            print("Sending message...")
            result = await remote_controller.execute_command('send_keys', {
                'keys': '{ENTER}'
            })
            print(f"Send result: {result}")
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"Clipboard approach failed: {e}")
        
        # Step 6: Check final state
        print(f"\n✅ Step 6: Check if message was sent")
        print("Please check Cursor IDE manually to see if any messages appeared.")
        print(f"Expected message: {cleanup_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    async def main():
        print("This will try multiple methods to interact with Cursor IDE")
        print("Please watch Cursor IDE window during the test...")
        
        print("Starting debug test in 2 seconds...")
        await asyncio.sleep(2)
        
        success = await debug_cursor_interaction()
        
        if success:
            print("\n🔍 Debug completed!")
            print("Check Cursor IDE to see if any interaction worked.")
            print("The message should be:")
            print("'请清理backup/目录：删除7天前文件，保留3个最新备份，生成清理脚本'")
        else:
            print("\n❌ Debug failed")
    
    asyncio.run(main())