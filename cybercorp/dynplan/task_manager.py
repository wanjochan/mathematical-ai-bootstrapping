from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid
import asyncio
import logging
from dataclasses import dataclass

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"

class TaskPriority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class EmployeeRole(str, Enum):
    DEVELOPER = "developer"
    FINANCE = "finance"
    MARKETING = "marketing"
    HR = "hr"
    MANAGER = "manager"

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    assigned_employee: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    estimated_hours: float = 1.0
    actual_hours: float = 0.0
    deadline: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def update_status(self, new_status: TaskStatus):
        """更新任务状态"""
        self.status = new_status
        self.updated_at = datetime.now()
    
    def assign_to_employee(self, employee_id: str):
        """分配任务给员工"""
        self.assigned_employee = employee_id
        self.updated_at = datetime.now()
    
    def add_dependency(self, task_id: str):
        """添加任务依赖"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
    
    def remove_dependency(self, task_id: str):
        """移除任务依赖"""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
    
    def is_ready(self, task_manager: 'TaskManager') -> bool:
        """检查任务是否准备好执行（所有依赖已完成）"""
        for dep_id in self.dependencies:
            dep_task = task_manager.get_task_by_id(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "assigned_employee": self.assigned_employee,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "tags": self.tags,
            "metadata": self.metadata
        }

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """初始化任务管理器"""
        logging.getLogger(__name__).info("Task Manager initialized")
    
    async def cleanup(self):
        """清理资源"""
        logging.getLogger(__name__).info("Task Manager cleaned up")
    
    async def create_task(self, title: str, description: str, priority: TaskPriority = TaskPriority.MEDIUM,
                         estimated_hours: float = 1.0, deadline: Optional[datetime] = None,
                         tags: List[str] = None, metadata: Dict[str, Any] = None) -> Task:
        """创建新任务"""
        async with self._lock:
            task = Task(
                title=title,
                description=description,
                priority=priority,
                estimated_hours=estimated_hours,
                deadline=deadline,
                tags=tags or [],
                metadata=metadata or {}
            )
            self.tasks[task.id] = task
            self.task_queue.append(task)
            return task
    
    async def update_task(self, task_id: str, **kwargs) -> bool:
        """更新任务信息"""
        async with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = datetime.now()
            return True
    
    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        async with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks.pop(task_id)
            if task in self.task_queue:
                self.task_queue.remove(task)
            return True
    
    async def assign_task(self, task_id: str, employee_id: str) -> bool:
        """分配任务给员工"""
        async with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.assign_to_employee(employee_id)
            return True
    
    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态"""
        async with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.update_status(status)
            return True
    
    async def add_task_dependency(self, task_id: str, dependency_id: str) -> bool:
        """添加任务依赖"""
        async with self._lock:
            if task_id not in self.tasks or dependency_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.add_dependency(dependency_id)
            return True
    
    async def remove_task_dependency(self, task_id: str, dependency_id: str) -> bool:
        """移除任务依赖"""
        async with self._lock:
            if task_id not in self.tasks or dependency_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.remove_dependency(dependency_id)
            return True
    
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
        task = self.tasks.get(task_id)
        return task.dependencies if task else []
    
    async def get_ready_tasks(self) -> List[Task]:
        """获取准备就绪的任务（所有依赖已完成）"""
        ready_tasks = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING and task.is_ready(self):
                ready_tasks.append(task)
        return ready_tasks
    
    async def get_task_stats(self) -> Dict[str, int]:
        """获取任务统计信息"""
        return {
            "total_tasks": len(self.tasks),
            "pending_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            "running_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]),
            "completed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
            "cancelled_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.CANCELLED]),
            "blocked_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.BLOCKED])
        }
    
    async def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    async def get_task_queue(self) -> List[Task]:
        """获取任务队列"""
        return self.task_queue.copy()
    
    async def clear_task_queue(self):
        """清空任务队列"""
        async with self._lock:
            self.task_queue.clear()
    
    async def reorder_task_queue(self, task_ids: List[str]):
        """重新排序任务队列"""
        async with self._lock:
            new_queue = []
            for task_id in task_ids:
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                    if task in self.task_queue:
                        self.task_queue.remove(task)
                    new_queue.append(task)
            
            # 添加剩余的任务
            for task in self.task_queue:
                if task not in new_queue:
                    new_queue.append(task)
            
            self.task_queue = new_queue