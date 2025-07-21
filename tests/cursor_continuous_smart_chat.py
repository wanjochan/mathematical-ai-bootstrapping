"""Continuous smart chat with Cursor - 50 rounds"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
from cybercorp_node.utils.remote_control import RemoteController


async def continuous_smart_chat():
    """Continue chatting with Cursor for 50 rounds"""
    
    print("🤖 Cursor持续对话 - 目标50轮")
    print("=" * 50)
    
    # Extended AGI discussion topics
    topics = [
        # 已发送5条，继续6-50
        "Chain-of-Thought真的是推理还是模式匹配的高级形式？",
        "RLHF是否足够解决AI对齐问题？还需要什么突破？",
        "大语言模型内部是否存在某种形式的世界模型？",
        "如何解决AI的灾难性遗忘问题？人脑是怎么做到持续学习的？",
        "AGI需要情感理解能力吗？纯理性智能是否足够？",
        "神经符号AI的前景如何？符号推理对AGI是必要的吗？",
        "当前AI的创造力是真正的创新还是高级的组合？",
        "人脑20瓦vs GPU数千瓦，这个能效差距告诉我们什么？",
        "量子计算会加速AGI的到来吗？",
        "LLM真的'理解'语言吗？什么是真正的理解？",
        "为什么常识推理对AI如此困难？",
        "AGI应该有自己的目标和动机吗？",
        "不同类型的记忆（短期、长期、情景）对AGI都必要吗？",
        "AGI会首先在哪个领域实现突破？",
        "从专用AI到通用AI的技术鸿沟有多大？",
        "黑箱AI能成为可信赖的AGI吗？",
        "多个AI协作是否比单一大模型更接近AGI？",
        "神经形态计算等生物启发方法的潜力如何？",
        "AGI需要睡眠和梦境吗？它们的功能是什么？",
        "AGI应该如何决定学习什么、何时学习？",
        "AGI的出现会是渐进的还是突然的智能爆炸？",
        "不确定性和矛盾信息的处理对AGI有多重要？",
        "AGI应该有自己的价值体系吗？如何形成？",
        "需要什么新标准来评估AGI？图灵测试还够吗？",
        "创造AGI会面临哪些伦理困境？",
        "如何确保AGI的公平性和无偏见决策？",
        "AGI会改变我们对智能本质的理解吗？",
        "自我保护本能对AGI是必要的吗？",
        "知识表示：符号vs向量vs混合，哪个更适合AGI？",
        "好奇心对AGI有多重要？如何实现人工好奇心？",
        "AGI需要什么样的治理和监管框架？",
        "哪些人类技能会因AGI而过时？哪些会更重要？",
        "AGI的目的：增强人类还是独立发展？",
        "第一个AGI系统会是开源还是闭源？影响如何？",
        "当前AGI研究是在加速还是遇到瓶颈？",
        "如何验证一个系统达到了AGI水平？",
        "AGI会有个性差异吗？还是趋同？",
        "AGI与人类智能的本质区别是什么？",
        "直觉对AGI重要吗？如何实现人工直觉？",
        "AGI的学习效率能超越人类吗？在哪些方面？",
        "语言是通向AGI的关键路径吗？",
        "身份认同对AGI重要吗？",
        "你最期待AGI帮助解决什么问题？",
        "AGI研究中最大的未解之谜是什么？"
    ]
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("continuous_chat")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ 未找到客户端")
            return
            
        print(f"✅ 已连接: {target_client}")
        
        # Find Cursor
        cursor_hwnd = 7670670  # Known Cursor window
        print(f"🎯 使用Cursor窗口: {cursor_hwnd}")
        
        # Get window size
        window_info = await remote_controller.execute_command('get_window_info', {'hwnd': cursor_hwnd})
        if window_info and 'rect' in window_info:
            rect = window_info['rect']
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
        else:
            width = 1200
            height = 800
            
        # Input position (bottom right)
        x = int(width * 0.75)
        y = int(height * 0.85)
        
        print(f"📍 输入位置: ({x}, {y})")
        print(f"📝 准备发送 {len(topics)} 条消息")
        
        # Activate window
        await remote_controller.execute_command('win32_call', {
            'function': 'SetForegroundWindow',
            'args': [cursor_hwnd]
        })
        await asyncio.sleep(1)
        
        # Send messages
        success_count = 5  # Already sent 5
        start_time = time.time()
        
        for i, topic in enumerate(topics):
            msg_num = i + 6  # Starting from message 6
            print(f"\n💬 消息 {msg_num}/50: {topic[:40]}...")
            
            try:
                # Click input area
                await remote_controller.execute_command('click', {'x': x, 'y': y})
                await asyncio.sleep(0.3)
                
                # Clear
                await remote_controller.execute_command('send_keys', {'keys': '^a'})
                await asyncio.sleep(0.1)
                await remote_controller.execute_command('send_keys', {'keys': '{DELETE}'})
                await asyncio.sleep(0.2)
                
                # Type
                await remote_controller.execute_command('send_keys', {'keys': topic})
                await asyncio.sleep(0.5)
                
                # Send
                await remote_controller.execute_command('send_keys', {'keys': '{ENTER}'})
                
                success_count += 1
                print(f"   ✅ 发送成功 ({success_count}/50)")
                
                # Wait for response
                wait_time = 4 + (i % 3)  # Vary wait time
                print(f"   ⏳ 等待{wait_time}秒...")
                await asyncio.sleep(wait_time)
                
                # Progress update
                if msg_num % 10 == 0:
                    elapsed = int(time.time() - start_time)
                    print(f"\n📊 进度报告:")
                    print(f"   已发送: {success_count}/50")
                    print(f"   已用时: {elapsed}秒")
                    print(f"   平均速度: {success_count/(elapsed/60):.1f}条/分钟")
                    
            except Exception as e:
                print(f"   ❌ 发送失败: {e}")
                # Try to recover
                await asyncio.sleep(2)
                
            # Prevent overload
            if msg_num % 5 == 0:
                print(f"   💭 稍作休息...")
                await asyncio.sleep(3)
                
        # Final summary
        total_time = int(time.time() - start_time)
        print(f"\n" + "=" * 50)
        print(f"🎉 对话完成！")
        print(f"✅ 成功发送: {success_count}/50 条消息")
        print(f"⏱️ 总用时: {total_time}秒 ({total_time/60:.1f}分钟)")
        print(f"💬 深入探讨了AGI的各个方面")
        print(f"🤖 请查看Cursor中的完整对话历史")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("开始与Cursor进行50轮AGI深度对话")
    print("预计需要5-8分钟完成")
    print("")
    asyncio.run(continuous_smart_chat())