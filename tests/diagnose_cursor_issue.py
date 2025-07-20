"""Diagnose why messages aren't reaching Cursor IDE"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def diagnose_cursor_issue():
    """Comprehensive diagnosis of Cursor IDE interaction issues"""
    
    print("CURSOR IDE INTERACTION DIAGNOSIS")
    print("=" * 40)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("diagnostics")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ No target client found")
            return
        
        print(f"✅ Connected to client: {target_client}")
        
        # Get Cursor window info
        windows = await remote_controller.get_windows()
        cursor_window = None
        for window in windows:
            if 'cursor' in window.get('title', '').lower():
                cursor_window = window
                break
        
        if not cursor_window:
            print("❌ Cursor window not found")
            return
        
        hwnd = cursor_window['hwnd']
        print(f"✅ Cursor window found: {cursor_window['title']}")
        print(f"   HWND: {hwnd}")
        print(f"   Visible: {cursor_window.get('visible', 'unknown')}")
        print(f"   Active: {cursor_window.get('is_active', 'unknown')}")
        
        # Step 1: Window state diagnosis
        print(f"\n🔍 Step 1: Window State Diagnosis")
        try:
            # Get detailed window info
            result = await remote_controller.execute_command('get_window_info', {'hwnd': hwnd})
            if result:
                print(f"   Window rect: {result.get('rect', 'unknown')}")
                print(f"   Window style: {result.get('style', 'unknown')}")
                print(f"   Window class: {result.get('class_name', 'unknown')}")
            
            # Try to get window text
            result = await remote_controller.execute_command('win32_call', {
                'function': 'GetWindowText',
                'args': [hwnd]
            })
            print(f"   Window text: {result}")
            
        except Exception as e:
            print(f"   Window info error: {e}")
        
        # Step 2: Window activation diagnosis
        print(f"\n🪟 Step 2: Window Activation Diagnosis")
        
        activation_methods = [
            ('ShowWindow SW_RESTORE', 'ShowWindow', [hwnd, 9]),
            ('ShowWindow SW_SHOW', 'ShowWindow', [hwnd, 5]), 
            ('ShowWindow SW_MAXIMIZE', 'ShowWindow', [hwnd, 3]),
            ('SetForegroundWindow', 'SetForegroundWindow', [hwnd]),
            ('BringWindowToTop', 'BringWindowToTop', [hwnd]),
            ('SetActiveWindow', 'SetActiveWindow', [hwnd]),
        ]
        
        for name, func, args in activation_methods:
            try:
                result = await remote_controller.execute_command('win32_call', {
                    'function': func,
                    'args': args
                })
                print(f"   {name}: {result}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"   {name}: Failed - {e}")
        
        # Check if window became visible
        await asyncio.sleep(2)
        windows_after = await remote_controller.get_windows()
        cursor_after = None
        for window in windows_after:
            if window['hwnd'] == hwnd:
                cursor_after = window
                break
        
        if cursor_after:
            print(f"   After activation - Visible: {cursor_after.get('visible', 'unknown')}")
            print(f"   After activation - Active: {cursor_after.get('is_active', 'unknown')}")
        
        # Step 3: Child window analysis
        print(f"\n🔍 Step 3: Child Window Analysis")
        try:
            result = await remote_controller.execute_command('enum_child_windows', {'hwnd': hwnd})
            if result and 'children' in result:
                children = result['children']
                print(f"   Found {len(children)} child windows:")
                
                for i, child in enumerate(children[:10]):  # Show first 10
                    class_name = child.get('class_name', 'unknown')
                    child_hwnd = child.get('hwnd', 0)
                    print(f"     {i+1}. {class_name} (HWND: {child_hwnd})")
                
                # Test sending to edit controls
                edit_controls = [c for c in children if 'edit' in c.get('class_name', '').lower()]
                if edit_controls:
                    print(f"   Found {len(edit_controls)} edit controls, testing...")
                    for edit_ctrl in edit_controls[:3]:
                        edit_hwnd = edit_ctrl['hwnd']
                        try:
                            # Test setting text
                            await remote_controller.execute_command('win32_call', {
                                'function': 'SendMessage',
                                'args': [edit_hwnd, 0x000C, 0, "Test message from diagnostics"]
                            })
                            
                            # Verify
                            verify = await remote_controller.execute_command('win32_call', {
                                'function': 'GetWindowText',
                                'args': [edit_hwnd]
                            })
                            print(f"     Edit control {edit_hwnd}: {verify}")
                        except Exception as e:
                            print(f"     Edit control {edit_hwnd}: Failed - {e}")
            else:
                print("   No child windows found or enumeration failed")
                
        except Exception as e:
            print(f"   Child enumeration error: {e}")
        
        # Step 4: Alternative interaction methods
        print(f"\n⌨️ Step 4: Alternative Interaction Methods")
        
        # Method 1: Focus + keyboard input
        print("   Testing focus + keyboard input...")
        try:
            # Set focus to main window
            await remote_controller.execute_command('win32_call', {
                'function': 'SetFocus',
                'args': [hwnd]
            })
            
            # Send a simple test message using SendInput
            test_msg = "Test from diagnostics"
            for char in test_msg:
                await remote_controller.execute_command('win32_call', {
                    'function': 'keybd_event',
                    'args': [ord(char.upper()), 0, 0, 0]  # Key down
                })
                await remote_controller.execute_command('win32_call', {
                    'function': 'keybd_event',
                    'args': [ord(char.upper()), 0, 2, 0]  # Key up
                })
                await asyncio.sleep(0.01)
            
            print("   Keyboard input method completed")
            
        except Exception as e:
            print(f"   Keyboard input failed: {e}")
        
        # Method 2: Clipboard + paste
        print("   Testing clipboard + paste method...")
        try:
            # Set clipboard
            await remote_controller.execute_command('set_clipboard', {
                'text': "Diagnostic message via clipboard"
            })
            
            # Send Ctrl+V
            await remote_controller.execute_command('win32_call', {
                'function': 'keybd_event',
                'args': [0x11, 0, 0, 0]  # Ctrl down
            })
            await remote_controller.execute_command('win32_call', {
                'function': 'keybd_event',
                'args': [0x56, 0, 0, 0]  # V down
            })
            await remote_controller.execute_command('win32_call', {
                'function': 'keybd_event',
                'args': [0x56, 0, 2, 0]  # V up
            })
            await remote_controller.execute_command('win32_call', {
                'function': 'keybd_event',
                'args': [0x11, 0, 2, 0]  # Ctrl up
            })
            
            print("   Clipboard paste method completed")
            
        except Exception as e:
            print(f"   Clipboard paste failed: {e}")
        
        # Summary and recommendations
        print(f"\n📋 DIAGNOSIS SUMMARY")
        print("   Please check Cursor IDE now to see if any of the test messages appeared.")
        print("   Look for:")
        print("   - 'Test message from diagnostics' (from Win32 direct)")
        print("   - 'Test from diagnostics' (from keyboard input)")
        print("   - 'Diagnostic message via clipboard' (from clipboard)")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print("   1. If no messages appeared: Cursor may be using a non-standard UI framework")
        print("   2. If messages appeared in wrong place: Need better UI element detection")
        print("   3. If some methods worked: Use the working method as primary")
        print("   4. Consider using UI Automation (UIA) as alternative approach")
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    async def main():
        print("Running comprehensive Cursor IDE interaction diagnosis...")
        print("This will help identify why messages aren't reaching the dialog.")
        
        await asyncio.sleep(1)
        
        success = await diagnose_cursor_issue()
        
        if success:
            print("\n" + "=" * 50)
            print("DIAGNOSIS COMPLETED")
            print("Please manually check Cursor IDE for any test messages")
            print("and let me know what you observe!")
            print("=" * 50)
    
    asyncio.run(main())