"""Get real Cursor window position and interact"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController


async def get_cursor_real_position():
    """Get Cursor's real position and send messages"""
    
    print("获取Cursor真实位置并交互")
    print("=" * 50)
    
    try:
        # Connect
        controller = RemoteController()
        await controller.connect("real_position")
        
        target = await controller.find_client("wjc2022")
        if not target:
            return
            
        print(f"✅ 已连接: {target}")
        
        # Get all windows with positions
        print("\n1. 获取所有窗口位置信息...")
        windows = await controller.get_windows()
        
        cursor_window = None
        for w in windows:
            if 'cursor' in w.get('title', '').lower():
                cursor_window = w
                break
        
        if not cursor_window:
            print("❌ 未找到Cursor窗口")
            return
            
        hwnd = cursor_window['hwnd']
        print(f"\n✅ 找到Cursor窗口")
        print(f"   标题: {cursor_window['title']}")
        print(f"   HWND: {hwnd}")
        
        # Method 1: Direct window rect
        print("\n2. 获取窗口矩形...")
        
        # Try different methods to get window position
        rect = None
        
        # Method A: GetWindowRect
        try:
            rect_result = await controller.execute_command('win32_call', {
                'function': 'GetWindowRect',
                'args': [hwnd]
            })
            if rect_result and len(rect_result) == 4:
                rect = rect_result
                print(f"   GetWindowRect: {rect}")
        except:
            pass
        
        # Method B: Get from window info
        if not rect:
            try:
                info = await controller.execute_command('get_window_info', {'hwnd': hwnd})
                if info and 'rect' in info:
                    rect = info['rect']
                    print(f"   WindowInfo: {rect}")
            except:
                pass
        
        # Method C: Use screen size
        if not rect:
            print("   使用屏幕默认值")
            # Assume standard screen
            rect = [100, 100, 1500, 900]
        
        # Calculate positions
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        
        print(f"\n3. 窗口位置和大小:")
        print(f"   位置: ({left}, {top})")
        print(f"   大小: {width} x {height}")
        
        # Activate window
        print("\n4. 激活窗口...")
        await controller.execute_command('win32_call', {
            'function': 'SetForegroundWindow',
            'args': [hwnd]
        })
        await asyncio.sleep(1)
        
        # Calculate input positions based on common chat UI layouts
        input_positions = [
            {
                'name': '右侧底部（常见聊天输入）',
                'x': left + int(width * 0.75),
                'y': top + int(height * 0.85)
            },
            {
                'name': '底部中央',
                'x': left + int(width * 0.5),
                'y': top + int(height * 0.9)
            },
            {
                'name': '右侧中部',
                'x': left + int(width * 0.75),
                'y': top + int(height * 0.5)
            }
        ]
        
        # AGI discussion messages
        messages = [
            "你好！开始讨论AGI技术。",
            "当前大模型离真正的AGI还有哪些关键差距？",
            "你认为意识和自我认知对AGI必要吗？",
            "如何解决AI的常识推理和因果理解问题？",
            "多模态融合是通向AGI的必经之路吗？",
            "持续学习和避免灾难性遗忘的方案是什么？",
            "AGI需要具备创造力和想象力吗？如何实现？",
            "你认为第一个AGI会在哪个领域率先出现？",
            "从专用AI到通用AI的技术路径是什么？",
            "AGI的评估标准应该是什么？超越图灵测试？"
        ]
        
        # Try first position
        pos = input_positions[0]
        print(f"\n5. 使用位置: {pos['name']}")
        print(f"   坐标: ({pos['x']}, {pos['y']})")
        
        success_count = 0
        
        for i, msg in enumerate(messages):
            print(f"\n消息 {i+1}/{len(messages)}: {msg[:30]}...")
            
            try:
                # Click
                await controller.execute_command('click', {
                    'x': pos['x'],
                    'y': pos['y']
                })
                await asyncio.sleep(0.3)
                
                # Clear
                await controller.execute_command('send_keys', {'keys': '^a'})
                await asyncio.sleep(0.1)
                await controller.execute_command('send_keys', {'keys': '{DELETE}'})
                await asyncio.sleep(0.2)
                
                # Type
                await controller.execute_command('send_keys', {'keys': msg})
                await asyncio.sleep(0.5)
                
                # Send
                await controller.execute_command('send_keys', {'keys': '{ENTER}'})
                
                success_count += 1
                print(f"✅ 发送成功 ({success_count}/{i+1})")
                
                # Wait
                await asyncio.sleep(4)
                
            except Exception as e:
                print(f"❌ 发送失败: {e}")
                await asyncio.sleep(1)
        
        print(f"\n" + "=" * 50)
        print(f"✅ 完成！成功发送 {success_count}/{len(messages)} 条消息")
        print(f"位置: ({pos['x']}, {pos['y']})")
        print(f"请检查Cursor中的对话")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(get_cursor_real_position())