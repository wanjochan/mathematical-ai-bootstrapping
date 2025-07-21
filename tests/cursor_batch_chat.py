"""Batch chat with Cursor IDE - more stable approach"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_batch_messages_to_cursor():
    """Send multiple messages to Cursor in batches"""
    
    print("CURSOR IDE 批量对话测试")
    print("分批发送AGI讨论消息")
    print("=" * 40)
    
    # AGI discussion messages (shorter for stability)
    messages = [
        "关于算力瓶颈，你觉得Transformer还能走多远？",
        "智能涌现是真实的还是我们的错觉？",
        "AGI需要意识吗？还是高级模式匹配就够了？",
        "多模态对AGI有多重要？",
        "具身智能是AGI的必要条件吗？",
        "Chain-of-Thought是真正的推理吗？",
        "RLHF能解决对齐问题吗？",
        "LLM有内部世界模型吗？",
        "如何解决灾难性遗忘？",
        "AGI需要情感吗？",
        "符号推理对AGI必要吗？",
        "AI的创造力是真的吗？",
        "人脑20瓦vs GPU千瓦意味着什么？",
        "量子计算对AGI有帮助吗？",
        "LLM真的理解语言吗？",
        "为什么常识推理这么难？",
        "AGI需要目标和动机吗？",
        "记忆系统有多重要？",
        "AGI会先在哪个领域实现？",
        "从专用到通用的鸿沟有多大？",
        "黑箱模型能成为AGI吗？",
        "集群智能更接近AGI吗？",
        "生物启发方法有用吗？",
        "AGI需要睡眠吗？",
        "AGI如何自主学习？",
        "会有智能爆炸吗？",
        "AGI如何处理不确定性？",
        "AGI该有自己的价值观吗？",
        "图灵测试还适用吗？",
        "AGI的伦理困境是什么？"
    ]
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("batch_chat")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ 未找到目标客户端")
            return False
        
        print(f"✅ 已连接到客户端: {target_client}")
        
        # Find Cursor window
        windows = await remote_controller.get_windows()
        cursor_window = None
        for window in windows:
            if 'cursor' in window.get('title', '').lower():
                cursor_window = window
                break
        
        if not cursor_window:
            print("❌ 未找到Cursor窗口")
            return False
        
        hwnd = cursor_window['hwnd']
        print(f"✅ 找到Cursor窗口: {hwnd}")
        
        # Get window dimensions
        try:
            window_info = await remote_controller.execute_command('get_window_info', {'hwnd': hwnd})
            if window_info and 'rect' in window_info:
                rect = window_info['rect']
                window_width = rect[2] - rect[0]
                window_height = rect[3] - rect[1]
            else:
                window_width = 1200
                window_height = 800
        except:
            window_width = 1200
            window_height = 800
        
        # Input position (active conversation area)
        input_x = int(window_width * 0.75)
        input_y = int(window_height * 0.85)
        
        print(f"\n📍 输入位置: ({input_x}, {input_y})")
        print(f"🔢 准备发送 {len(messages)} 条消息")
        
        # Activate window
        try:
            await remote_controller.execute_command('win32_call', {
                'function': 'SetForegroundWindow',
                'args': [hwnd]
            })
            await asyncio.sleep(1)
        except:
            pass
        
        # Send messages in batches
        batch_size = 5
        success_count = 0
        
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(messages) + batch_size - 1) // batch_size
            
            print(f"\n📦 批次 {batch_num}/{total_batches}")
            
            for j, msg in enumerate(batch):
                msg_num = i + j + 1
                print(f"\n💬 消息 {msg_num}: {msg}")
                
                try:
                    # Click to focus
                    await remote_controller.execute_command('click', {
                        'x': input_x,
                        'y': input_y
                    })
                    await asyncio.sleep(0.3)
                    
                    # Clear
                    await remote_controller.execute_command('send_keys', {'keys': '^a'})
                    await asyncio.sleep(0.1)
                    await remote_controller.execute_command('send_keys', {'keys': '{DELETE}'})
                    await asyncio.sleep(0.2)
                    
                    # Type message
                    await remote_controller.execute_command('send_keys', {'keys': msg})
                    await asyncio.sleep(0.5)
                    
                    # Send
                    await remote_controller.execute_command('send_keys', {'keys': '{ENTER}'})
                    
                    print(f"   ✅ 发送成功")
                    success_count += 1
                    
                    # Wait for response
                    print(f"   ⏳ 等待响应...")
                    await asyncio.sleep(6)
                    
                except Exception as e:
                    print(f"   ❌ 发送失败: {e}")
                    # Try to reconnect for next message
                    try:
                        await remote_controller.disconnect()
                        await asyncio.sleep(1)
                        await remote_controller.connect("batch_chat_retry")
                        target_client = await remote_controller.find_client("wjc2022")
                        if target_client:
                            print(f"   🔄 重新连接成功")
                    except:
                        pass
            
            # Batch completed
            print(f"\n✅ 批次 {batch_num} 完成")
            print(f"📊 进度: {min(i + batch_size, len(messages))}/{len(messages)}")
            
            # Pause between batches
            if i + batch_size < len(messages):
                print(f"⏸️ 批次间休息3秒...")
                await asyncio.sleep(3)
        
        print(f"\n🎉 对话完成！")
        print(f"✅ 成功发送 {success_count}/{len(messages)} 条消息")
        print(f"💬 探讨了AGI的核心问题")
        print(f"🤖 请查看Cursor IDE中的对话历史")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 批量对话失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function"""
    print("准备进行Cursor IDE批量对话测试")
    print("将分批发送30条AGI讨论消息")
    print("")
    
    await asyncio.sleep(1)
    
    success = await send_batch_messages_to_cursor()
    
    if success:
        print("\n" + "=" * 50)
        print("批量对话测试成功！")
        print("系统成功与Cursor进行了多轮AGI讨论")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())