"""
VirtualColleague 模块

实现无界面虚拟员工的核心功能。
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态"""
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()

class ColleagueState(Enum):
    """同事状态"""
    IDLE = auto()
    WORKING = auto()
    ERROR = auto()
    OFFLINE = auto()

@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

class VirtualColleague:
    """
    虚拟同事基类
    
    提供虚拟员工的基本功能，包括：
    - 状态管理
    - 任务处理
    - 事件通知
    """
    
    def __init__(self, name: str, role: str, skills: List[str]):
        """
        初始化虚拟同事
        
        Args:
            name: 同事名称
            role: 角色名称
            skills: 技能列表
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.skills = set(skills)
        self._state = ColleagueState.IDLE
        self._current_task = None
        self._task_callbacks = []
        self._state_callbacks = []
        
    @property
    def state(self) -> ColleagueState:
        """获取当前状态"""
        return self._state
    
    @state.setter
    def state(self, new_state: ColleagueState):
        """更新状态并触发回调"""
        old_state = self._state
        self._state = new_state
        self._notify_state_change(old_state, new_state)
    
    def add_skill(self, skill: str) -> None:
        """添加新技能"""
        self.skills.add(skill)
    
    def remove_skill(self, skill: str) -> None:
        """移除技能"""
        self.skills.discard(skill)
    
    def has_skill(self, skill: str) -> bool:
        """检查是否具备某项技能"""
        return skill in self.skills
    
    def assign_task(self, task: Dict) -> bool:
        """
        分配任务给该同事
        
        Args:
            task: 任务字典，必须包含 'id' 和 'type' 字段
            
        Returns:
            bool: 是否成功接受任务
        """
        if self.state != ColleagueState.IDLE:
            return False
            
        self._current_task = task
        self.state = ColleagueState.WORKING
        return True
    
    async def execute_task(self) -> TaskResult:
        """
        执行当前任务
        
        Returns:
            TaskResult: 任务执行结果
        """
        if not self._current_task:
            return TaskResult(False, "No task assigned")
            
        try:
            task_type = self._current_task.get('type')
            task_handler = getattr(self, f"handle_{task_type}", None)
            
            if not task_handler:
                return TaskResult(False, f"No handler for task type: {task_type}")
                
            result = await task_handler(self._current_task)
            self._current_task = None
            self.state = ColleagueState.IDLE
            return result
            
        except Exception as e:
            logger.exception(f"Error executing task: {e}")
            self.state = ColleagueState.ERROR
            return TaskResult(False, str(e))
    
    def add_task_callback(self, callback: Callable[[str, TaskResult], None]) -> None:
        """添加任务完成回调"""
        self._task_callbacks.append(callback)
    
    def add_state_callback(self, callback: Callable[[ColleagueState, ColleagueState], None]) -> None:
        """添加状态变更回调"""
        self._state_callbacks.append(callback)
    
    def _notify_task_complete(self, result: TaskResult) -> None:
        """通知任务完成"""
        for callback in self._task_callbacks:
            try:
                callback(self.id, result)
            except Exception as e:
                logger.error(f"Error in task callback: {e}")
    
    def _notify_state_change(self, old_state: ColleagueState, new_state: ColleagueState) -> None:
        """通知状态变更"""
        for callback in self._state_callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'skills': list(self.skills),
            'state': self.state.name,
            'current_task': self._current_task
        }
