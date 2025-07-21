"""Continue AGI discussion to reach 50 rounds"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController


async def continue_to_50_rounds():
    """Continue the AGI discussion to reach 50 rounds"""
    
    print("继续AGI讨论 - 目标50轮")
    print("=" * 50)
    
    try:
        controller = RemoteController()
        await controller.connect("continue_50")
        
        target = await controller.find_client("wjc2022")
        if not target:
            return
            
        print(f"✅ 已连接: {target}")
        
        # Use the successful position from before
        cursor_hwnd = 7670670
        x, y = 1150, 780  # Right bottom position that worked
        
        print(f"使用已验证的位置: ({x}, {y})")
        
        # Activate window
        await controller.execute_command('win32_call', {
            'function': 'SetForegroundWindow',
            'args': [cursor_hwnd]
        })
        await asyncio.sleep(1)
        
        # Messages 11-50 (already sent 10)
        messages = [
            # 11-20: 技术架构
            "Transformer之后的下一代架构会是什么？",
            "神经网络的可解释性对AGI有多重要？",
            "量子计算会加速AGI的实现吗？",
            "类脑计算和神经形态芯片的潜力如何？",
            "分布式AI和联邦学习对AGI的意义？",
            "知识蒸馏和模型压缩会影响通用性吗？",
            "自监督学习是通向AGI的关键吗？",
            "强化学习在AGI中的角色是什么？",
            "图神经网络对AGI有什么帮助？",
            "神经符号结合是必要的吗？",
            
            # 21-30: 认知能力
            "AGI需要具备哪些核心认知能力？",
            "如何实现真正的抽象推理？",
            "元学习对AGI有多重要？",
            "AGI如何理解和使用类比？",
            "计划和决策能力如何实现？",
            "AGI需要情绪智能吗？",
            "创造性问题解决的机制是什么？",
            "AGI如何形成和更新信念？",
            "注意力机制够用还是需要新突破？",
            "AGI的记忆系统该如何设计？",
            
            # 31-40: 应用和影响
            "AGI会首先在科研领域产生突破吗？",
            "AGI对教育的革命性影响是什么？",
            "AGI如何改变医疗诊断和治疗？",
            "AGI在创意产业的应用前景？",
            "AGI会如何影响就业市场？",
            "AGI时代人类的核心价值是什么？",
            "如何确保AGI的公平获取？",
            "AGI的监管框架应该怎样设计？",
            "AGI会加剧还是缓解不平等？",
            "人机协作的最佳模式是什么？",
            
            # 41-50: 哲学和未来
            "AGI会改变我们对智能的定义吗？",
            "意识难题对AGI研究的启示？",
            "AGI能理解自己的存在吗？",
            "超级智能是必然的吗？",
            "AGI的道德地位应该如何界定？",
            "人类增强vs人工智能，哪条路更可行？",
            "AGI会有自己的目标和欲望吗？",
            "如何防止AGI的价值偏离？",
            "AGI时代的人类意义何在？",
            "你对AGI的最终愿景是什么？"
        ]
        
        print(f"\n准备发送消息 11-50 (共{len(messages)}条)")
        
        success_count = 10  # Already sent 10
        
        for i, msg in enumerate(messages):
            msg_num = i + 11
            print(f"\n消息 {msg_num}/50: {msg[:25]}...")
            
            try:
                # Click
                await controller.execute_command('click', {'x': x, 'y': y})
                await asyncio.sleep(0.3)
                
                # Clear
                await controller.execute_command('send_keys', {'keys': '^a'})
                await asyncio.sleep(0.1)
                await controller.execute_command('send_keys', {'keys': '{DELETE}'})
                await asyncio.sleep(0.2)
                
                # Type
                await controller.execute_command('send_keys', {'keys': msg})
                await asyncio.sleep(0.4)
                
                # Send
                await controller.execute_command('send_keys', {'keys': '{ENTER}'})
                
                success_count += 1
                print(f"✅ 成功 (总计: {success_count}/50)")
                
                # Wait for response
                wait_time = 3 + (i % 3)  # Vary 3-5 seconds
                await asyncio.sleep(wait_time)
                
                # Progress report every 10 messages
                if msg_num % 10 == 0:
                    print(f"\n📊 进度: {msg_num}/50 完成")
                    
            except Exception as e:
                print(f"❌ 失败: {e}")
                await asyncio.sleep(2)
        
        print(f"\n" + "=" * 50)
        print(f"🎉 AGI深度对话完成！")
        print(f"✅ 成功发送: {success_count}/50 条消息")
        print(f"💬 涵盖了AGI的技术、认知、应用和哲学层面")
        print(f"🤖 请查看Cursor中的完整对话历史")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(continue_to_50_rounds())