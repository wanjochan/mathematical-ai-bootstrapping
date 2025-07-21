"""Simple click and type for Cursor"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController


async def simple_cursor_interaction():
    """Most basic interaction - just click and type"""
    
    print("最简单的Cursor交互")
    print("=" * 50)
    
    try:
        # Connect
        controller = RemoteController()
        await controller.connect("simple_test")
        
        target = await controller.find_client("wjc2022")
        if not target:
            return
            
        print(f"✅ 已连接: {target}")
        
        # 1. First activate Cursor window
        print("\n1. 激活Cursor窗口 (HWND: 7670670)")
        await controller.execute_command('win32_call', {
            'function': 'SetForegroundWindow',
            'args': [7670670]
        })
        await asyncio.sleep(1)
        
        # 2. Simple absolute position click (assuming 1920x1080 screen)
        # Right side bottom area where chat input usually is
        positions_to_try = [
            (1400, 900, "右下角"),
            (1400, 600, "右中部"),
            (960, 900, "中下部"),
            (1400, 300, "右上部")
        ]
        
        test_message = "测试消息：你好Cursor！"
        
        for x, y, desc in positions_to_try:
            print(f"\n尝试位置: {desc} ({x}, {y})")
            
            # Simple click
            print(f"  点击...")
            await controller.execute_command('click', {'x': x, 'y': y})
            await asyncio.sleep(0.5)
            
            # Select all and delete
            print(f"  清空...")
            await controller.execute_command('send_keys', {'keys': '^a'})
            await asyncio.sleep(0.2)
            await controller.execute_command('send_keys', {'keys': '{DELETE}'})
            await asyncio.sleep(0.2)
            
            # Type message
            print(f"  输入: {test_message}")
            await controller.execute_command('send_keys', {'keys': test_message})
            await asyncio.sleep(0.5)
            
            # Don't send yet - let user verify
            print(f"  ✅ 已输入文字，请检查是否出现在Cursor中")
            
            # Wait before trying next position
            await asyncio.sleep(2)
            
            # Clear for next test
            await controller.execute_command('send_keys', {'keys': '^a'})
            await asyncio.sleep(0.1)
            await controller.execute_command('send_keys', {'keys': '{DELETE}'})
            await asyncio.sleep(0.5)
        
        # Now try to send one message
        print("\n" + "=" * 50)
        print("现在发送一条完整消息...")
        
        # Use the most likely position (right bottom)
        x, y = 1400, 900
        message = "你好Cursor！请问AGI最大的技术挑战是什么？"
        
        # Click
        await controller.execute_command('click', {'x': x, 'y': y})
        await asyncio.sleep(0.5)
        
        # Clear
        await controller.execute_command('send_keys', {'keys': '^a'})
        await asyncio.sleep(0.2)
        await controller.execute_command('send_keys', {'keys': '{DELETE}'})
        await asyncio.sleep(0.2)
        
        # Type
        await controller.execute_command('send_keys', {'keys': message})
        await asyncio.sleep(0.5)
        
        # Send
        print("按Enter发送...")
        await controller.execute_command('send_keys', {'keys': '{ENTER}'})
        
        print("\n✅ 完成！")
        print("请告诉我：")
        print("1. 你看到测试文字了吗？")
        print("2. 最后的消息发送成功了吗？")
        print("3. 输入框实际在屏幕的什么位置？")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(simple_cursor_interaction())