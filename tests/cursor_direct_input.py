"""Direct mouse and keyboard input to Cursor at specific coordinates"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController


async def direct_cursor_input():
    """Direct input to Cursor using simple mouse/keyboard events"""
    
    print("直接向Cursor发送鼠标键盘事件")
    print("=" * 50)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("direct_input")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            return
            
        print(f"✅ 已连接: {target_client}")
        
        # Cursor window
        cursor_hwnd = 7670670
        print(f"🎯 Cursor窗口: {cursor_hwnd}")
        
        # Get window position and size
        rect = await remote_controller.execute_command('win32_call', {
            'function': 'GetWindowRect',
            'args': [cursor_hwnd]
        })
        
        if rect and len(rect) == 4:
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top
            print(f"窗口位置: ({left}, {top})")
            print(f"窗口大小: {width}x{height}")
        else:
            # Default if can't get rect
            left, top = 100, 100
            width, height = 1200, 800
            print("使用默认窗口参数")
        
        # Activate window first
        print("\n1. 激活窗口")
        await remote_controller.execute_command('win32_call', {
            'function': 'SetForegroundWindow',
            'args': [cursor_hwnd]
        })
        await asyncio.sleep(0.5)
        
        # Calculate input position (right side, bottom area - typical for chat)
        input_x = left + int(width * 0.75)  # 75% from left
        input_y = top + int(height * 0.85)  # 85% from top
        
        print(f"\n2. 输入位置: ({input_x}, {input_y})")
        
        # Messages to send
        messages = [
            "你好Cursor！这是第一条测试消息。",
            "关于AGI，你认为最大的技术挑战是什么？",
            "Transformer架构的局限性在哪里？",
            "多模态学习对AGI有多重要？",
            "如何解决AI的常识推理问题？"
        ]
        
        print(f"\n3. 发送{len(messages)}条消息：")
        
        for i, msg in enumerate(messages):
            print(f"\n消息{i+1}: {msg[:30]}...")
            
            # Mouse click at input position
            print(f"  - 点击 ({input_x}, {input_y})")
            await remote_controller.execute_command('mouse_click', {
                'x': input_x,
                'y': input_y,
                'button': 'left'
            })
            await asyncio.sleep(0.5)
            
            # Clear any existing text
            print("  - 清空输入框")
            await remote_controller.execute_command('key_combo', {'keys': ['ctrl', 'a']})
            await asyncio.sleep(0.2)
            await remote_controller.execute_command('key_press', {'key': 'delete'})
            await asyncio.sleep(0.2)
            
            # Type message
            print("  - 输入文字")
            await remote_controller.execute_command('type_text', {'text': msg})
            await asyncio.sleep(0.5)
            
            # Press Enter to send
            print("  - 按Enter发送")
            await remote_controller.execute_command('key_press', {'key': 'return'})
            
            print("  ✅ 已发送")
            
            # Wait for response
            await asyncio.sleep(5)
        
        print("\n" + "=" * 50)
        print("✅ 完成！已发送5条消息")
        print("请检查Cursor中的对话")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(direct_cursor_input())