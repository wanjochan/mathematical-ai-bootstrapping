"""Continuous chat with Cursor IDE for multiple rounds"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
import random
import time
from cybercorp_node.utils.remote_control import RemoteController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CursorChatBot:
    """Bot for continuous conversation with Cursor IDE"""
    
    def __init__(self, remote_controller):
        self.controller = remote_controller
        self.conversation_count = 0
        self.hwnd = None
        
        # AGI discussion topics and responses
        self.agi_topics = [
            "你提到的算力问题很有意思。我想深入讨论一下，你认为当前的Transformer架构是否已经接近极限？还是说我们需要全新的架构突破？",
            "关于智能的涌现（emergence），你觉得规模定律（scaling laws）能一直有效吗？还是会遇到瓶颈？",
            "说到意识和自我认知，你认为AGI需要具备意识吗？还是说高级的模式匹配就足够了？",
            "multimodal能力对AGI有多重要？现在的视觉-语言模型算是朝着正确方向前进吗？",
            "你如何看待具身智能（embodied AI）？AGI是否需要与物理世界交互才能真正理解世界？",
            "关于推理能力，Chain-of-Thought这类技术是真正的推理还是模式匹配的巧妙运用？",
            "AGI的安全性和对齐问题，你认为目前的RLHF方法足够吗？还需要什么突破？",
            "世界模型（world model）对AGI的重要性如何？现在的LLM有内部世界模型吗？",
            "持续学习和灾难性遗忘问题，你觉得怎么解决？人脑是如何做到的？",
            "AGI需要情感理解能力吗？还是纯理性就够了？",
            "你怎么看待神经符号AI（neuro-symbolic AI）？结合符号推理是必要的吗？",
            "关于创造力，你认为当前AI的创造力是真正的创新还是组合已有模式？",
            "AGI的能源效率问题，人脑20瓦vs GPU几千瓦，这个差距意味着什么？",
            "量子计算对AGI发展会有帮助吗？还是说经典计算就足够？",
            "你如何定义'理解'？LLM真的理解语言吗？",
            "关于常识推理，为什么这对AI来说这么难？人类是如何获得常识的？",
            "AGI需要有目标和动机吗？还是作为工具就好？",
            "记忆系统的重要性如何？短期记忆、长期记忆、情景记忆都需要吗？",
            "你认为AGI会首先在哪个领域实现？科研、编程还是日常对话？",
            "关于泛化能力，从特定任务到通用智能的鸿沟有多大？",
            "AGI的可解释性重要吗？黑箱模型能成为AGI吗？",
            "你怎么看待集群智能？多个AI协作会比单一大模型更接近AGI吗？",
            "生物启发的方法（如神经形态计算）对AGI有多大帮助？",
            "AGI需要睡眠和做梦吗？这些对智能有什么作用？",
            "关于自主学习，AGI应该如何决定学什么、什么时候学？",
            "你认为AGI的突破会是渐进的还是突然的？会有'智能爆炸'吗？",
            "AGI如何处理不确定性和矛盾信息？",
            "关于价值观和伦理，AGI应该有自己的价值体系吗？",
            "你觉得图灵测试还适用于评估AGI吗？需要新的标准吗？",
            "AGI的创造者会面临什么伦理困境？",
            "如何确保AGI的决策过程是公平和无偏见的？",
            "AGI会改变人类对智能和意识的理解吗？",
            "你认为AGI会有自我保护的本能吗？这是好事还是坏事？",
            "关于知识表示，符号、向量还是混合方式更适合AGI？",
            "AGI需要好奇心吗？如何实现人工好奇心？",
            "你如何看待AGI的社会影响？需要什么样的治理框架？",
            "AGI会让某些人类技能变得过时吗？哪些技能会更重要？",
            "关于创造AGI的动机，是为了增强人类还是替代人类？",
            "你认为第一个AGI会是开源的还是闭源的？各有什么影响？",
            "AGI的发展速度，我们是在加速还是遇到了瓶颈？",
            "如何验证一个系统是否真的达到了AGI水平？",
            "AGI会有个性吗？还是都是相似的？",
            "你觉得AGI和人类智能最大的区别会是什么？",
            "关于直觉，这是AGI需要的能力吗？如何实现？",
            "AGI的学习效率能超过人类吗？在哪些方面？",
            "你认为语言是通向AGI的关键吗？还是只是一个方面？",
            "AGI需要有身份认同感吗？'我是谁'这个问题重要吗？",
            "最后，你个人最期待AGI能帮助解决什么问题？",
            "回顾我们的讨论，你觉得最大的未解之谜是什么？",
            "谢谢精彩的讨论！你对AGI的未来是乐观还是谨慎？"
        ]
        
    async def find_cursor_window(self):
        """Find Cursor IDE window"""
        windows = await self.controller.get_windows()
        for window in windows:
            if 'cursor' in window.get('title', '').lower():
                self.hwnd = window['hwnd']
                return True
        return False
    
    async def send_message(self, message):
        """Send a message to Cursor IDE"""
        if not self.hwnd:
            return False
        
        try:
            # Get window dimensions
            window_info = await self.controller.execute_command('get_window_info', {'hwnd': self.hwnd})
            if window_info and 'rect' in window_info:
                rect = window_info['rect']
                window_width = rect[2] - rect[0]
                window_height = rect[3] - rect[1]
            else:
                window_width = 1200
                window_height = 800
            
            # Try multiple input locations
            input_locations = [
                [int(window_width * 0.75), int(window_height * 0.85)],  # Active conversation
                [int(window_width * 0.5), int(window_height * 0.8)],    # Center-bottom
                [int(window_width * 0.75), int(window_height * 0.6)],   # Right-center
            ]
            
            for pos in input_locations:
                try:
                    # Click to focus
                    await self.controller.execute_command('click', {
                        'x': pos[0],
                        'y': pos[1]
                    })
                    await asyncio.sleep(0.3)
                    
                    # Clear existing content
                    await self.controller.execute_command('send_keys', {'keys': '^a'})
                    await asyncio.sleep(0.1)
                    await self.controller.execute_command('send_keys', {'keys': '{DELETE}'})
                    await asyncio.sleep(0.1)
                    
                    # Type message
                    await self.controller.execute_command('send_keys', {'keys': message})
                    await asyncio.sleep(0.5)
                    
                    # Send
                    await self.controller.execute_command('send_keys', {'keys': '{ENTER}'})
                    await asyncio.sleep(0.2)
                    
                    return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False
    
    async def wait_for_response(self, wait_time=8):
        """Wait for Cursor to respond"""
        print(f"   等待Cursor响应 ({wait_time}秒)...")
        await asyncio.sleep(wait_time)
    
    async def run_conversation(self, rounds=50):
        """Run multiple rounds of conversation"""
        print(f"开始与Cursor进行{rounds}轮对话")
        print("=" * 50)
        
        # Find Cursor window
        if not await self.find_cursor_window():
            print("❌ 未找到Cursor窗口")
            return
        
        print(f"✅ 找到Cursor窗口: {self.hwnd}")
        
        # Activate window
        try:
            await self.controller.execute_command('win32_call', {
                'function': 'SetForegroundWindow',
                'args': [self.hwnd]
            })
            await asyncio.sleep(1)
        except:
            pass
        
        # Start conversation rounds
        for i in range(min(rounds, len(self.agi_topics))):
            self.conversation_count = i + 1
            
            print(f"\n🔄 第{self.conversation_count}轮对话")
            print(f"时间: {time.strftime('%H:%M:%S')}")
            
            # Get topic
            topic = self.agi_topics[i]
            print(f"📝 发送: {topic[:60]}...")
            
            # Send message
            success = await self.send_message(topic)
            
            if success:
                print(f"   ✅ 消息发送成功")
                
                # Wait for response
                wait_time = random.randint(5, 10)
                await self.wait_for_response(wait_time)
                
                # Add some variety in timing
                if i % 5 == 0:
                    print(f"   💭 稍作思考...")
                    await asyncio.sleep(2)
                
            else:
                print(f"   ❌ 消息发送失败，重试...")
                await asyncio.sleep(2)
                # Retry once
                if await self.send_message(topic):
                    print(f"   ✅ 重试成功")
                    await self.wait_for_response(8)
                else:
                    print(f"   ❌ 重试失败，跳过")
            
            # Progress update
            if (i + 1) % 10 == 0:
                print(f"\n📊 进度: {i + 1}/{rounds} 轮完成")
                print(f"⏱️ 已用时: {(i + 1) * 10} 秒")
        
        print(f"\n🎉 对话完成！")
        print(f"✅ 总共进行了 {self.conversation_count} 轮对话")
        print(f"💬 探讨了AGI的各个方面")
        print(f"🤖 请查看Cursor IDE中的完整对话历史")


async def main():
    """Main function"""
    print("Cursor IDE 持续对话测试")
    print("将进行50轮关于AGI的深度对话")
    print("")
    
    try:
        # Connect to remote control
        remote_controller = RemoteController()
        await remote_controller.connect("continuous_chat")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ 未找到目标客户端")
            return
        
        print(f"✅ 已连接到客户端: {target_client}")
        
        # Create chat bot
        bot = CursorChatBot(remote_controller)
        
        # Run conversation
        await bot.run_conversation(rounds=50)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())