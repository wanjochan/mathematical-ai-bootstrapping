"""Verify actual Cursor state and capture screenshot"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController


async def verify_cursor_state():
    """Capture and verify actual Cursor state"""
    
    print("验证Cursor实际状态")
    print("=" * 50)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("verify_state")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ 未找到客户端")
            return
            
        print(f"✅ 已连接: {target_client}")
        
        # Find all windows again
        print("\n1. 重新查找所有窗口：")
        windows = await remote_controller.get_windows()
        
        cursor_windows = []
        for window in windows:
            title = window.get('title', '')
            if 'cursor' in title.lower():
                cursor_windows.append(window)
                print(f"   找到: {title} (HWND: {window['hwnd']})")
        
        if not cursor_windows:
            print("   ❌ 未找到Cursor窗口")
            return
            
        # Use the first Cursor window
        cursor_window = cursor_windows[0]
        hwnd = cursor_window['hwnd']
        
        # Step 2: Capture screenshot
        print(f"\n2. 截图窗口 HWND {hwnd}:")
        try:
            # Method 1: Direct capture
            result = await remote_controller.execute_command('capture_window', {
                'hwnd': hwnd,
                'save_to': f'cursor_state_{hwnd}.png'
            })
            if result and result.get('success'):
                print(f"   ✅ 截图成功: {result.get('path', 'saved')}")
            else:
                print(f"   ❌ 截图失败: {result}")
                
            # Method 2: Alternative capture
            alt_result = await remote_controller.execute_command('screenshot', {
                'window_hwnd': hwnd
            })
            if alt_result:
                print(f"   ✅ 备用截图成功")
                
        except Exception as e:
            print(f"   截图错误: {e}")
        
        # Step 3: Get window details
        print(f"\n3. 窗口详细信息:")
        try:
            info = await remote_controller.execute_command('get_window_info', {'hwnd': hwnd})
            if info:
                print(f"   位置: {info.get('rect', '未知')}")
                print(f"   类名: {info.get('class_name', '未知')}")
                print(f"   状态: {info.get('state', '未知')}")
        except:
            pass
        
        # Step 4: Try to read any text from window
        print(f"\n4. 尝试读取窗口文本:")
        try:
            # Get all child windows
            children = await remote_controller.execute_command('enum_child_windows', {'hwnd': hwnd})
            if children and 'children' in children:
                print(f"   找到 {len(children['children'])} 个子窗口")
                
                # Try to get text from each
                text_found = []
                for child in children['children'][:10]:  # Check first 10
                    try:
                        text = await remote_controller.execute_command('win32_call', {
                            'function': 'GetWindowText',
                            'args': [child['hwnd']]
                        })
                        if text and len(str(text)) > 0:
                            text_found.append(f"{child['class_name']}: {text[:50]}")
                    except:
                        pass
                
                if text_found:
                    print("   找到的文本:")
                    for t in text_found:
                        print(f"     - {t}")
                else:
                    print("   ❌ 未找到任何文本")
                    
        except Exception as e:
            print(f"   读取文本错误: {e}")
        
        # Step 5: Test actual typing
        print(f"\n5. 测试实际输入:")
        print("   我将输入一条明显的测试消息...")
        
        # Activate window
        await remote_controller.execute_command('win32_call', {
            'function': 'SetForegroundWindow',
            'args': [hwnd]
        })
        await asyncio.sleep(1)
        
        # Get window size
        try:
            rect = info.get('rect', [0, 0, 1200, 800])
            if len(rect) == 4:
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
            else:
                width = 1200
                height = 800
        except:
            width = 1200
            height = 800
        
        # Try multiple positions
        test_positions = [
            ("右下", int(width * 0.75), int(height * 0.85)),
            ("右中", int(width * 0.75), int(height * 0.5)),
            ("中下", int(width * 0.5), int(height * 0.85)),
            ("右上", int(width * 0.75), int(height * 0.2))
        ]
        
        test_message = "【测试】这是验证消息，时间:" + str(asyncio.get_event_loop().time())[:5]
        
        for desc, x, y in test_positions:
            print(f"\n   尝试{desc}位置 ({x}, {y}):")
            
            # Click
            await remote_controller.execute_command('click', {'x': x, 'y': y})
            await asyncio.sleep(0.5)
            
            # Type
            await remote_controller.execute_command('send_keys', {'keys': test_message})
            await asyncio.sleep(0.5)
            
            # Take screenshot
            try:
                result = await remote_controller.execute_command('capture_window', {
                    'hwnd': hwnd,
                    'save_to': f'cursor_test_{desc}.png'
                })
                print(f"     截图保存: cursor_test_{desc}.png")
            except:
                pass
            
            # Clear
            await remote_controller.execute_command('send_keys', {'keys': '^a'})
            await asyncio.sleep(0.1)
            await remote_controller.execute_command('send_keys', {'keys': '{DELETE}'})
            await asyncio.sleep(0.3)
        
        print(f"\n" + "=" * 50)
        print("验证完成！")
        print("1. 请检查生成的截图文件")
        print("2. 告诉我你在Cursor中看到了什么")
        print("3. 是否看到了测试消息？")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(verify_cursor_state())