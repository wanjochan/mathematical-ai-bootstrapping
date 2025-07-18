"""
董秘中控系统

负责监控和协调各类虚拟员工，包括命令行AI工具和图形界面IDE。
特别支持对接和监控vscode+augment等IDE进程。
"""
import asyncio
import logging
import psutil
import time
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

from .colleague import Colleague, Task, ColleagueStatus, TaskPriority, ColleagueManager

logger = logging.getLogger(__name__)

class EmployeeType(Enum):
    """员工类型"""
    COMMAND_LINE = "command_line"  # 命令行AI工具
    IDE = "ide"                    # 图形界面IDE

class IDEProcess:
    """IDE进程监控对象"""
    def __init__(self, process_name: str, employee_id: str):
        self.process_name = process_name
        self.employee_id = employee_id
        self.pid = None
        self.start_time = None
        self.last_check = None
        self.memory_usage = 0
        self.cpu_usage = 0
        self.status = "unknown"
        
    def update(self) -> bool:
        """更新进程状态，返回进程是否存活"""
        self.last_check = datetime.now()
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'cpu_percent']):
            if self.process_name.lower() in proc.info['name'].lower():
                self.pid = proc.pid
                self.memory_usage = proc.info['memory_info'].rss / 1024 / 1024  # MB
                self.cpu_usage = proc.info['cpu_percent']
                self.status = "running"
                if not self.start_time:
                    self.start_time = datetime.now()
                return True
                
        # 如果之前有PID但现在找不到了
        if self.pid:
            self.status = "stopped"
            self.pid = None
            
        return False

class BoardSecretary(Colleague):
    """
    董秘中控系统
    
    负责监控和协调各类AI员工，并与ColleagueManager集成
    """
    
    def __init__(self, name: str, manager: ColleagueManager):
        super().__init__(
            name=name,
            role="board_secretary",
            skills=["coordination", "monitoring", "task_management"]
        )
        self.manager = manager
        self.monitored_processes: Dict[str, IDEProcess] = {}
        self.process_history: Dict[str, List[Dict[str, Any]]] = {}
        self.last_report_time = datetime.now()
        self.report_interval = 60  # 60秒生成一次报告
        
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.manager.tasks.get(task_id)
    
    def monitor_ide_process(self, process_name: str, employee_id: str) -> None:
        """开始监控IDE进程"""
        logger.info(f"开始监控IDE进程: {process_name} 关联员工ID: {employee_id}")
        ide_process = IDEProcess(process_name, employee_id)
        self.monitored_processes[employee_id] = ide_process
        self.process_history[employee_id] = []
        
    async def update_process_status(self) -> Dict[str, Dict[str, Any]]:
        """更新所有监控进程的状态"""
        status_dict = {}
        
        for emp_id, process in self.monitored_processes.items():
            is_alive = process.update()
            status_dict[emp_id] = {
                "process_name": process.process_name,
                "pid": process.pid,
                "status": process.status,
                "cpu_usage": process.cpu_usage,
                "memory_usage": process.memory_usage,
                "alive": is_alive,
                "last_check": process.last_check
            }
            
            # 记录历史
            self.process_history[emp_id].append(status_dict[emp_id])
            # 只保留最近100条记录
            if len(self.process_history[emp_id]) > 100:
                self.process_history[emp_id] = self.process_history[emp_id][-100:]
                
        return status_dict
    
    async def generate_status_report(self) -> Dict[str, Any]:
        """生成状态报告"""
        process_status = await self.update_process_status()
        colleague_status = self._get_all_colleague_status()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "processes": process_status,
            "colleagues": colleague_status,
            "tasks": self._get_task_summary()
        }
        
        self.last_report_time = datetime.now()
        return report
    
    def _get_all_colleague_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有虚拟同事状态"""
        result = {}
        for cid, colleague in self.manager.colleagues.items():
            result[cid] = {
                "id": colleague.id,
                "name": colleague.name,
                "role": colleague.role,
                "status": colleague.status.value,
                "current_task": colleague.current_task
            }
        return result
    
    def _get_task_summary(self) -> Dict[str, int]:
        """获取任务统计信息"""
        summary = {
            "total": len(self.manager.tasks),
            "pending": 0,
            "assigned": 0,
            "completed": 0,
            "failed": 0
        }
        
        for task in self.manager.tasks.values():
            summary[task.status] = summary.get(task.status, 0) + 1
            
        return summary
    
    async def run_monitoring_loop(self) -> None:
        """运行监控循环"""
        logger.info(f"{self.name} 开始监控循环")
        
        try:
            while True:
                await self.update_process_status()
                
                # 检查是否需要生成报告
                time_since_last_report = (datetime.now() - self.last_report_time).total_seconds()
                if time_since_last_report >= self.report_interval:
                    report = await self.generate_status_report()
                    logger.info(f"状态报告: {report}")
                
                await asyncio.sleep(5)  # 每5秒检查一次
        except Exception as e:
            logger.error(f"监控循环出错: {e}", exc_info=True)
            self.status = ColleagueStatus.ERROR
            
    async def handle_monitor(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理监控任务"""
        target = task.get("target", "all")
        duration = task.get("duration", 60)  # 默认监控60秒
        
        start_time = time.time()
        reports = []
        
        while time.time() - start_time < duration:
            if target == "all" or target == "process":
                process_status = await self.update_process_status()
                reports.append({"timestamp": datetime.now().isoformat(), "process_status": process_status})
            
            await asyncio.sleep(5)
            
        return {
            "success": True,
            "message": f"监控完成，收集了{len(reports)}个数据点",
            "reports": reports
        }
        
    async def handle_assign_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """分配任务给其他同事"""
        task_data = task.get("task_data", {})
        target_colleague_id = task.get("target_colleague_id")
        
        if not target_colleague_id or target_colleague_id not in self.manager.colleagues:
            return {
                "success": False,
                "message": f"目标同事不存在: {target_colleague_id}"
            }
            
        target_colleague = self.manager.colleagues[target_colleague_id]
        
        # 创建任务对象
        new_task = Task(
            title=task_data.get("title", "未命名任务"),
            description=task_data.get("description", ""),
            priority=TaskPriority[task_data.get("priority", "NORMAL").upper()]
        )
        
        # 添加到任务列表
        self.manager.tasks[new_task.id] = new_task
        
        # 分配给目标同事
        assigned = target_colleague.assign_task(new_task)
        
        if assigned:
            return {
                "success": True,
                "message": f"任务分配成功，ID: {new_task.id}",
                "task_id": new_task.id
            }
        else:
            return {
                "success": False,
                "message": f"任务分配失败，目标同事状态: {target_colleague.status.value}"
            }
