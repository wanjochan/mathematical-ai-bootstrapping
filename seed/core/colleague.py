"""
CyberColleague 核心模块

提供虚拟同事的基本实现，包括任务管理和状态跟踪。
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import logging
import uuid
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ColleagueStatus(Enum):
    """同事状态"""
    IDLE = "idle"
    WORKING = "working"
    BUSY = "busy"
    ERROR = "error"

class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3

@dataclass
class Task:
    """任务定义"""
    title: str
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: TaskPriority = TaskPriority.NORMAL
    status: str = "pending"
    progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class Colleague:
    """虚拟同事基类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: str
    skills: List[str]
    status: ColleagueStatus = ColleagueStatus.IDLE
    current_task: Optional[str] = None
    
    def assign_task(self, task: Task) -> bool:
        """分配任务给同事"""
        if self.status != ColleagueStatus.IDLE:
            return False
            
        task.assigned_to = self.id
        task.status = "assigned"
        self.current_task = task.id
        self.status = ColleagueStatus.WORKING
        return True
    
    def update_task_progress(self, progress: float) -> None:
        """更新任务进度"""
        if not self.current_task:
            return
            
        task = self.get_task(self.current_task)
        if task:
            task.progress = max(0.0, min(1.0, progress))
    
    def complete_task(self, result: Optional[Dict] = None) -> Optional[Task]:
        """标记任务为完成"""
        if not self.current_task:
            return None
            
        task = self.get_task(self.current_task)
        if task:
            task.status = "completed"
            task.progress = 1.0
            task.result = result
            self.current_task = None
            self.status = ColleagueStatus.IDLE
            return task
        return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务（子类实现）"""
        raise NotImplementedError

class ColleagueManager:
    """同事管理器"""
    def __init__(self):
        self.colleagues: Dict[str, Colleague] = {}
        self.tasks: Dict[str, Task] = {}
    
    def add_colleague(self, colleague: Colleague) -> None:
        """添加新同事"""
        self.colleagues[colleague.id] = colleague
    
    def create_task(self, title: str, description: str, 
                   priority: TaskPriority = TaskPriority.NORMAL) -> Task:
        """创建新任务"""
        task = Task(title=title, description=description, priority=priority)
        self.tasks[task.id] = task
        return task
    
    def assign_task(self, task_id: str, colleague_id: str) -> bool:
        """分配任务给指定同事"""
        if task_id not in self.tasks or colleague_id not in self.colleagues:
            return False
            
        task = self.tasks[task_id]
        colleague = self.colleagues[colleague_id]
        return colleague.assign_task(task)
    
    def get_colleague_status(self) -> Dict[str, Any]:
        """获取所有同事状态"""
        return {
            cid: {
                'name': c.name,
                'role': c.role,
                'status': c.status.value,
                'current_task': c.current_task
            }
            for cid, c in self.colleagues.items()
        }
