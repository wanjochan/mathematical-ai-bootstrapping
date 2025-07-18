"""动态规划引擎 - 实现任务分解与智能调度"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time
from datetime import datetime, timedelta

from .scheduler import TaskScheduler
from .resource_manager import ResourceManager
from .employee_manager import EmployeeManager
from .task_manager import TaskManager


class TaskState(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """任务数据结构"""
    id: str
    name: str
    description: str
    priority: TaskPriority
    state: TaskState
    dependencies: List[str]
    estimated_duration: float  # 秒
    actual_duration: Optional[float] = None
    assigned_employee: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class DynamicPlanningEngine:
    """动态规划核心引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scheduler = TaskScheduler()
        self.resource_manager = ResourceManager()
        self.employee_manager = EmployeeManager()
        self.task_manager = TaskManager()
        
        self.tasks: Dict[str, Task] = {}
        self.running = False
        self._monitor_task = None
        
    async def start(self):
        """启动动态规划引擎"""
        self.logger.info("Starting Dynamic Planning Engine...")
        self.running = True
        
        # 初始化各管理器
        await self.resource_manager.initialize()
        await self.employee_manager.initialize()
        await self.task_manager.initialize()
        
        # 启动监控任务
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        self.logger.info("Dynamic Planning Engine started")
        
    async def stop(self):
        """停止动态规划引擎"""
        self.logger.info("Stopping Dynamic Planning Engine...")
        self.running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
                
        await self.resource_manager.cleanup()
        await self.employee_manager.cleanup()
        await self.task_manager.cleanup()
        
        self.logger.info("Dynamic Planning Engine stopped")
        
    async def submit_task(self, task: Task) -> str:
        """提交新任务"""
        task_id = task.id
        self.tasks[task_id] = task
        
        # 检查依赖关系
        if await self._check_dependencies(task):
            task.state = TaskState.PENDING
            await self.scheduler.add_task(task)
            self.logger.info(f"Task {task_id} submitted and ready for execution")
        else:
            task.state = TaskState.BLOCKED
            self.logger.info(f"Task {task_id} blocked by dependencies")
            
        return task_id
        
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self.tasks:
            return False
            
        task = self.tasks[task_id]
        if task.state in [TaskState.RUNNING, TaskState.PENDING]:
            task.state = TaskState.CANCELLED
            await self.scheduler.remove_task(task_id)
            self.logger.info(f"Task {task_id} cancelled")
            return True
            
        return False
        
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id not in self.tasks:
            return None
            
        task = self.tasks[task_id]
        return {
            "id": task.id,
            "name": task.name,
            "state": task.state.value,
            "priority": task.priority.value,
            "progress": await self._calculate_progress(task),
            "assigned_employee": task.assigned_employee,
            "estimated_duration": task.estimated_duration,
            "actual_duration": task.actual_duration,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
        
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统整体状态"""
        return {
            "total_tasks": len(self.tasks),
            "pending_tasks": len([t for t in self.tasks.values() if t.state == TaskState.PENDING]),
            "running_tasks": len([t for t in self.tasks.values() if t.state == TaskState.RUNNING]),
            "completed_tasks": len([t for t in self.tasks.values() if t.state == TaskState.COMPLETED]),
            "failed_tasks": len([t for t in self.tasks.values() if t.state == TaskState.FAILED]),
            "available_employees": await self.employee_manager.get_available_count(),
            "resource_utilization": await self.resource_manager.get_utilization(),
            "queue_length": await self.scheduler.get_queue_length()
        }
        
    async def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 检查待执行任务
                await self._process_ready_tasks()
                
                # 更新任务状态
                await self._update_task_states()
                
                # 优化资源分配
                await self._optimize_resources()
                
                # 记录系统状态
                await self._log_system_status()
                
                await asyncio.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # 出错后等待5秒
                
    async def _process_ready_tasks(self):
        """处理就绪任务"""
        ready_tasks = await self.scheduler.get_ready_tasks()
        
        for task in ready_tasks:
            # 分配员工
            employee = await self.employee_manager.assign_employee(task)
            if employee:
                task.assigned_employee = employee.id
                task.state = TaskState.RUNNING
                task.started_at = datetime.utcnow()
                
                # 启动任务执行
                asyncio.create_task(self._execute_task(task, employee))
                
    async def _execute_task(self, task: Task, employee):
        """执行具体任务"""
        try:
            self.logger.info(f"Starting task {task.id} with employee {employee.id}")
            
            # 执行任务逻辑
            start_time = time.time()
            success = await self.task_manager.execute_task(task, employee)
            end_time = time.time()
            
            task.actual_duration = end_time - start_time
            
            if success:
                task.state = TaskState.COMPLETED
                task.completed_at = datetime.utcnow()
                self.logger.info(f"Task {task.id} completed successfully")
            else:
                task.state = TaskState.FAILED
                self.logger.error(f"Task {task.id} failed")
                
        except Exception as e:
            task.state = TaskState.FAILED
            self.logger.error(f"Task {task.id} failed with exception: {e}", exc_info=True)
            
        finally:
            # 释放员工
            await self.employee_manager.release_employee(employee.id, task.id)
            
    async def _check_dependencies(self, task: Task) -> bool:
        """检查任务依赖是否满足"""
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                return False
                
            dep_task = self.tasks[dep_id]
            if dep_task.state != TaskState.COMPLETED:
                return False
                
        return True
        
    async def _update_task_states(self):
        """更新任务状态"""
        # 检查被阻塞的任务是否可以执行
        for task in self.tasks.values():
            if task.state == TaskState.BLOCKED:
                if await self._check_dependencies(task):
                    task.state = TaskState.PENDING
                    await self.scheduler.add_task(task)
                    
    async def _optimize_resources(self):
        """优化资源分配"""
        # 基于当前负载和任务优先级调整资源
        system_status = await self.get_system_status()
        
        # 如果队列过长，增加资源
        if system_status["queue_length"] > 10:
            await self.resource_manager.scale_up()
            
        # 如果资源利用率过低，减少资源
        if system_status["resource_utilization"] < 0.3:
            await self.resource_manager.scale_down()
            
    async def _calculate_progress(self, task: Task) -> float:
        """计算任务进度"""
        if task.state == TaskState.COMPLETED:
            return 100.0
            
        if task.state == TaskState.RUNNING and task.started_at:
            elapsed = (datetime.utcnow() - task.started_at).total_seconds()
            progress = min((elapsed / task.estimated_duration) * 100, 99.0)
            return progress
            
        return 0.0
        
    async def _log_system_status(self):
        """记录系统状态"""
        if len(self.tasks) % 10 == 0:  # 每10个任务记录一次
            status = await self.get_system_status()
            self.logger.info(f"System status: {status}")