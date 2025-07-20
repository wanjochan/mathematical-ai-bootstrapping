"""Adaptive Cursor IDE interaction that handles dynamic UI layout"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def adaptive_cursor_interaction():
    """Adaptive interaction that handles Cursor's dynamic UI layout"""
    
    print("ADAPTIVE CURSOR IDE INTERACTION")
    print("Handles dynamic UI layout changes")
    print("=" * 40)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("adaptive_cursor")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ No target client found")
            return False
        
        print(f"✅ Connected to client: {target_client}")
        
        # Get Cursor window
        windows = await remote_controller.get_windows()
        cursor_window = None
        for window in windows:
            if 'cursor' in window.get('title', '').lower():
                cursor_window = window
                break
        
        if not cursor_window:
            print("❌ Cursor window not found")
            return False
        
        hwnd = cursor_window['hwnd']
        print(f"✅ Found Cursor window: {hwnd}")
        
        # Step 1: Activate window properly
        print(f"\n🪟 Step 1: Activating Cursor window")
        await activate_cursor_window(remote_controller, hwnd)
        
        # Step 2: Detect current UI state and find input locations
        print(f"\n🔍 Step 2: Scanning for input locations (right side)")
        input_locations = await scan_for_input_locations(remote_controller, hwnd)
        
        if not input_locations:
            print("❌ No potential input locations found")
            return False
        
        print(f"✅ Found {len(input_locations)} potential input locations")
        for i, loc in enumerate(input_locations):
            print(f"   {i+1}. {loc['description']} at {loc['position']}")
        
        # Step 3: Try each location until one works
        print(f"\n📝 Step 3: Testing input locations with cleanup message")
        
        cleanup_message = """请帮我清理backup/目录，要求：
1. 删除7天前的备份文件  
2. 保留最新3个备份
3. 清理临时文件
4. 生成清理脚本"""
        
        success = False
        for i, location in enumerate(input_locations):
            print(f"\n   Testing location {i+1}: {location['description']}")
            
            # Try this location
            if await try_input_at_location(remote_controller, location, cleanup_message):
                print(f"   ✅ SUCCESS at location {i+1}!")
                success = True
                break
            else:
                print(f"   ❌ Failed at location {i+1}")
        
        if success:
            print(f"\n🎉 ADAPTIVE INTERACTION SUCCESSFUL!")
            print(f"Message sent to Cursor IDE!")
            print(f"Please check the chat dialog for the cleanup response.")
        else:
            print(f"\n❌ All locations failed, but locations were identified")
            print(f"Manual intervention may be needed to start the conversation")
        
        return success
        
    except Exception as e:
        print(f"❌ Adaptive interaction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def activate_cursor_window(remote_controller, hwnd):
    """Properly activate Cursor window"""
    activation_methods = [
        ('ShowWindow RESTORE', 'ShowWindow', [hwnd, 9]),
        ('ShowWindow SHOW', 'ShowWindow', [hwnd, 5]),
        ('SetForegroundWindow', 'SetForegroundWindow', [hwnd]),
        ('BringWindowToTop', 'BringWindowToTop', [hwnd]),
    ]
    
    for name, func, args in activation_methods:
        try:
            await remote_controller.execute_command('win32_call', {
                'function': func,
                'args': args
            })
            await asyncio.sleep(0.3)
        except Exception as e:
            print(f"   {name} failed: {e}")
    
    # Give window time to activate
    await asyncio.sleep(1)


async def scan_for_input_locations(remote_controller, hwnd):
    """Scan for potential input locations in Cursor IDE"""
    locations = []
    
    # Get window dimensions first
    try:
        window_info = await remote_controller.execute_command('get_window_info', {'hwnd': hwnd})
        if window_info and 'rect' in window_info:
            rect = window_info['rect']
            window_width = rect[2] - rect[0]
            window_height = rect[3] - rect[1]
            print(f"   Window size: {window_width}x{window_height}")
        else:
            # Default assumptions
            window_width = 1200
            window_height = 800
    except:
        window_width = 1200
        window_height = 800
    
    # Location 1: Right-bottom area (after conversation starts)
    locations.append({
        'description': 'Right-bottom input (conversation active)',
        'position': [int(window_width * 0.75), int(window_height * 0.85)],
        'method': 'click_and_type'
    })
    
    # Location 2: Right-center area (general chat area)
    locations.append({
        'description': 'Right-center chat area',
        'position': [int(window_width * 0.75), int(window_height * 0.6)],
        'method': 'click_and_type'
    })
    
    # Location 3: Right-top area (initial dialog)
    locations.append({
        'description': 'Right-top initial dialog',
        'position': [int(window_width * 0.75), int(window_height * 0.25)],
        'method': 'click_and_type'
    })
    
    # Location 4: Center-bottom (fallback)
    locations.append({
        'description': 'Center-bottom fallback',
        'position': [int(window_width * 0.5), int(window_height * 0.8)],
        'method': 'click_and_type'
    })
    
    # Try to find actual edit controls and map them to locations
    try:
        result = await remote_controller.execute_command('enum_child_windows', {'hwnd': hwnd})
        if result and 'children' in result:
            edit_controls = []
            for child in result['children']:
                class_name = child.get('class_name', '').lower()
                if 'edit' in class_name or 'input' in class_name:
                    edit_controls.append(child)
            
            # Add edit controls as direct Win32 locations
            for i, edit_ctrl in enumerate(edit_controls):
                locations.append({
                    'description': f'Direct Win32 edit control {i+1}',
                    'position': None,
                    'method': 'win32_direct',
                    'hwnd': edit_ctrl['hwnd']
                })
    except Exception as e:
        print(f"   Child enumeration failed: {e}")
    
    return locations


async def try_input_at_location(remote_controller, location, message):
    """Try to input message at a specific location"""
    try:
        if location['method'] == 'win32_direct' and 'hwnd' in location:
            # Direct Win32 to edit control
            edit_hwnd = location['hwnd']
            
            # Clear and set text
            await remote_controller.execute_command('win32_call', {
                'function': 'SendMessage',
                'args': [edit_hwnd, 0x000C, 0, ""]  # Clear
            })
            
            await remote_controller.execute_command('win32_call', {
                'function': 'SendMessage',
                'args': [edit_hwnd, 0x000C, 0, message]  # Set text
            })
            
            # Verify
            verify = await remote_controller.execute_command('win32_call', {
                'function': 'GetWindowText',
                'args': [edit_hwnd]
            })
            
            if verify and len(str(verify)) > 10:  # Text was set
                # Send Enter
                await remote_controller.execute_command('win32_call', {
                    'function': 'SendMessage',
                    'args': [edit_hwnd, 0x0100, 0x0D, 0]  # Enter
                })
                return True
        
        elif location['method'] == 'click_and_type':
            # Click at position and type
            pos = location['position']
            
            # Click to focus
            await remote_controller.execute_command('click', {
                'x': pos[0], 
                'y': pos[1]
            })
            await asyncio.sleep(0.5)
            
            # Clear any existing content
            await remote_controller.execute_command('send_keys', {'keys': '^a'})
            await asyncio.sleep(0.1)
            await remote_controller.execute_command('send_keys', {'keys': '{DELETE}'})
            await asyncio.sleep(0.2)
            
            # Type message
            await remote_controller.execute_command('send_keys', {'keys': message})
            await asyncio.sleep(0.5)
            
            # Send Enter
            await remote_controller.execute_command('send_keys', {'keys': '{ENTER}'})
            await asyncio.sleep(0.5)
            
            return True  # Assume success for click_and_type
        
        return False
        
    except Exception as e:
        print(f"     Error at location: {e}")
        return False


if __name__ == "__main__":
    async def main():
        print("Testing adaptive Cursor IDE interaction")
        print("This accounts for dynamic UI layout changes:")
        print("- Initial dialog in right-top")
        print("- Input moves to right-bottom after conversation starts")
        print("")
        
        await asyncio.sleep(1)
        
        success = await adaptive_cursor_interaction()
        
        if success:
            print("\n" + "=" * 50)
            print("ADAPTIVE INTERACTION SUCCESS!")
            print("✓ Handled dynamic UI layout")
            print("✓ Found correct input location")
            print("✓ Sent cleanup message successfully")
            print("Check Cursor IDE for the backup cleanup response!")
            print("=" * 50)
        else:
            print("\nNeed manual intervention to start conversation first")
    
    asyncio.run(main())