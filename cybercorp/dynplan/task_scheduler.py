"""任务调度器 - 基于优先级的智能任务调度"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .task_manager import Task, TaskStatus, TaskPriority
from .employee_manager import VirtualEmployee, EmployeeManager
from .dynamic_planning_engine import DynamicPlanningEngine, PlanningStrategy


class SchedulingAlgorithm(Enum):
    """调度算法"""
    ROUND_ROBIN = "round_robin"
    PRIORITY_QUEUE = "priority_queue"
    FAIR_SHARING = "fair_sharing"
    DEADLINE_AWARE = "deadline_aware"


@dataclass
class SchedulingDecision:
    """调度决策"""
    task_id: str
    employee_id: str
    scheduled_time: datetime
    estimated_completion: datetime
    priority_adjustment: float
    reason: str


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scheduling_queue: List[Task] = []
        self.scheduling_history: List[SchedulingDecision] = []
        self.current_algorithm = SchedulingAlgorithm.PRIORITY_QUEUE
        self.planning_engine = DynamicPlanningEngine()
        
    async def initialize(self):
        """初始化调度器"""
        self.logger.info("Initializing Task Scheduler...")
        self.scheduling_queue.clear()
        self.scheduling_history.clear()
        await self.planning_engine.initialize()
        self.logger.info("Task Scheduler initialized")
        
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up Task Scheduler...")
        self.scheduling_queue.clear()
        self.scheduling_history.clear()
        await self.planning_engine.cleanup()
        self.logger.info("Task Scheduler cleaned up")
        
    async def schedule_tasks(self, 
                           tasks: List[Task], 
                           employees: List[VirtualEmployee]) -> List[SchedulingDecision]:
        """调度任务"""
        self.logger.info(f"Scheduling {len(tasks)} tasks for {len(employees)} employees")
        
        # 过滤可调度任务
        schedulable_tasks = [t for t in tasks 
                           if t.status in [TaskStatus.PENDING, TaskStatus.BLOCKED]]
        
        if not schedulable_tasks:
            return []
            
        # 使用规划引擎生成调度计划
        plan = await self.planning_engine.plan_tasks(
            schedulable_tasks, 
            employees,
            strategy=PlanningStrategy.BALANCED
        )
        
        # 根据计划生成调度决策
        decisions = []
        for assignment in plan.get("assignments", []):
            decision = SchedulingDecision(
                task_id=assignment["task_id"],
                employee_id=assignment["employee_id"],
                scheduled_time=datetime.utcnow(),
                estimated_completion=assignment["estimated_completion"],
                priority_adjustment=0.0,
                reason=f"Optimized by {plan['strategy']} strategy"
            )
            decisions.append(decision)
            self.scheduling_history.append(decision)
            
        self.logger.info(f"Generated {len(decisions)} scheduling decisions")
        return decisions
        
    async def reschedule_tasks(self, 
                             tasks: List[Task], 
                             employees: List[VirtualEmployee],
                             reason: str = "dynamic_reallocation") -> List[SchedulingDecision]:
        """重新调度任务"""
        self.logger.info(f"Rescheduling {len(tasks)} tasks due to: {reason}")
        
        # 取消现有调度
        for task in tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                task.status = TaskStatus.PENDING
                
        # 重新调度
        return await self.schedule_tasks(tasks, employees)
        
    async def get_scheduling_queue(self) -> List[Task]:
        """获取调度队列"""
        return self.scheduling_queue
        
    async def get_scheduling_history(self, 
                                   limit: int = 50) -> List[SchedulingDecision]:
        """获取调度历史"""
        return self.scheduling_history[-limit:]
        
    async def get_scheduling_metrics(self) -> Dict[str, Any]:
        """获取调度指标"""
        if not self.scheduling_history:
            return {"message": "No scheduling history available"}
            
        recent_decisions = self.scheduling_history[-20:]
        
        # 计算指标
        total_tasks = len(recent_decisions)
        avg_completion_time = sum(
            (d.estimated_completion - d.scheduled_time).total_seconds() 
            for d in recent_decisions
        ) / total_tasks if total_tasks > 0 else 0
        
        employee_distribution = {}
        for decision in recent_decisions:
            emp_id = decision.employee_id
            employee_distribution[emp_id] = employee_distribution.get(emp_id, 0) + 1
            
        return {
            "total_scheduled_tasks": len(self.scheduling_history),
            "recent_scheduled_tasks": total_tasks,
            "average_completion_time": avg_completion_time,
            "employee_distribution": employee_distribution,
            "current_algorithm": self.current_algorithm.value
        }
        
    async def optimize_scheduling(self, 
                                feedback_data: Dict[str, Any]) -> bool:
        """优化调度策略"""
        self.logger.info("Optimizing scheduling based on feedback")
        
        # 根据反馈调整算法
        if feedback_data.get("missed_deadlines", 0) > 5:
            self.current_algorithm = SchedulingAlgorithm.DEADLINE_AWARE
        elif feedback_data.get("unfair_distribution", 0) > 0.3:
            self.current_algorithm = SchedulingAlgorithm.FAIR_SHARING
        elif feedback_data.get("low_priority_starvation", 0) > 0:
            self.current_algorithm = SchedulingAlgorithm.PRIORITY_QUEUE
        else:
            self.current_algorithm = SchedulingAlgorithm.ROUND_ROBIN
            
        self.logger.info(f"Switched to {self.current_algorithm.value} algorithm")
        return True
        
    def _apply_scheduling_algorithm(self, 
                                  tasks: List[Task], 
                                  employees: List[VirtualEmployee]) -> List[Tuple[Task, VirtualEmployee]]:
        """应用调度算法"""
        if self.current_algorithm == SchedulingAlgorithm.ROUND_ROBIN:
            return self._round_robin_schedule(tasks, employees)
        elif self.current_algorithm == SchedulingAlgorithm.PRIORITY_QUEUE:
            return self._priority_queue_schedule(tasks, employees)
        elif self.current_algorithm == SchedulingAlgorithm.FAIR_SHARING:
            return self._fair_sharing_schedule(tasks, employees)
        else:
            return self._deadline_aware_schedule(tasks, employees)
            
    def _round_robin_schedule(self, 
                            tasks: List[Task], 
                            employees: List[VirtualEmployee]) -> List[Tuple[Task, VirtualEmployee]]:
        """轮询调度"""
        assignments = []
        employee_index = 0
        
        for task in tasks:
            if employee_index < len(employees):
                assignments.append((task, employees[employee_index]))
                employee_index = (employee_index + 1) % len(employees)
                
        return assignments
        
    def _priority_queue_schedule(self, 
                               tasks: List[Task], 
                               employees: List[VirtualEmployee]) -> List[Tuple[Task, VirtualEmployee]]:
        """优先级队列调度"""
        # 按优先级排序任务
        sorted_tasks = sorted(tasks, 
                            key=lambda t: (t.priority.value, -t.estimated_duration))
        
        # 按能力排序员工
        sorted_employees = sorted(employees, 
                                key=lambda e: e.skill_level, 
                                reverse=True)
        
        assignments = []
        for i, task in enumerate(sorted_tasks):
            if i < len(sorted_employees):
                assignments.append((task, sorted_employees[i]))
                
        return assignments
        
    def _fair_sharing_schedule(self, 
                             tasks: List[Task], 
                             employees: List[VirtualEmployee]) -> List[Tuple[Task, VirtualEmployee]]:
        """公平共享调度"""
        # 计算每个员工应分配的任务数
        tasks_per_employee = len(tasks) // len(employees)
        remainder = len(tasks) % len(employees)
        
        assignments = []
        task_index = 0
        
        for i, employee in enumerate(employees):
            num_tasks = tasks_per_employee + (1 if i < remainder else 0)
            
            for j in range(num_tasks):
                if task_index < len(tasks):
                    assignments.append((tasks[task_index], employee))
                    task_index += 1
                    
        return assignments
        
    def _deadline_aware_schedule(self, 
                               tasks: List[Task], 
                               employees: List[VirtualEmployee]) -> List[Tuple[Task, VirtualEmployee]]:
        """截止时间感知调度"""
        # 按截止时间排序
        sorted_tasks = sorted(tasks, 
                            key=lambda t: t.metadata.get("deadline", datetime.max))
        
        assignments = []
        employee_availability = {emp.id: 0 for emp in employees}
        
        for task in sorted_tasks:
            # 找到最早可用的员工
            best_employee = min(employees, 
                              key=lambda e: employee_availability[e.id])
            
            assignments.append((task, best_employee))
            employee_availability[best_employee.id] += task.estimated_duration
            
        return assignments
        
    async def predict_scheduling_conflicts(self, 
                                         tasks: List[Task], 
                                         employees: List[VirtualEmployee]) -> List[Dict[str, Any]]:
        """预测调度冲突"""
        conflicts = []
        
        # 检查资源冲突
        total_workload = sum(t.estimated_duration for t in tasks)
        total_capacity = sum(e.max_workload * 3600 for e in employees)  # 转换为秒
        
        if total_workload > total_capacity:
            conflicts.append({
                "type": "resource_overload",
                "severity": "high",
                "description": f"Total workload ({total_workload}s) exceeds capacity ({total_capacity}s)",
                "suggested_action": "Add more employees or extend deadlines"
            })
            
        # 检查截止时间冲突
        deadline_tasks = [t for t in tasks if "deadline" in t.metadata]
        for task in deadline_tasks:
            deadline = task.metadata["deadline"]
            estimated_completion = datetime.utcnow() + timedelta(seconds=task.estimated_duration)
            
            if estimated_completion > deadline:
                conflicts.append({
                    "type": "deadline_conflict",
                    "severity": "high",
                    "task_id": task.id,
                    "description": f"Task {task.name} cannot meet deadline",
                    "suggested_action": "Reassign to more skilled employee or split task"
                })
                
        return conflicts
        
    async def get_employee_schedule(self, 
                                  employee: VirtualEmployee,
                                  days: int = 7) -> List[Dict[str, Any]]:
        """获取员工日程安排"""
        schedule = []
        
        # 获取该员工相关的调度决策
        employee_decisions = [d for d in self.scheduling_history 
                            if d.employee_id == employee.id]
        
        for decision in employee_decisions[-days:]:
            schedule.append({
                "task_id": decision.task_id,
                "scheduled_time": decision.scheduled_time.isoformat(),
                "estimated_completion": decision.estimated_completion.isoformat(),
                "reason": decision.reason
            })
            
        return schedule
        
    async def simulate_scheduling_scenarios(self, 
                                          tasks: List[Task], 
                                          employees: List[VirtualEmployee]) -> Dict[str, Any]:
        """模拟调度场景"""
        scenarios = {}
        
        for algorithm in SchedulingAlgorithm:
            # 临时切换算法
            original_algorithm = self.current_algorithm
            self.current_algorithm = algorithm
            
            # 生成调度方案
            assignments = self._apply_scheduling_algorithm(tasks, employees)
            
            # 计算场景指标
            total_time = sum(t.estimated_duration for t, _ in assignments)
            avg_completion = total_time / len(assignments) if assignments else 0
            
            scenarios[algorithm.value] = {
                "assignments": len(assignments),
                "total_time": total_time,
                "average_completion_time": avg_completion,
                "algorithm": algorithm.value
            }
            
            # 恢复原始算法
            self.current_algorithm = original_algorithm
            
        return scenarios