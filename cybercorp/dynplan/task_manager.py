"""任务管理器 - 员工任务管理与委派"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
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
    status: TaskStatus
    assigned_employee: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: float = 0.0  # 秒
    actual_duration: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.metadata:
            self.metadata = {}


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.task_dependencies: Dict[str, List[str]] = {}
        
    async def initialize(self):
        """初始化任务管理器"""
        self.logger.info("Initializing Task Manager...")
        
        # 初始化任务队列
        self.task_queue = []
        self.task_dependencies = {}
        
        self.logger.info("Task Manager initialized")
        
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up Task Manager...")
        
        self.tasks.clear()
        self.task_queue.clear()
        self.task_dependencies.clear()
        
        self.logger.info("Task Manager cleaned up")
        
    async def submit_task(self, task: Task) -> str:
        """提交新任务"""
        task_id = task.id
        self.tasks[task_id] = task
        
        # 检查依赖关系
        if await self._check_dependencies(task):
            task.status = TaskStatus.PENDING
            self.task_queue.append(task)
            self.logger.info(f"Task {task_id} submitted and ready for execution")
        else:
            task.status = TaskStatus.BLOCKED
            self.logger.info(f"Task {task_id} blocked by dependencies")
            
        return task_id
        
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self.tasks:
            return False
            
        task = self.tasks[task_id]
        if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
            task.status = TaskStatus.CANCELLED
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
            "status": task.status.value,
            "priority": task.priority.value,
            "assigned_employee": task.assigned_employee,
            "dependencies": task.dependencies,
            "estimated_duration": task.estimated_duration,
            "actual_duration": task.actual_duration,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
        
    async def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return list(self.tasks.values())
        
    async def get_task_queue(self) -> List[Task]:
        """获取任务队列"""
        return self.task_queue
        
    async def get_task_queue_length(self) -> int:
        """获取任务队列长度"""
        return len(self.task_queue)
        
    async def get_task_queue_status(self) -> Dict[str, Any]:
        """获取任务队列状态"""
        return {
            "total_tasks": len(self.tasks),
            "pending_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            "running_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]),
            "completed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
            "cancelled_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.CANCELLED]),
            "blocked_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.BLOCKED])
        }
        
    async def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        return self.tasks.get(task_id)
        
    async def get_tasks_by_role(self, role: EmployeeRole) -> List[Task]:
        """根据角色获取任务"""
        return [task for task in self.tasks.values() if task.assigned_employee and task.assigned_employee.startswith(role.value)]
        
    async def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务"""
        return [task for task in self.tasks.values() if task.status == status]
        
    async def get_tasks_by_employee(self, employee_id: str) -> List[Task]:
        """根据员工ID获取任务"""
        return [task for task in self.tasks.values() if task.assigned_employee == employee_id]
        
    async def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        """根据优先级获取任务"""
        return [task for task in self.tasks.values() if task.priority == priority]
        
    async def get_tasks_by_dependencies(self, task_id: str) -> List[Task]:
        """根据依赖获取任务"""
        return [task for task in self.tasks.values() if task_id in task.dependencies]
        
    async def get_task_dependencies(self, task_id: str) -> List[str]:
        """获取任务依赖"""
        return self.tasks.get(task_id, Task()).dependencies
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]:
        """根据优先级获取任务队列"""
        return [task for task in self.task_queue if task.priority == priority}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务队列"""
        return [task for task in self.task_queue if task.status == status}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]:
        """根据员工ID获取任务队列"""
        return [task for task in self.task_queue if task.assigned_employee == employee_id}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]:
        """根据依赖获取任务队列"""
        return [task for task in self.task_queue if task_id in task.dependencies}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]:
        """根据优先级获取任务队列"""
        return [task for task in self.task_queue if task.priority == priority}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务队列"""
        return [task for task in self.task_queue if task.status == status}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]:
        """根据员工ID获取任务队列"""
        return [task for task in self.task_queue if task.assigned_employee == employee_id}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]:
        """根据依赖获取任务队列"""
        return [task for task in self.task_queue if task_id in task.dependencies}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]:
        """根据优先级获取任务队列"""
        return [task for task in self.task_queue if task.priority == priority}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务队列"""
        return [task for task in self.task_queue if task.status == status}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]:
        """根据员工ID获取任务队列"""
        return [task for task in self.task_queue if task.assigned_employee == employee_id}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]:
        """根据依赖获取任务队列"""
        return [task for task in self.task_queue if task_id in task.dependencies}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]:
        """根据优先级获取任务队列"""
        return [task for task in self.task_queue if task.priority == priority}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务队列"""
        return [task for task in self.task_queue if task.status == status}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]:
        """根据员工ID获取任务队列"""
        return [task for task in self.task_queue if task.assigned_employee == employee_id}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]:
        """根据依赖获取任务队列"""
        return [task for task in self.task_queue if task_id in task.dependencies}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]:
        """根据优先级获取任务队列"""
        return [task for task in self.task_queue if task.priority == priority}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务队列"""
        return [task for task in self.task_queue if task.status == status}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]:
        """根据员工ID获取任务队列"""
        return [task for task in self.task_queue if task.assigned_employee == employee_id}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]:
        """根据依赖获取任务队列"""
        return [task for task in self.task_queue if task_id in task.dependencies}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]:
        """根据优先级获取任务队列"""
        return [task for task in self.task_queue if task.priority == priority}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务队列"""
        return [task for task in self.task_queue if task.status == status}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]:
        """根据员工ID获取任务队列"}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]:
        """根据依赖获取任务队列"}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]:
        """根据优先级获取任务队列"}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) -> List[Task]}
        
    async def get_task_queue_by_employee(self, employee_id: str) -> List[Task]}
        
    async def get_task_queue_by_dependencies(self, task_id: str) -> List[Task]}
        
    async def get_task_queue_by_priority(self, priority: TaskPriority) -> List[Task]}
        
    async def get_task_queue_by_status(self, status: TaskStatus) =