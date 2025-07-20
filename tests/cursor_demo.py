"""Cursor IDE备选开发员演示 - cybercorp_node控制Cursor IDE"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.cursor_ide_controller import CursorIDEController
from cybercorp_node.utils.remote_control import RemoteController

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CursorDeveloperAgent:
    """Cursor IDE 备选开发员代理"""
    
    def __init__(self):
        self.remote_controller = RemoteController()
        self.cursor_controller = CursorIDEController(self.remote_controller)
        self.ready = False
        
    async def initialize(self) -> bool:
        """初始化并检查Cursor IDE连接"""
        print("🚀 初始化Cursor IDE备选开发员...")
        
        # 查找Cursor窗口
        hwnd = await self.cursor_controller.find_cursor_window()
        if not hwnd:
            print("❌ 未找到Cursor IDE窗口")
            print("请确保:")
            print("1. Cursor IDE已启动")
            print("2. AI助手面板已打开")
            return False
        
        # 分析UI元素
        elements = await self.cursor_controller.detect_dialog_elements()
        if not elements.input_box:
            print("❌ 未找到输入框，无法控制Cursor IDE")
            return False
        
        print(f"✅ 成功连接到Cursor IDE: {self.cursor_controller.cursor_window['title']}")
        print(f"✅ 检测到UI元素: 输入框 {'✓' if elements.input_box else '✗'} | 发送按钮 {'✓' if elements.send_button else '✗'}")
        
        self.ready = True
        return True
    
    async def ask_cursor(self, question: str) -> str:
        """向Cursor IDE提问并获取回答"""
        if not self.ready:
            return "错误: 开发员代理未就绪"
        
        print(f"\n💬 向Cursor提问: {question}")
        print("⏳ 发送中...")
        
        try:
            # 发送问题并等待回答
            response = await self.cursor_controller.send_and_get_response(question, timeout=60)
            
            if response:
                print(f"✅ 收到回答 ({len(response)}字符)")
                return response
            else:
                print("⚠️ 未收到有效回答")
                return "无法获取Cursor的回答，请检查连接状态"
                
        except Exception as e:
            print(f"❌ 交互失败: {e}")
            return f"交互过程出错: {str(e)}"

async def demo_scenarios():
    """演示各种开发场景"""
    
    developer = CursorDeveloperAgent()
    
    # 初始化
    if not await developer.initialize():
        return False
    
    print("\n" + "="*60)
    print("🎯 Cursor IDE 备选开发员演示")
    print("="*60)
    
    # 演示场景列表
    scenarios = [
        {
            "name": "代码编写",
            "prompt": "写一个Python函数，用递归方法计算斐波那契数列的第n项"
        },
        {
            "name": "代码解释", 
            "prompt": "解释一下什么是装饰器，并给出一个简单的例子"
        },
        {
            "name": "Bug修复",
            "prompt": "这段代码有什么问题: def factorial(n): return n * factorial(n-1)"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 场景 {i}: {scenario['name']}")
        print("-" * 40)
        
        response = await developer.ask_cursor(scenario['prompt'])
        
        print(f"\n📝 Cursor回答:")
        print("-" * 40)
        # 显示回答的前500字符
        preview = response[:500] if response else "无回答"
        print(preview)
        if len(response) > 500:
            print(f"... (还有 {len(response)-500} 字符)")
        
        print("\n⏸️ 按Enter继续下一个场景...")
        input()
    
    print("\n🎉 演示完成！")
    print("✅ cybercorp_node成功控制Cursor IDE，可作为备选开发员使用")
    
    return True

async def interactive_mode():
    """交互模式 - 用户可以直接向Cursor提问"""
    
    developer = CursorDeveloperAgent()
    
    if not await developer.initialize():
        return False
    
    print("\n" + "="*60)
    print("💻 进入交互模式 - 直接与Cursor IDE对话")
    print("="*60)
    print("输入 'quit' 退出")
    print()
    
    while True:
        try:
            question = input("🤔 您的问题: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 退出交互模式")
                break
            
            if not question:
                continue
            
            response = await developer.ask_cursor(question)
            
            print(f"\n💡 Cursor回答:")
            print("-" * 40)
            print(response)
            print("-" * 40)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 用户中断，退出交互模式")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    return True

async def main():
    """主函数"""
    print("🌟 Cursor IDE 备选开发员 - 由cybercorp_node驱动")
    print("="*60)
    print()
    print("选择模式:")
    print("1. 自动演示模式 (展示预设场景)")
    print("2. 交互模式 (自由提问)")
    print("3. 仅测试连接")
    print()
    
    try:
        choice = input("请选择 (1/2/3): ").strip()
        
        if choice == "1":
            success = await demo_scenarios()
        elif choice == "2":
            success = await interactive_mode()
        elif choice == "3":
            developer = CursorDeveloperAgent()
            success = await developer.initialize()
            if success:
                print("✅ 连接测试成功！")
        else:
            print("❌ 无效选择")
            return False
        
        return success
        
    except KeyboardInterrupt:
        print("\n👋 用户取消")
        return False

if __name__ == "__main__":
    print("准备启动 Cursor IDE 备选开发员...")
    print("请确保 Cursor IDE 已经启动并且 AI助手面板可见")
    input("按Enter开始...")
    
    try:
        success = asyncio.run(main())
        if success:
            print("\n🎉 演示成功完成！")
            print("cybercorp_node 现在可以作为 Cursor IDE 的自动化控制器使用")
        else:
            print("\n😞 演示未能完成，请检查Cursor IDE状态")
    except Exception as e:
        print(f"\n💥 演示过程出错: {e}")
        print("请检查:")
        print("1. Cursor IDE是否正常运行")
        print("2. AI助手面板是否打开")
        print("3. 没有其他程序阻挡Cursor窗口")