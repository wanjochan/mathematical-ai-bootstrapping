"""Find the REAL Cursor window and input area"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController


async def find_real_cursor():
    """Find the real Cursor window by checking all windows"""
    
    print("🔍 查找真正的Cursor窗口")
    print("=" * 50)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("find_cursor")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            return
            
        print(f"✅ 已连接: {target_client}\n")
        
        # Get ALL windows
        windows = await remote_controller.get_windows()
        print(f"总共找到 {len(windows)} 个窗口\n")
        
        # Filter and categorize
        cursor_candidates = []
        vscode_windows = []
        other_windows = []
        
        for w in windows:
            title = w.get('title', '')
            hwnd = w.get('hwnd', 0)
            
            if not title:
                continue
                
            if 'cursor' in title.lower():
                cursor_candidates.append((title, hwnd))
            elif 'visual studio code' in title.lower() or 'vscode' in title.lower():
                vscode_windows.append((title, hwnd))
            elif any(x in title.lower() for x in ['chrome', 'edge', 'firefox']):
                continue  # Skip browsers
            else:
                other_windows.append((title, hwnd))
        
        # Show results
        print("🎯 Cursor候选窗口:")
        for title, hwnd in cursor_candidates:
            print(f"  - {title}")
            print(f"    HWND: {hwnd}")
            
            # Check if this is the real input window
            print(f"    检查子窗口...")
            try:
                children = await remote_controller.execute_command('enum_child_windows', {'hwnd': hwnd})
                if children and 'children' in children:
                    child_count = len(children['children'])
                    print(f"    子窗口数: {child_count}")
                    
                    # Look for edit controls
                    edit_count = 0
                    for child in children['children']:
                        class_name = child.get('class_name', '').lower()
                        if 'edit' in class_name or 'text' in class_name:
                            edit_count += 1
                            
                    if edit_count > 0:
                        print(f"    ⭐ 找到 {edit_count} 个编辑控件!")
            except:
                pass
            print()
        
        print("\n📝 VSCode窗口:")
        for title, hwnd in vscode_windows[:3]:
            print(f"  - {title} (HWND: {hwnd})")
        
        print("\n📄 其他相关窗口:")
        for title, hwnd in other_windows[:5]:
            if len(title) < 50:  # Skip very long titles
                print(f"  - {title} (HWND: {hwnd})")
        
        # Test the most likely Cursor window
        if cursor_candidates:
            print("\n" + "=" * 50)
            print("测试最可能的Cursor窗口...")
            
            test_hwnd = cursor_candidates[0][1]
            print(f"测试窗口: {cursor_candidates[0][0]}")
            print(f"HWND: {test_hwnd}")
            
            # Send a clear test message
            test_msg = "===这是测试消息==="
            
            print(f"\n发送测试消息: {test_msg}")
            
            # Activate
            await remote_controller.execute_command('win32_call', {
                'function': 'SetForegroundWindow',
                'args': [test_hwnd]
            })
            await asyncio.sleep(1)
            
            # Get window rect
            rect_info = await remote_controller.execute_command('win32_call', {
                'function': 'GetWindowRect',
                'args': [test_hwnd]
            })
            
            if rect_info and len(rect_info) == 4:
                left, top, right, bottom = rect_info
                width = right - left
                height = bottom - top
                
                # Calculate absolute positions
                positions = [
                    ("绝对右下", left + int(width * 0.75), top + int(height * 0.85)),
                    ("绝对右中", left + int(width * 0.75), top + int(height * 0.5)),
                    ("绝对中心", left + int(width * 0.5), top + int(height * 0.5))
                ]
                
                for desc, x, y in positions:
                    print(f"\n尝试{desc} ({x}, {y}):")
                    
                    # Click with absolute coordinates
                    await remote_controller.execute_command('click', {
                        'x': x,
                        'y': y,
                        'absolute': True
                    })
                    await asyncio.sleep(0.5)
                    
                    # Type test
                    await remote_controller.execute_command('send_keys', {'keys': test_msg})
                    await asyncio.sleep(0.5)
                    
                    print(f"  已发送，请检查Cursor")
                    
                    # Clear
                    await remote_controller.execute_command('send_keys', {'keys': '^a'})
                    await asyncio.sleep(0.1)
                    await remote_controller.execute_command('send_keys', {'keys': '{DELETE}'})
                    await asyncio.sleep(0.5)
            
        print("\n" + "=" * 50)
        print("💡 请告诉我:")
        print("1. 你看到测试消息了吗？")
        print("2. Cursor窗口的确切标题是什么？")
        print("3. 输入框在窗口的哪个位置？")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(find_real_cursor())