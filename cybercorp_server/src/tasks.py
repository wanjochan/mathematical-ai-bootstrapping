# src/tasks.py - Task Management Module

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Task:
    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: Optional[str] = None
    created_by: str = "system"
    created_at: datetime = None
    updated_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: int = 3600
    metadata: Optional[Dict[str, Any]] = None

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """初始化示例任务数据"""
        sample_tasks = [
            Task(
                id=str(uuid.uuid4()),
                title="系统性能监控",
                description="轮询监控系统性能指标",
                status=TaskStatus.RUNNING,
                priority=TaskPriority.HIGH,
                assigned_to="system",
                created_by="system"
            ),
            Task(
                id=str(uuid.uuid4()),
                title="数据备份",
                description="每日数据备份任务",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                assigned_to="backup_service",
                created_by="admin"
            ),
            Task(
                id=str(uuid.uuid4()),
                title="安全检查",
                description="定期安全扫描",
                status=TaskStatus.COMPLETED,
                priority=TaskPriority.CRITICAL,
                assigned_to="security_team",
                created_by="security_admin",
                completed_at=datetime.now()
            )
        ]
        
        for task in sample_tasks:
            task.created_at = datetime.now()
            task.updated_at = datetime.now()
            self.tasks[task.id] = task
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        return self.tasks.get(task_id)
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务"""
        return [task for task in self.tasks.values() 
                if task.status == status]
    
    def get_tasks_by_assigned_to(self, assigned_to: str) -> List[Task]:
        """根据分配人获取任务"""
        return [task for task in self.tasks.values() 
                if task.assigned_to == assigned_to]
    
    def create_task(self, title: str, description: Optional[str] = None,
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   assigned_to: Optional[str] = None,
                   created_by: str = "system") -> Task:
        """创建新任务"""
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            created_by=created_by,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.tasks[task.id] = task
        return task
    
    def update_task_status(self, task_id: str, new_status: TaskStatus) -> Optional[Task]:
        """更新任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        old_status = task.status
        task.status = new_status
        task.updated_at = datetime.now()
        
        if new_status == TaskStatus.RUNNING and old_status != TaskStatus.RUNNING:
            task.started_at = datetime.now()
        elif new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()
        
        return task
    
    def update_task(self, task_id: str, **kwargs) -> Optional[Task]:
        """更新任务信息"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        for key, value in kwargs.items():
            if hasattr(task, key) and key != 'id':
                setattr(task, key, value)
        
        task.updated_at = datetime.now()
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
    
    def get_task_statistics(self) -> Dict[str, int]:
        """获取任务统计信息"""
        total = len(self.tasks)
        by_status = {}
        by_priority = {}
        
        for task in self.tasks.values():
            if task.status.value in by_status:
                by_status[task.status.value] += 1
            else:
                by_status[task.status.value] = 1
            
            if task.priority.value in by_priority:
                by_priority[task.priority.value] += 1
            else:
                by_priority[task.priority.value] = 1
        
        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority
        }

# 全局任务管理器实例
task_manager = TaskManager()

# 修复缺少的Any类型
from typing import Any