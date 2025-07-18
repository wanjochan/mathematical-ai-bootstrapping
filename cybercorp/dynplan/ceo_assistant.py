"""总裁智能助理 - 高级决策与任务委派"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .employee_manager import EmployeeManager, EmployeeRole, VirtualEmployee
from .task_manager import TaskManager, Task, TaskPriority, TaskStatus
from .dynamic_planning_engine import DynamicPlanningEngine


class DecisionType(Enum):
    """决策类型"""
    STRATEGIC = "strategic"
    TACTICAL = "tactical"
    OPERATIONAL = "operational"
    CRISIS = "crisis"


@dataclass
class StrategicDecision:
    """战略决策"""
    id: str
    type: DecisionType
    title: str
    description: str
    priority: TaskPriority
    estimated_impact: float
    required_resources: List[str]
    timeline: timedelta
    created_at: datetime
    approved: bool = False
    executed: bool = False


class CEOAssistant:
    """总裁智能助理"""
    
    def __init__(self, employee_manager: EmployeeManager, task_manager: TaskManager, planning_engine: DynamicPlanningEngine):
        self.logger = logging.getLogger(__name__)
        self.employee_manager = employee_manager
        self.task_manager = task_manager
        self.planning_engine = planning_engine
        
        self.strategic_decisions: List[StrategicDecision] = []
        self.decision_history: List[Dict[str, Any]] = []
        
    async def initialize(self):
        """初始化总裁助理"""
        self.logger.info("Initializing CEO Assistant...")
        
        # 初始化战略决策列表
        self.strategic_decisions = []
        self.decision_history = []
        
        self.logger.info("CEO Assistant initialized")
        
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up CEO Assistant...")
        
        self.strategic_decisions.clear()
        self.decision_history.clear()
        
        self.logger.info("CEO Assistant cleaned up")
        
    async def analyze_business_situation(self) -> Dict[str, Any]:
        """分析业务状况"""
        # 获取当前业务数据
        employee_stats = await self.employee_manager.get_employee_stats()
        task_stats = await self.task_manager.get_task_queue_status()
        
        # 分析关键指标
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "employee_utilization": employee_stats.get("utilization_rate", 0),
            "task_completion_rate": task_stats.get("completed_tasks", 0) / max(task_stats.get("total_tasks", 1), 1),
            "pending_tasks": task_stats.get("pending_tasks", 0),
            "critical_tasks": task_stats.get("critical_tasks", 0),
            "bottlenecks": await self._identify_bottlenecks(),
            "opportunities": await self._identify_opportunities()
        }
        
        self.logger.info(f"Business situation analyzed: {analysis}")
        return analysis
        
    async def make_strategic_decision(self, situation: Dict[str, Any]) -> Optional[StrategicDecision]:
        """制定战略决策"""
        # 基于业务状况制定决策
        if situation["pending_tasks"] > 50:
            decision = StrategicDecision(
                id=f"strategic_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                type=DecisionType.STRATEGIC,
                title="扩大团队规模",
                description="当前任务积压严重，需要增加人力资源",
                priority=TaskPriority.CRITICAL,
                estimated_impact=0.8,
                required_resources=["hr_manager", "recruitment_specialist"],
                timeline=timedelta(days=7),
                created_at=datetime.utcnow()
            )
            self.strategic_decisions.append(decision)
            return decision
            
        elif situation["employee_utilization"] < 0.3:
            decision = StrategicDecision(
                id=f"strategic_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                type=DecisionType.STRATEGIC,
                title="优化资源配置",
                description="员工利用率过低，需要重新分配任务",
                priority=TaskPriority.HIGH,
                estimated_impact=0.6,
                required_resources=["operations_manager", "team_leads"],
                timeline=timedelta(days=3),
                created_at=datetime.utcnow()
            )
            self.strategic_decisions.append(decision)
            return decision
            
        return None
        
    async def delegate_task(self, task: Task, employee: VirtualEmployee) -> bool:
        """委派任务给员工"""
        try:
            # 检查员工是否适合该任务
            if not await self._check_employee_suitability(task, employee):
                self.logger.warning(f"Employee {employee.id} not suitable for task {task.id}")
                return False
                
            # 委派任务
            task.assigned_employee = employee.id
            employee.current_task = task.id
            employee.status = "working"
            
            self.logger.info(f"Task {task.id} delegated to employee {employee.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error delegating task: {e}")
            return False
            
    async def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """优先级排序任务"""
        # 使用AI算法进行智能排序
        sorted_tasks = sorted(tasks, key=lambda t: (
            t.priority.value,
            -t.estimated_duration,
            len(t.dependencies)
        ))
        
        return sorted_tasks
        
    async def monitor_employee_performance(self) -> Dict[str, Any]:
        """监控员工表现"""
        employees = await self.employee_manager.get_all_employees()
        performance_data = {}
        
        for employee in employees:
            tasks = await self.task_manager.get_tasks_by_employee(employee.id)
            completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
            
            performance_data[employee.id] = {
                "name": employee.name,
                "role": employee.role.value,
                "total_tasks": len(tasks),
                "completed_tasks": len(completed_tasks),
                "success_rate": len(completed_tasks) / max(len(tasks), 1),
                "average_completion_time": await self._calculate_average_completion_time(completed_tasks)
            }
            
        return performance_data
        
    async def generate_work_report(self) -> Dict[str, Any]:
        """生成工作报告"""
        situation = await self.analyze_business_situation()
        performance = await self.monitor_employee_performance()
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "business_situation": situation,
            "employee_performance": performance,
            "strategic_decisions": len(self.strategic_decisions),
            "recent_decisions": self.strategic_decisions[-5:] if self.strategic_decisions else []
        }
        
        return report
        
    async def _identify_bottlenecks(self) -> List[str]:
        """识别瓶颈"""
        bottlenecks = []
        
        # 检查任务队列
        queue_length = await self.task_manager.get_task_queue_length()
        if queue_length > 20:
            bottlenecks.append("任务队列积压")
            
        # 检查员工负载
        employees = await self.employee_manager.get_all_employees()
        overloaded_employees = [e for e in employees if e.workload > 0.8]
        if overloaded_employees:
            bottlenecks.append("员工负载过重")
            
        return bottlenecks
        
    async def _identify_opportunities(self) -> List[str]:
        """识别机会"""
        opportunities = []
        
        # 检查低负载员工
        employees = await self.employee_manager.get_all_employees()
        underutilized_employees = [e for e in employees if e.workload < 0.3]
        if underutilized_employees:
            opportunities.append("有员工可承担更多任务")
            
        return opportunities
        
    async def _check_employee_suitability(self, task: Task, employee: VirtualEmployee) -> bool:
        """检查员工是否适合任务"""
        # 检查角色匹配
        role_suitable = False
        if task.name.startswith("财务"):
            role_suitable = employee.role == EmployeeRole.FINANCE
        elif task.name.startswith("技术"):
            role_suitable = employee.role == EmployeeRole.DEVELOPER
        elif task.name.startswith("市场"):
            role_suitable = employee.role == EmployeeRole.MARKETING
        elif task.name.startswith("人事"):
            role_suitable = employee.role == EmployeeRole.HR
        else:
            role_suitable = True
            
        # 检查工作负载
        workload_ok = employee.workload < 0.8
        
        return role_suitable and workload_ok
        
    async def _calculate_average_completion_time(self, tasks: List[Task]) -> float:
        """计算平均完成时间"""
        if not tasks:
            return 0.0
            
        total_time = 0
        for task in tasks:
            if task.completed_at and task.started_at:
                total_time += (task.completed_at - task.started_at).total_seconds()
                
        return total_time / len(tasks) if tasks else 0.0
        
    async def handle_crisis(self, crisis_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """处理危机情况"""
        self.logger.critical(f"Crisis detected: {crisis_type}")
        
        # 创建危机处理任务
        crisis_task = Task(
            id=f"crisis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            name=f"危机处理: {crisis_type}",
            description=f"紧急处理{crisis_type}危机",
            priority=TaskPriority.CRITICAL,
            status=TaskStatus.PENDING,
            estimated_duration=3600  # 1小时
        )
        
        # 立即委派给最高优先级员工
        available_employees = await self.employee_manager.get_available_employees()
        if available_employees:
            best_employee = max(available_employees, key=lambda e: e.skill_level)
            await self.delegate_task(crisis_task, best_employee)
            
        return {
            "crisis_type": crisis_type,
            "task_id": crisis_task.id,
            "assigned_employee": best_employee.id if available_employees else None,
            "response_time": datetime.utcnow().isoformat()
        }