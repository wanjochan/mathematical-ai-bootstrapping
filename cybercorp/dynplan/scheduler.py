"""任务调度器 - 基于优先级和资源的智能调度"""

import asyncio
import heapq
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .engine import Task, TaskPriority, TaskState


@dataclass
class ScheduledTask:
    """调度任务包装器"""
    task: Task
    priority_score: float = 0.0
    queue_time: datetime = field(default_factory=datetime.utcnow)
    
    def __lt__(self, other):
        return self.priority_score > other.priority_score


class TaskScheduler:
    """智能任务调度器"""
    
    def __init__(self):
        self.task_queue: List[ScheduledTask] = []
        self.task_map: Dict[str, ScheduledTask] = {}
        self.waiting_tasks: Dict[str, Task] = {}
        
    async def add_task(self, task: Task):
        """添加任务到调度队列"""
        # 计算优先级分数
        priority_score = self._calculate_priority_score(task)
        
        scheduled_task = ScheduledTask(
            task=task,
            priority_score=priority_score
        )
        
        # 添加到优先队列
        heapq.heappush(self.task_queue, scheduled_task)
        self.task_map[task.id] = scheduled_task
        
    async def remove_task(self, task_id: str) -> bool:
        """从调度队列移除任务"""
        if task_id not in self.task_map:
            return False
            
        # 标记为已移除，实际从队列中清理会在下次调度时进行
        scheduled_task = self.task_map[task_id]
        scheduled_task.task.state = TaskState.CANCELLED
        
        del self.task_map[task_id]
        return True
        
    async def get_ready_tasks(self) -> List[Task]:
        """获取就绪任务"""
        ready_tasks = []
        
        # 清理已取消的任务
        self._cleanup_cancelled_tasks()
        
        # 获取优先级最高的任务
        while self.task_queue and len(ready_tasks) < 5:  # 每次最多处理5个任务
            scheduled_task = heapq.heappop(self.task_queue)
            
            # 检查任务是否仍然有效
            if (scheduled_task.task.id in self.task_map and 
                scheduled_task.task.state == TaskState.PENDING):
                ready_tasks.append(scheduled_task.task)
                
        return ready_tasks
        
    async def get_queue_length(self) -> int:
        """获取队列长度"""
        return len([t for t in self.task_queue if t.task.state == TaskState.PENDING])
        
    async def get_queue_status(self) -> Dict[str, any]:
        """获取队列状态"""
        pending_count = len([t for t in self.task_queue if t.task.state == TaskState.PENDING])
        
        # 按优先级统计
        priority_stats = {}
        for scheduled_task in self.task_queue:
            if scheduled_task.task.state == TaskState.PENDING:
                priority = scheduled_task.task.priority.name
                priority_stats[priority] = priority_stats.get(priority, 0) + 1
                
        # 计算平均等待时间
        now = datetime.utcnow()
        total_wait_time = 0
        pending_tasks = [t for t in self.task_queue if t.task.state == TaskState.PENDING]
        
        for scheduled_task in pending_tasks:
            wait_time = (now - scheduled_task.queue_time).total_seconds()
            total_wait_time += wait_time
            
        avg_wait_time = total_wait_time / len(pending_tasks) if pending_tasks else 0
        
        return {
            "total_pending": pending_count,
            "priority_distribution": priority_stats,
            "average_wait_time": avg_wait_time,
            "queue_size": len(self.task_queue)
        }
        
    def _calculate_priority_score(self, task: Task) -> float:
        """计算任务优先级分数"""
        base_score = task.priority.value * 10
        
        # 考虑任务等待时间
        wait_time = (datetime.utcnow() - task.created_at).total_seconds()
        wait_bonus = min(wait_time / 60, 10)  # 每分钟增加1分，最多10分
        
        # 考虑任务复杂度
        complexity_factor = min(task.estimated_duration / 60, 5)  # 复杂度加分
        
        # 考虑依赖任务数量
        dependency_penalty = len(task.dependencies) * 2
        
        # 最终分数
        final_score = base_score + wait_bonus + complexity_factor - dependency_penalty
        
        return max(final_score, 1.0)  # 确保分数为正
        
    def _cleanup_cancelled_tasks(self):
        """清理已取消的任务"""
        # 创建新的队列，排除已取消的任务
        new_queue = []
        for scheduled_task in self.task_queue:
            if (scheduled_task.task.state == TaskState.PENDING and 
                scheduled_task.task.id in self.task_map):
                heapq.heappush(new_queue, scheduled_task)
                
        self.task_queue = new_queue
        
    async def rebalance_queue(self):
        """重新平衡队列"""
        # 重新计算所有任务的优先级
        new_queue = []
        
        for scheduled_task in self.task_queue:
            if scheduled_task.task.state == TaskState.PENDING:
                scheduled_task.priority_score = self._calculate_priority_score(
                    scheduled_task.task
                )
                heapq.heappush(new_queue, scheduled_task)
                
        self.task_queue = new_queue
        
    async def prioritize_task(self, task_id: str, new_priority: TaskPriority):
        """调整任务优先级"""
        if task_id not in self.task_map:
            return False
            
        scheduled_task = self.task_map[task_id]
        scheduled_task.task.priority = new_priority
        
        # 重新计算优先级分数
        scheduled_task.priority_score = self._calculate_priority_score(
            scheduled_task.task
        )
        
        # 重新平衡队列
        await self.rebalance_queue()
        
        return True
        
    async def get_task_position(self, task_id: str) -> Optional[int]:
        """获取任务在队列中的位置"""
        if task_id not in self.task_map:
            return None
            
        # 按优先级排序的任务列表
        sorted_tasks = sorted(
            [t for t in self.task_queue if t.task.state == TaskState.PENDING],
            key=lambda x: x.priority_score,
            reverse=True
        )
        
        for i, scheduled_task in enumerate(sorted_tasks):
            if scheduled_task.task.id == task_id:
                return i + 1
                
        return None