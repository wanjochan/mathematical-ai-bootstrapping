"""Send a single clear message to Cursor to verify"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController


async def send_single_message():
    """Send one clear message to verify it works"""
    
    print("发送单条消息到Cursor IDE")
    print("=" * 40)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("single_msg")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ 未找到客户端")
            return False
        
        print(f"✅ 已连接: {target_client}")
        
        # Find Cursor
        windows = await remote_controller.get_windows()
        cursor_window = None
        for window in windows:
            if 'cursor' in window.get('title', '').lower():
                cursor_window = window
                break
        
        if not cursor_window:
            print("❌ 未找到Cursor")
            return False
        
        hwnd = cursor_window['hwnd']
        print(f"✅ Cursor窗口: {hwnd}")
        
        # Get dimensions
        window_info = await remote_controller.execute_command('get_window_info', {'hwnd': hwnd})
        if window_info and 'rect' in window_info:
            rect = window_info['rect']
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
        else:
            width = 1200
            height = 800
        
        # Message to send
        message = "你好Cursor！这是一条测试消息。请帮我分析一下Python中装饰器的工作原理。"
        
        print(f"\n📝 消息内容: {message}")
        
        # Position - bottom right for active chat
        x = int(width * 0.75)
        y = int(height * 0.85)
        
        print(f"📍 点击位置: ({x}, {y})")
        
        # Activate window
        await remote_controller.execute_command('win32_call', {
            'function': 'SetForegroundWindow',
            'args': [hwnd]
        })
        await asyncio.sleep(1)
        
        # Click
        print("🖱️ 点击输入区域...")
        await remote_controller.execute_command('click', {'x': x, 'y': y})
        await asyncio.sleep(0.5)
        
        # Clear
        print("🧹 清空输入框...")
        await remote_controller.execute_command('send_keys', {'keys': '^a'})
        await asyncio.sleep(0.2)
        await remote_controller.execute_command('send_keys', {'keys': '{DELETE}'})
        await asyncio.sleep(0.3)
        
        # Type
        print("⌨️ 输入消息...")
        await remote_controller.execute_command('send_keys', {'keys': message})
        await asyncio.sleep(1)
        
        # Send
        print("📤 按Enter发送...")
        await remote_controller.execute_command('send_keys', {'keys': '{ENTER}'})
        
        print("\n✅ 消息发送步骤完成")
        print("请检查Cursor IDE是否收到消息")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(send_single_message())