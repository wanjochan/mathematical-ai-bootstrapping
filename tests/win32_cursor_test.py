"""Use Win32 API for more reliable Cursor IDE interaction"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def win32_cursor_interaction():
    """Use Win32 API for reliable Cursor IDE interaction"""
    
    print("Win32 API Cursor IDE Interaction Test")
    print("=" * 40)
    
    try:
        # Connect to remote control
        remote_controller = RemoteController()
        await remote_controller.connect("win32_cursor")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("No target client found")
            return False
        
        print(f"Connected to client: {target_client}")
        
        # Get Cursor window
        windows = await remote_controller.get_windows()
        cursor_window = None
        for window in windows:
            if 'cursor' in window.get('title', '').lower():
                cursor_window = window
                break
        
        if not cursor_window:
            print("Cursor window not found")
            return False
        
        hwnd = cursor_window['hwnd']
        print(f"Found Cursor window: {cursor_window['title']} (HWND: {hwnd})")
        
        # Step 1: Force window to foreground using Win32 API
        print("\nStep 1: Activating window with Win32 API...")
        
        # Show and restore window
        try:
            result = await remote_controller.execute_command('win32_call', {
                'function': 'ShowWindow',
                'args': [hwnd, 9]  # SW_RESTORE
            })
            print(f"ShowWindow SW_RESTORE: {result}")
            
            result = await remote_controller.execute_command('win32_call', {
                'function': 'ShowWindow',
                'args': [hwnd, 5]  # SW_SHOW
            })
            print(f"ShowWindow SW_SHOW: {result}")
            
            # Set foreground
            result = await remote_controller.execute_command('win32_call', {
                'function': 'SetForegroundWindow',
                'args': [hwnd]
            })
            print(f"SetForegroundWindow: {result}")
            
            # Force focus
            result = await remote_controller.execute_command('win32_call', {
                'function': 'SetFocus',
                'args': [hwnd]
            })
            print(f"SetFocus: {result}")
            
        except Exception as e:
            print(f"Window activation failed: {e}")
        
        await asyncio.sleep(2)
        
        # Step 2: Find child windows (input boxes, buttons)
        print("\nStep 2: Finding child windows...")
        
        try:
            # Enumerate child windows to find input controls
            result = await remote_controller.execute_command('enum_child_windows', {
                'hwnd': hwnd
            })
            print(f"Child windows found: {len(result.get('children', []))}")
            
            # Look for edit controls (input boxes)
            edit_controls = []
            for child in result.get('children', []):
                class_name = child.get('class_name', '')
                if 'edit' in class_name.lower() or 'input' in class_name.lower():
                    edit_controls.append(child)
                    print(f"Found edit control: {class_name} (HWND: {child['hwnd']})")
            
        except Exception as e:
            print(f"Child window enumeration failed: {e}")
            edit_controls = []
        
        # Step 3: Direct Win32 text input
        print("\nStep 3: Direct Win32 text input...")
        
        cleanup_message = """请帮我清理backup/目录，要求：
1. 删除7天前的备份文件
2. 保留最新3个备份
3. 清理临时文件
4. 生成清理脚本"""
        
        print(f"Message to send: {cleanup_message[:50]}...")
        
        # Method A: Try SendMessage to edit controls
        if edit_controls:
            print("Trying SendMessage to edit controls...")
            for edit_ctrl in edit_controls[:2]:  # Try first 2 edit controls
                try:
                    edit_hwnd = edit_ctrl['hwnd']
                    print(f"Sending to edit control {edit_hwnd}...")
                    
                    # Clear existing text
                    result = await remote_controller.execute_command('win32_call', {
                        'function': 'SendMessage',
                        'args': [edit_hwnd, 0x000C, 0, ""]  # WM_SETTEXT
                    })
                    print(f"Clear text result: {result}")
                    
                    # Set new text
                    result = await remote_controller.execute_command('win32_call', {
                        'function': 'SendMessage',
                        'args': [edit_hwnd, 0x000C, 0, cleanup_message]  # WM_SETTEXT
                    })
                    print(f"Set text result: {result}")
                    
                    # Simulate Enter key
                    result = await remote_controller.execute_command('win32_call', {
                        'function': 'SendMessage',
                        'args': [edit_hwnd, 0x0100, 0x0D, 0]  # WM_KEYDOWN, VK_RETURN
                    })
                    print(f"Send Enter result: {result}")
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"SendMessage to edit control failed: {e}")
        
        # Method B: Try PostMessage to main window
        print("\nTrying PostMessage to main window...")
        try:
            # Focus on main window first
            result = await remote_controller.execute_command('win32_call', {
                'function': 'SetFocus',
                'args': [hwnd]
            })
            
            # Send character by character using PostMessage
            for char in cleanup_message[:20]:  # Send first 20 chars as test
                char_code = ord(char)
                result = await remote_controller.execute_command('win32_call', {
                    'function': 'PostMessage',
                    'args': [hwnd, 0x0102, char_code, 0]  # WM_CHAR
                })
                await asyncio.sleep(0.05)  # Small delay between characters
            
            # Send Enter
            result = await remote_controller.execute_command('win32_call', {
                'function': 'PostMessage',
                'args': [hwnd, 0x0100, 0x0D, 0]  # WM_KEYDOWN, VK_RETURN
            })
            print("PostMessage text sending completed")
            
        except Exception as e:
            print(f"PostMessage failed: {e}")
        
        # Method C: Advanced - Use SetWindowText on potential input controls
        print("\nTrying SetWindowText method...")
        try:
            # Get all child windows and try SetWindowText
            result = await remote_controller.execute_command('win32_call', {
                'function': 'EnumChildWindows',
                'args': [hwnd]
            })
            
            if result and 'children' in result:
                for child_hwnd in result['children'][:5]:  # Try first 5 children
                    try:
                        result = await remote_controller.execute_command('win32_call', {
                            'function': 'SetWindowText',
                            'args': [child_hwnd, cleanup_message]
                        })
                        print(f"SetWindowText to {child_hwnd}: {result}")
                    except:
                        pass
                        
        except Exception as e:
            print(f"SetWindowText method failed: {e}")
        
        print("\nWin32 API interaction completed!")
        print("Please check Cursor IDE to see if the message was received.")
        print("This demonstrates the improved system using direct Win32 calls.")
        
        return True
        
    except Exception as e:
        print(f"Win32 interaction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    async def main():
        print("Using Win32 API for more reliable Cursor IDE interaction")
        print("This approach is more stable than keyboard shortcuts")
        
        await asyncio.sleep(2)
        
        success = await win32_cursor_interaction()
        
        if success:
            print("\nWin32 API interaction completed!")
            print("This demonstrates how the improved system can use")
            print("direct Win32 calls for more reliable text input.")
        else:
            print("\nWin32 API interaction failed")
    
    asyncio.run(main())