"""动态规划引擎 - 核心任务分解与智能调度"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .task_manager import Task, TaskStatus, TaskPriority
from .employee_manager import VirtualEmployee, EmployeeRole, EmployeeManager


class PlanningStrategy(Enum):
    """规划策略"""
    PRIORITY_FIRST = "priority_first"
    RESOURCE_FIRST = "resource_first"
    DEADLINE_FIRST = "deadline_first"
    BALANCED = "balanced"


@dataclass
class PlanningContext:
    """规划上下文"""
    current_tasks: List[Task]
    available_employees: List[VirtualEmployee]
    business_goals: Dict[str, Any]
    constraints: Dict[str, Any]
    historical_data: Dict[str, Any]


class DynamicPlanningEngine:
    """动态规划引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.planning_history: List[Dict[str, Any]] = []
        self.current_strategy = PlanningStrategy.BALANCED
        self.learning_rate = 0.1
        
    async def initialize(self):
        """初始化引擎"""
        self.logger.info("Initializing Dynamic Planning Engine...")
        self.planning_history.clear()
        self.logger.info("Dynamic Planning Engine initialized")
        
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up Dynamic Planning Engine...")
        self.planning_history.clear()
        self.logger.info("Dynamic Planning Engine cleaned up")
        
    async def plan_tasks(self, 
                        tasks: List[Task], 
                        employees: List[VirtualEmployee],
                        strategy: PlanningStrategy = None) -> Dict[str, Any]:
        """智能任务规划"""
        if strategy is None:
            strategy = self.current_strategy
            
        self.logger.info(f"Planning {len(tasks)} tasks with {len(employees)} employees using {strategy.value}")
        
        # 构建规划上下文
        context = PlanningContext(
            current_tasks=tasks,
            available_employees=employees,
            business_goals={},
            constraints={},
            historical_data=self._get_historical_data()
        )
        
        # 根据策略选择规划算法
        if strategy == PlanningStrategy.PRIORITY_FIRST:
            plan = await self._priority_first_planning(context)
        elif strategy == PlanningStrategy.RESOURCE_FIRST:
            plan = await self._resource_first_planning(context)
        elif strategy == PlanningStrategy.DEADLINE_FIRST:
            plan = await self._deadline_first_planning(context)
        else:
            plan = await self._balanced_planning(context)
            
        # 记录规划历史
        self._record_planning_history(plan, strategy)
        
        return plan
        
    async def _priority_first_planning(self, context: PlanningContext) -> Dict[str, Any]:
        """优先级优先规划"""
        tasks = sorted(context.current_tasks, 
                      key=lambda t: (t.priority.value, -t.estimated_duration))
        
        assignments = []
        employee_workloads = {emp.id: 0 for emp in context.available_employees}
        
        for task in tasks:
            best_employee = self._find_best_employee_for_task(
                task, context.available_employees, employee_workloads)
            
            if best_employee:
                assignments.append({
                    "task_id": task.id,
                    "employee_id": best_employee.id,
                    "estimated_completion": self._estimate_completion_time(task, best_employee),
                    "confidence": self._calculate_confidence(task, best_employee)
                })
                employee_workloads[best_employee.id] += task.estimated_duration
                
        return {
            "strategy": "priority_first",
            "assignments": assignments,
            "total_tasks": len(tasks),
            "assigned_tasks": len(assignments),
            "utilization_rate": self._calculate_utilization_rate(employee_workloads)
        }
        
    async def _resource_first_planning(self, context: PlanningContext) -> Dict[str, Any]:
        """资源优先规划"""
        # 按员工技能匹配度排序
        assignments = []
        task_queue = context.current_tasks.copy()
        employee_availability = {emp.id: emp.max_workload for emp in context.available_employees}
        
        for employee in context.available_employees:
            available_time = employee_availability[employee.id]
            
            # 找到最适合该员工的任务
            suitable_tasks = [t for t in task_queue 
                            if self._is_suitable_for_employee(t, employee)]
            
            for task in suitable_tasks:
                if available_time >= task.estimated_duration:
                    assignments.append({
                        "task_id": task.id,
                        "employee_id": employee.id,
                        "estimated_completion": self._estimate_completion_time(task, employee),
                        "confidence": self._calculate_confidence(task, employee)
                    })
                    available_time -= task.estimated_duration
                    task_queue.remove(task)
                    
        return {
            "strategy": "resource_first",
            "assignments": assignments,
            "total_tasks": len(context.current_tasks),
            "assigned_tasks": len(assignments),
            "utilization_rate": self._calculate_utilization_rate(employee_availability)
        }
        
    async def _deadline_first_planning(self, context: PlanningContext) -> Dict[str, Any]:
        """截止时间优先规划"""
        # 按紧急程度排序
        tasks = sorted(context.current_tasks, 
                      key=lambda t: (t.metadata.get("deadline", datetime.max), t.priority.value))
        
        assignments = []
        employee_schedules = {emp.id: [] for emp in context.available_employees}
        
        for task in tasks:
            best_employee = self._find_employee_for_deadline(
                task, context.available_employees, employee_schedules)
            
            if best_employee:
                start_time = self._calculate_earliest_start_time(
                    best_employee, employee_schedules[best_employee.id])
                
                assignments.append({
                    "task_id": task.id,
                    "employee_id": best_employee.id,
                    "start_time": start_time,
                    "estimated_completion": start_time + timedelta(seconds=task.estimated_duration),
                    "confidence": self._calculate_confidence(task, best_employee)
                })
                
                employee_schedules[best_employee.id].append({
                    "task": task,
                    "start": start_time,
                    "end": start_time + timedelta(seconds=task.estimated_duration)
                })
                
        return {
            "strategy": "deadline_first",
            "assignments": assignments,
            "total_tasks": len(tasks),
            "assigned_tasks": len(assignments),
            "utilization_rate": self._calculate_schedule_utilization(employee_schedules)
        }
        
    async def _balanced_planning(self, context: PlanningContext) -> Dict[str, Any]:
        """平衡规划"""
        # 综合考虑优先级、资源匹配度和截止时间
        assignments = []
        employee_workloads = {emp.id: 0 for emp in context.available_employees}
        
        # 计算每个任务的综合评分
        task_scores = {}
        for task in context.current_tasks:
            scores = []
            for employee in context.available_employees:
                score = self._calculate_balanced_score(task, employee, employee_workloads[employee.id])
                scores.append((employee, score))
            
            # 选择最佳匹配
            if scores:
                best_employee, best_score = max(scores, key=lambda x: x[1])
                if best_score > 0.5:  # 阈值
                    assignments.append({
                        "task_id": task.id,
                        "employee_id": best_employee.id,
                        "score": best_score,
                        "estimated_completion": self._estimate_completion_time(task, best_employee),
                        "confidence": self._calculate_confidence(task, best_employee)
                    })
                    employee_workloads[best_employee.id] += task.estimated_duration
                    
        return {
            "strategy": "balanced",
            "assignments": assignments,
            "total_tasks": len(context.current_tasks),
            "assigned_tasks": len(assignments),
            "utilization_rate": self._calculate_utilization_rate(employee_workloads)
        }
        
    def _find_best_employee_for_task(self, 
                                   task: Task, 
                                   employees: List[VirtualEmployee],
                                   workloads: Dict[str, float]) -> Optional[VirtualEmployee]:
        """为任务找到最佳员工"""
        suitable_employees = []
        
        for employee in employees:
            # 检查角色匹配
            if not self._is_role_suitable(task, employee.role):
                continue
                
            # 检查工作负载
            if workloads[employee.id] >= employee.max_workload * 3600:  # 转换为秒
                continue
                
            # 计算匹配度
            score = self._calculate_employee_task_match(task, employee)
            suitable_employees.append((employee, score))
            
        if not suitable_employees:
            return None
            
        # 选择匹配度最高的员工
        return max(suitable_employees, key=lambda x: x[1])[0]
        
    def _is_role_suitable(self, task: Task, role: EmployeeRole) -> bool:
        """检查角色是否适合任务"""
        # 简单的角色匹配逻辑
        role_mapping = {
            "development": [EmployeeRole.DEVELOPER],
            "finance": [EmployeeRole.FINANCE],
            "marketing": [EmployeeRole.MARKETING],
            "hr": [EmployeeRole.HR],
            "management": [EmployeeRole.MANAGER]
        }
        
        task_type = task.metadata.get("type", "general")
        suitable_roles = role_mapping.get(task_type, list(EmployeeRole))
        
        return role in suitable_roles
        
    def _calculate_employee_task_match(self, task: Task, employee: VirtualEmployee) -> float:
        """计算员工与任务的匹配度"""
        # 基础匹配度
        base_score = 0.5
        
        # 技能匹配
        skill_bonus = employee.skill_level * 0.3
        
        # 工作负载考虑
        workload_penalty = 0.1 if employee.workload > 0.7 else 0
        
        # 历史表现
        performance_bonus = 0.1 if employee.performance_history else 0
        
        return base_score + skill_bonus - workload_penalty + performance_bonus
        
    def _calculate_confidence(self, task: Task, employee: VirtualEmployee) -> float:
        """计算任务完成信心度"""
        # 基于员工技能和历史表现
        confidence = employee.skill_level
        
        # 考虑任务复杂度
        complexity_factor = min(1.0, 3600 / max(task.estimated_duration, 3600))
        
        return confidence * complexity_factor
        
    def _estimate_completion_time(self, task: Task, employee: VirtualEmployee) -> datetime:
        """估计任务完成时间"""
        base_time = task.estimated_duration
        efficiency_factor = 1.0 - (employee.skill_level * 0.3)  # 技能越高，效率越高
        estimated_seconds = base_time * efficiency_factor
        
        return datetime.utcnow() + timedelta(seconds=estimated_seconds)
        
    def _calculate_utilization_rate(self, workloads: Dict[str, float]) -> float:
        """计算资源利用率"""
        if not workloads:
            return 0.0
            
        total_workload = sum(workloads.values())
        max_workload = len(workloads) * 3600  # 假设每人每天8小时
        
        return min(1.0, total_workload / max_workload)
        
    def _calculate_schedule_utilization(self, schedules: Dict[str, List[Dict]]) -> float:
        """计算调度利用率"""
        total_allocated = 0
        total_available = len(schedules) * 8 * 3600  # 8小时工作制
        
        for employee_schedule in schedules.values():
            for slot in employee_schedule:
                total_allocated += slot["task"].estimated_duration
                
        return min(1.0, total_allocated / total_available)
        
    def _calculate_balanced_score(self, task: Task, employee: VirtualEmployee, current_workload: float) -> float:
        """计算平衡评分"""
        # 优先级权重
        priority_weight = task.priority.value / 4.0
        
        # 技能匹配权重
        skill_weight = employee.skill_level
        
        # 工作负载权重
        workload_weight = 1.0 - (current_workload / (employee.max_workload * 3600))
        
        # 综合评分
        return (priority_weight * 0.4 + skill_weight * 0.4 + workload_weight * 0.2)
        
    def _get_historical_data(self) -> Dict[str, Any]:
        """获取历史数据"""
        return {
            "planning_history": self.planning_history[-10:],  # 最近10次
            "success_rate": 0.85,  # 模拟数据
            "average_completion_time": 3600  # 模拟数据
        }
        
    def _record_planning_history(self, plan: Dict[str, Any], strategy: PlanningStrategy):
        """记录规划历史"""
        self.planning_history.append({
            "timestamp": datetime.utcnow(),
            "strategy": strategy.value,
            "plan": plan,
            "metrics": {
                "total_tasks": plan.get("total_tasks", 0),
                "assigned_tasks": plan.get("assigned_tasks", 0),
                "utilization_rate": plan.get("utilization_rate", 0)
            }
        })
        
    async def optimize_strategy(self, feedback_data: Dict[str, Any]) -> PlanningStrategy:
        """基于反馈优化策略"""
        # 简单的策略优化逻辑
        if feedback_data.get("success_rate", 0) < 0.7:
            # 成功率低，切换到更保守的策略
            return PlanningStrategy.BALANCED
        elif feedback_data.get("urgent_tasks", 0) > 5:
            # 紧急任务多，使用截止时间优先
            return PlanningStrategy.DEADLINE_FIRST
        elif feedback_data.get("resource_utilization", 0) < 0.5:
            # 资源利用率低，使用资源优先
            return PlanningStrategy.RESOURCE_FIRST
        else:
            # 默认使用平衡策略
            return PlanningStrategy.BALANCED
            
    async def get_planning_insights(self) -> Dict[str, Any]:
        """获取规划洞察"""
        if not self.planning_history:
            return {"message": "No planning history available"}
            
        recent_plans = self.planning_history[-10:]
        
        avg_utilization = sum(p["metrics"]["utilization_rate"] for p in recent_plans) / len(recent_plans)
        avg_assigned = sum(p["metrics"]["assigned_tasks"] for p in recent_plans) / len(recent_plans)
        
        strategy_usage = {}
        for plan in recent_plans:
            strategy = plan["strategy"]
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
            
        return {
            "total_plans": len(self.planning_history),
            "recent_plans": len(recent_plans),
            "average_utilization": avg_utilization,
            "average_assigned_tasks": avg_assigned,
            "strategy_usage": strategy_usage,
            "current_strategy": self.current_strategy.value
        }