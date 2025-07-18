"""
AI中控助理使用示例

展示如何使用AI中控助理的各种功能，包括：
1. 基本任务执行
2. 模式化处理
3. WebSocket实时交互
4. 批量任务处理
"""

import asyncio
import aiohttp
import json
from datetime import datetime

class AIOrchestratorDemo:
    """AI中控助理演示客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/ai-orchestrator"
    
    async def demo_basic_tasks(self):
        """演示基本任务执行"""
        print("=== 基本任务执行演示 ===")
        
        tasks = [
            "用Python实现一个计算器类",
            "设计一个用户管理系统的架构",
            "调试这个TypeError: 'NoneType' object is not iterable错误",
            "如何优化Python代码的性能？"
        ]
        
        async with aiohttp.ClientSession() as session:
            for i, task_description in enumerate(tasks, 1):
                print(f"\n{i}. 执行任务: {task_description}")
                
                task_data = {
                    "description": task_description,
                    "context": {"demo": True, "task_index": i}
                }
                
                async with session.post(
                    f"{self.api_url}/tasks",
                    json=task_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"   ✅ 模式: {result['mode']}")
                        print(f"   ⏱️  耗时: {result['execution_time']:.2f}秒")
                        print(f"   📋 结果: {result['result'].get('status', 'Unknown')}")
                    else:
                        print(f"   ❌ 失败: {response.status}")
    
    async def demo_specific_modes(self):
        """演示指定模式执行"""
        print("\n=== 指定模式执行演示 ===")
        
        mode_tasks = [
            ("architect", "设计一个电商系统"),
            ("code", "实现用户注册功能"),
            ("debug", "修复内存泄漏问题"),
            ("ask", "什么是微服务架构？")
        ]
        
        async with aiohttp.ClientSession() as session:
            for mode, description in mode_tasks:
                print(f"\n📋 {mode.upper()}模式: {description}")
                
                task_data = {
                    "description": description,
                    "mode": mode,
                    "context": {"forced_mode": True}
                }
                
                async with session.post(
                    f"{self.api_url}/tasks",
                    json=task_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"   ✅ 执行成功，耗时: {result['execution_time']:.2f}秒")
                    else:
                        print(f"   ❌ 执行失败")
    
    async def demo_quick_apis(self):
        """演示快捷API"""
        print("\n=== 快捷API演示 ===")
        
        async with aiohttp.ClientSession() as session:
            # 快速编程
            print("\n🚀 快速编程:")
            async with session.post(
                f"{self.api_url}/quick/code",
                params={"description": "排序算法", "language": "python"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Python排序算法实现完成")
            
            # 快速调试
            print("\n🔧 快速调试:")
            async with session.post(
                f"{self.api_url}/quick/debug",
                params={
                    "description": "程序崩溃",
                    "error_details": "Segmentation fault"
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ 调试分析完成")
            
            # 快速询问
            print("\n❓ 快速询问:")
            async with session.post(
                f"{self.api_url}/quick/ask",
                params={"question": "Docker和虚拟机的区别？"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ 问题回答完成")
    
    async def demo_system_status(self):
        """演示系统状态查询"""
        print("\n=== 系统状态查询演示 ===")
        
        async with aiohttp.ClientSession() as session:
            # 获取系统状态
            async with session.get(f"{self.api_url}/status") as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"🟢 系统运行状态: {'正常' if status['is_running'] else '异常'}")
                    print(f"📊 活跃任务数: {status['active_tasks']}")
                    print(f"✅ 已完成任务: {status['completed_tasks']}")
                    print(f"🛠️  可用工具: {', '.join(status['available_tools'])}")
                    print(f"🎯 可用模式: {', '.join(status['available_modes'])}")
            
            # 获取性能指标
            async with session.get(f"{self.api_url}/metrics") as response:
                if response.status == 200:
                    metrics = await response.json()
                    print(f"\n📈 性能指标:")
                    print(f"   已完成任务: {metrics.get('tasks_completed', 0)}")
                    print(f"   平均完成时间: {metrics.get('average_completion_time', 0):.2f}秒")
    
    async def demo_websocket(self):
        """演示WebSocket实时交互"""
        print("\n=== WebSocket实时交互演示 ===")
        
        import websockets
        
        uri = f"ws://localhost:8000/ai-orchestrator/ws/demo_session"
        
        try:
            async with websockets.connect(uri) as websocket:
                # 接收连接确认
                response = await websocket.recv()
                connection_info = json.loads(response)
                print(f"🔗 WebSocket连接已建立: {connection_info['session_id']}")
                
                # 发送任务执行请求
                task_request = {
                    "command": "execute_task",
                    "description": "创建一个Hello World程序",
                    "context": {"websocket_demo": True}
                }
                
                await websocket.send(json.dumps(task_request))
                print("📤 任务请求已发送")
                
                # 接收任务开始通知
                start_response = await websocket.recv()
                start_info = json.loads(start_response)
                if start_info['type'] == 'task_started':
                    print("⚡ 任务执行已开始")
                
                # 接收任务完成结果
                result_response = await websocket.recv()
                result_info = json.loads(result_response)
                if result_info['type'] == 'task_completed':
                    print("✅ 任务执行已完成")
                    print(f"   结果: {result_info['result']['success']}")
                
                # 查询系统状态
                status_request = {"command": "get_status"}
                await websocket.send(json.dumps(status_request))
                
                status_response = await websocket.recv()
                status_info = json.loads(status_response)
                if status_info['type'] == 'system_status':
                    print(f"📊 系统状态: {status_info['is_running']}")
                
        except Exception as e:
            print(f"❌ WebSocket演示失败: {e}")
            print("请确保AI中控助理服务正在运行")
    
    async def demo_batch_processing(self):
        """演示批量任务处理"""
        print("\n=== 批量任务处理演示 ===")
        
        batch_tasks = [
            {
                "description": "实现用户登录功能",
                "mode": "code",
                "context": {"module": "auth"}
            },
            {
                "description": "设计数据库schema",
                "mode": "architect", 
                "context": {"domain": "user_management"}
            },
            {
                "description": "编写单元测试",
                "mode": "code",
                "context": {"test_type": "unit"}
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/batch",
                json={"tasks": batch_tasks}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"🚀 批量任务已启动: {result['message']}")
                else:
                    print(f"❌ 批量任务启动失败")
    
    async def run_all_demos(self):
        """运行所有演示"""
        print("🤖 AI中控助理演示开始")
        print("=" * 50)
        
        try:
            await self.demo_basic_tasks()
            await self.demo_specific_modes()
            await self.demo_quick_apis()
            await self.demo_system_status()
            await self.demo_batch_processing()
            # 注意：WebSocket演示需要websockets库
            # await self.demo_websocket()
            
            print("\n" + "=" * 50)
            print("🎉 演示完成！")
            
        except Exception as e:
            print(f"\n❌ 演示过程中出现错误: {e}")
            print("请确保AI中控助理服务正在运行在 http://localhost:8000")

# 命令行工具
class CLIDemo:
    """命令行演示工具"""
    
    def __init__(self):
        self.demo = AIOrchestratorDemo()
    
    async def interactive_mode(self):
        """交互模式"""
        print("🤖 AI中控助理交互模式")
        print("输入任务描述，AI会自动选择最佳处理方式")
        print("输入 'quit' 退出\n")
        
        async with aiohttp.ClientSession() as session:
            while True:
                task_input = input("📝 请输入任务: ").strip()
                
                if task_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 再见!")
                    break
                
                if not task_input:
                    continue
                
                print("⏳ 处理中...")
                
                try:
                    task_data = {
                        "description": task_input,
                        "context": {"interactive": True}
                    }
                    
                    async with session.post(
                        f"{self.demo.api_url}/tasks",
                        json=task_data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ 模式: {result['mode']}")
                            print(f"⏱️  耗时: {result['execution_time']:.2f}秒")
                            
                            if result['success']:
                                result_data = result.get('result', {})
                                if 'status' in result_data:
                                    print(f"📋 状态: {result_data['status']}")
                                if 'answer' in result_data:
                                    print(f"💡 回答: {result_data['answer']}")
                            else:
                                print(f"❌ 错误: {result.get('error', 'Unknown error')}")
                        else:
                            print(f"❌ 请求失败: {response.status}")
                            
                except Exception as e:
                    print(f"❌ 错误: {e}")
                
                print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # 交互模式
        cli = CLIDemo()
        asyncio.run(cli.interactive_mode())
    else:
        # 演示模式
        demo = AIOrchestratorDemo()
        asyncio.run(demo.run_all_demos()) 