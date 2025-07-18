"""
虚拟同事演示脚本

展示如何使用 VirtualColleague 和 Developer 类。
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from core.developer import Developer
from core.virtual_colleague import TaskResult

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('virtual_colleagues.log')
    ]
)

logger = logging.getLogger(__name__)

class VirtualOffice:
    """虚拟办公室，管理虚拟同事"""
    
    def __init__(self):
        self.colleagues = {}
        self.task_queue = asyncio.Queue()
        self.running = False
    
    def add_colleague(self, colleague):
        """添加同事到办公室"""
        self.colleagues[colleague.id] = colleague
        colleague.add_task_callback(self.on_task_complete)
        colleague.add_state_callback(self.on_state_change)
        logger.info(f"新同事加入: {colleague.name} ({colleague.role})")
    
    async def start(self):
        """启动办公室"""
        self.running = True
        logger.info("虚拟办公室开始运作...")
        
        # 启动任务处理循环
        await self.process_tasks()
    
    async def stop(self):
        """停止办公室"""
        self.running = False
        logger.info("虚拟办公室停止运作")
    
    async def add_task(self, task: dict):
        """添加新任务到队列"""
        await self.task_queue.put(task)
        logger.info(f"新任务已添加: {task.get('type')} - {task.get('id', '')}")
    
    async def process_tasks(self):
        """处理任务队列"""
        while self.running:
            try:
                # 获取任务
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # 查找合适的同事
                colleague = self.find_colleague_for_task(task)
                if not colleague:
                    logger.warning(f"没有合适的同事处理任务: {task}")
                    continue
                
                # 分配任务
                if colleague.assign_task(task):
                    logger.info(f"任务 {task.get('id')} 已分配给 {colleague.name}")
                    
                    # 异步执行任务
                    asyncio.create_task(self.execute_task(colleague))
                else:
                    logger.warning(f"无法分配任务给 {colleague.name}，状态: {colleague.state}")
                    # 将任务重新放回队列
                    await self.task_queue.put(task)
                    
            except asyncio.TimeoutError:
                # 超时检查是否应该停止
                continue
            except Exception as e:
                logger.error(f"处理任务时出错: {e}")
    
    async def execute_task(self, colleague):
        """执行同事的当前任务"""
        try:
            result = await colleague.execute_task()
            if result.success:
                logger.info(f"任务完成: {result.message}")
            else:
                logger.error(f"任务失败: {result.message}")
        except Exception as e:
            logger.exception(f"执行任务时发生错误: {e}")
    
    def find_colleague_for_task(self, task: dict):
        """根据任务类型找到合适的同事"""
        task_type = task.get('type', '')
        
        for colleague in self.colleagues.values():
            # 简单实现：查找第一个空闲的同事
            if colleague.state.name == 'IDLE':
                return colleague
        
        return None
    
    def on_task_complete(self, colleague_id: str, result: TaskResult):
        """任务完成回调"""
        colleague = self.colleagues.get(colleague_id)
        if colleague:
            status = "成功" if result.success else "失败"
            logger.info(f"{colleague.name} 完成任务: {status} - {result.message}")
    
    def on_state_change(self, old_state, new_state):
        """状态变更回调"""
        logger.debug(f"同事状态变更: {old_state.name} -> {new_state.name}")

async def main():
    """主函数"""
    # 创建虚拟办公室
    office = VirtualOffice()
    
    # 添加开发者
    dev1 = Developer("张伟", ["python", "git", "docker"])
    dev2 = Developer("李娜", ["python", "javascript", "react"])
    
    office.add_colleague(dev1)
    office.add_colleague(dev2)
    
    # 启动办公室
    office_task = asyncio.create_task(office.start())
    
    try:
        # 添加一些任务
        tasks = [
            {"id": "task1", "type": "develop_feature", "feature": "用户登录", "complexity": "high"},
            {"id": "task2", "type": "fix_bug", "bug_id": "BUG-123", "severity": "high"},
            {"id": "task3", "type": "code_review", "pr_id": "42"},
            {"id": "task4", "type": "develop_feature", "feature": "购物车功能", "complexity": "medium"},
        ]
        
        for task in tasks:
            await office.add_task(task)
            await asyncio.sleep(0.5)  # 添加一些延迟
        
        # 运行一段时间
        await asyncio.sleep(10)
        
    except KeyboardInterrupt:
        logger.info("接收到停止信号...")
    finally:
        # 清理
        await office.stop()
        office_task.cancel()
        try:
            await office_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())
