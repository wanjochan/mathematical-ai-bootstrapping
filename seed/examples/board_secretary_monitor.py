"""
董秘中控系统示例

演示如何启动董秘中控系统并监控VSCode+Augment进程（员工一号）。
"""
import asyncio
import logging
import sys
import os

# 添加父目录到搜索路径，以便导入core模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.colleague import ColleagueManager, Colleague, Task, TaskPriority
from core.board_secretary import BoardSecretary
from core.logging_config import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

async def main():
    """主函数"""
    logger.info("启动董秘中控系统示例")
    
    # 创建同事管理器
    manager = ColleagueManager()
    
    # 创建董秘实例
    secretary = BoardSecretary("董秘", manager)
    
    # 将董秘添加到管理器
    manager.add_colleague(secretary)
    
    # 创建一个员工一号（模拟VSCode+Augment进程）
    employee1 = Colleague(
        name="员工一号", 
        role="developer",
        skills=["coding", "debugging", "code_review"]
    )
    
    # 将员工一号添加到管理器
    manager.add_colleague(employee1)
    
    # 开始监控员工一号关联的VSCode+Augment进程
    secretary.monitor_ide_process("Code.exe", employee1.id)  # Windows上VSCode进程名通常是Code.exe
    
    # 创建并分配一个测试任务给员工一号
    test_task = Task(
        title="测试功能开发",
        description="开发一个测试功能，用于验证系统",
        priority=TaskPriority.NORMAL
    )
    
    # 添加任务到管理器
    manager.tasks[test_task.id] = test_task
    
    # 分配给员工一号
    employee1.assign_task(test_task)
    
    # 启动董秘监控循环（在后台运行）
    monitoring_task = asyncio.create_task(secretary.run_monitoring_loop())
    
    try:
        # 显示初始状态
        logger.info(f"初始状态:")
        logger.info(f"员工一号: ID={employee1.id}, 状态={employee1.status.value}")
        logger.info(f"当前任务: {employee1.current_task}")
        
        # 等待30秒以观察监控结果
        logger.info("开始监控VSCode进程，等待30秒...")
        
        # 每5秒输出一次状态
        for i in range(6):
            await asyncio.sleep(5)
            status = await secretary.update_process_status()
            
            emp_status = status.get(employee1.id, {})
            process_name = emp_status.get("process_name", "未知")
            process_status = emp_status.get("status", "未知")
            
            logger.info(f"[{i*5}秒] 进程 {process_name} 状态: {process_status}")
            if process_status == "running":
                logger.info(f"  CPU使用率: {emp_status.get('cpu_usage', 0):.2f}%, 内存: {emp_status.get('memory_usage', 0):.2f} MB")
        
        # 生成最终报告
        final_report = await secretary.generate_status_report()
        logger.info(f"最终状态报告:")
        for key, value in final_report.items():
            logger.info(f"{key}: {value}")
            
    except KeyboardInterrupt:
        logger.info("监控被用户中断")
    finally:
        # 取消监控任务
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass
        
        logger.info("董秘中控系统示例结束")

if __name__ == "__main__":
    asyncio.run(main())
