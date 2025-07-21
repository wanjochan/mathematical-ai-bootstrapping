"""Direct Win32 API interaction with Cursor"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController


async def cursor_win32_interaction():
    """Use Win32 API to interact with Cursor"""
    
    print("Cursor Win32 API 直接交互")
    print("=" * 50)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("win32_cursor")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            return False
        
        print(f"✅ 已连接: {target_client}")
        
        # The correct Cursor window
        cursor_hwnd = 7670670
        print(f"🎯 使用Cursor窗口 HWND: {cursor_hwnd}")
        
        # Step 1: Enumerate all child windows using Win32
        print("\n步骤1: 枚举所有子窗口")
        try:
            result = await remote_controller.execute_command('win32_call', {
                'function': 'EnumChildWindows',
                'args': [cursor_hwnd]
            })
            print(f"枚举结果: {result}")
        except Exception as e:
            print(f"枚举失败，尝试其他方法: {e}")
            
            # Alternative: Get child windows
            try:
                result = await remote_controller.execute_command('enum_child_windows', {
                    'hwnd': cursor_hwnd
                })
                if result and 'children' in result:
                    children = result['children']
                    print(f"找到 {len(children)} 个子窗口")
                    
                    # Find edit controls
                    edit_controls = []
                    for child in children:
                        class_name = child.get('class_name', '')
                        hwnd = child.get('hwnd')
                        print(f"  - {class_name} (HWND: {hwnd})")
                        
                        if 'edit' in class_name.lower() or 'text' in class_name.lower():
                            edit_controls.append(hwnd)
                    
                    if edit_controls:
                        print(f"\n找到 {len(edit_controls)} 个可能的输入控件")
                        
                        # Try each edit control
                        test_msg = "测试Win32消息：你好Cursor！"
                        
                        for edit_hwnd in edit_controls:
                            print(f"\n尝试控件 {edit_hwnd}:")
                            try:
                                # Clear text
                                await remote_controller.execute_command('win32_call', {
                                    'function': 'SendMessage',
                                    'args': [edit_hwnd, 0x000C, 0, ""]  # WM_SETTEXT
                                })
                                
                                # Set new text
                                result = await remote_controller.execute_command('win32_call', {
                                    'function': 'SendMessage',
                                    'args': [edit_hwnd, 0x000C, 0, test_msg]
                                })
                                print(f"  设置文本结果: {result}")
                                
                                # Read back
                                text = await remote_controller.execute_command('win32_call', {
                                    'function': 'GetWindowText',
                                    'args': [edit_hwnd]
                                })
                                print(f"  读回文本: {text}")
                                
                                if text and test_msg in str(text):
                                    print(f"  ✅ 成功设置文本！")
                                    
                                    # Send Enter key
                                    await remote_controller.execute_command('win32_call', {
                                        'function': 'SendMessage',
                                        'args': [edit_hwnd, 0x0100, 0x0D, 0]  # WM_KEYDOWN Enter
                                    })
                                    await remote_controller.execute_command('win32_call', {
                                        'function': 'SendMessage',
                                        'args': [edit_hwnd, 0x0101, 0x0D, 0]  # WM_KEYUP Enter
                                    })
                                    print(f"  ✅ 已发送Enter键")
                                    return True
                                    
                            except Exception as e:
                                print(f"  ❌ 失败: {e}")
                                
            except Exception as e:
                print(f"获取子窗口失败: {e}")
        
        # Step 2: Try PostMessage to main window
        print("\n步骤2: 尝试向主窗口发送消息")
        try:
            # Activate window first
            await remote_controller.execute_command('win32_call', {
                'function': 'SetForegroundWindow',
                'args': [cursor_hwnd]
            })
            await asyncio.sleep(0.5)
            
            # Send test message using WM_CHAR
            test_msg = "Hello Cursor from Win32!"
            for char in test_msg:
                await remote_controller.execute_command('win32_call', {
                    'function': 'PostMessage',
                    'args': [cursor_hwnd, 0x0102, ord(char), 0]  # WM_CHAR
                })
                await asyncio.sleep(0.01)
            
            print("✅ 字符消息已发送")
            
            # Send Enter
            await remote_controller.execute_command('win32_call', {
                'function': 'PostMessage',
                'args': [cursor_hwnd, 0x0100, 0x0D, 0]  # WM_KEYDOWN Enter
            })
            print("✅ Enter键已发送")
            
        except Exception as e:
            print(f"PostMessage失败: {e}")
        
        # Step 3: Find input area by position
        print("\n步骤3: 使用Win32获取指定位置的窗口")
        try:
            # Get window rect
            rect_result = await remote_controller.execute_command('win32_call', {
                'function': 'GetWindowRect',
                'args': [cursor_hwnd]
            })
            print(f"窗口位置: {rect_result}")
            
            # Use WindowFromPoint to find window at input position
            if rect_result and len(rect_result) == 4:
                # Calculate input position (bottom right)
                x = rect_result[0] + int((rect_result[2] - rect_result[0]) * 0.75)
                y = rect_result[1] + int((rect_result[3] - rect_result[1]) * 0.85)
                
                point_window = await remote_controller.execute_command('win32_call', {
                    'function': 'WindowFromPoint',
                    'args': [x, y]
                })
                print(f"位置 ({x}, {y}) 的窗口: {point_window}")
                
                if point_window and point_window != cursor_hwnd:
                    # Try to send text to this window
                    await remote_controller.execute_command('win32_call', {
                        'function': 'SendMessage',
                        'args': [point_window, 0x000C, 0, "Win32 position test"]
                    })
                    print("✅ 已向位置窗口发送文本")
                    
        except Exception as e:
            print(f"位置查找失败: {e}")
        
        print("\n" + "=" * 50)
        print("Win32测试完成，请检查Cursor是否收到消息")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(cursor_win32_interaction())