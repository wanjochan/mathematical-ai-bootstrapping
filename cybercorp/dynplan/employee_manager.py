"""虚拟员工管理器 - 角色定义与操作系统会话绑定"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class EmployeeRole(Enum):
    """员工角色类型"""
    CEO = "ceo"  # 总裁
    SECRETARY = "secretary"  # 董秘
    DEVELOPER = "developer"  # 开发者
    ANALYST = "analyst"  # 分析师
    OPERATOR = "operator"  # 操作员
    MONITOR = "monitor"  # 监控员


class EmployeeState(Enum):
    """员工状态"""
    IDLE = "idle"
    WORKING = "working"
    BREAK = "break"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class VirtualEmployee:
    """虚拟员工数据结构"""
    id: str
    name: str
    role: EmployeeRole
    state: EmployeeState
    skills: List[str]
    current_task: Optional[str] = None
    session_info: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.performance_metrics:
            self.performance_metrics = {
                "tasks_completed": 0.0,
                "success_rate": 1.0,
                "avg_task_duration": 0.0,
                "efficiency": 1.0
            }


class EmployeeManager:
    """虚拟员工管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.employees: Dict[str, VirtualEmployee] = {}
        self.role_templates: Dict[EmployeeRole, Dict[str, Any]] = {}
        self.session_bindings: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """初始化员工管理器"""
        self.logger.info("Initializing Employee Manager...")
        
        # 初始化角色模板
        await self._initialize_role_templates()
        
        # 创建默认员工
        await self._create_default_employees()
        
        self.logger.info("Employee Manager initialized")
        
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up Employee Manager...")
        
        # 断开所有会话
        for employee_id in list(self.session_bindings.keys()):
            await self._disconnect_session(employee_id)
            
        self.employees.clear()
        self.session_bindings.clear()
        
    async def create_employee(self, name: str, role: EmployeeRole, 
                            skills: List[str] = None) -> VirtualEmployee:
        """创建新员工"""
        employee_id = str(uuid.uuid4())
        
        if skills is None:
            skills = self._get_default_skills(role)
            
        employee = VirtualEmployee(
            id=employee_id,
            name=name,
            role=role,
            state=EmployeeState.IDLE,
            skills=skills
        )
        
        self.employees[employee_id] = employee
        self.logger.info(f"Created employee {name} ({role.value}) with ID {employee_id}")
        
        return employee
        
    async def assign_employee(self, task) -> Optional[VirtualEmployee]:
        """为员工分配任务"""
        # 根据任务需求找到合适的员工
        suitable_employees = await self._find_suitable_employees(task)
        
        if not suitable_employees:
            self.logger.warning(f"No suitable employee found for task {task.id}")
            return None
            
        # 选择最空闲的员工
        selected_employee = min(
            suitable_employees,
            key=lambda e: e.performance_metrics.get("tasks_completed", 0)
        )
        
        # 绑定会话
        session_info = await self._bind_session(selected_employee.id, task)
        if session_info:
            selected_employee.session_info = session_info
            selected_employee.state = EmployeeState.WORKING
            selected_employee.current_task = task.id
            selected_employee.last_activity = datetime.utcnow()
            
            self.logger.info(
                f"Assigned employee {selected_employee.name} to task {task.id}"
            )
            
            return selected_employee
            
        return None
        
    async def release_employee(self, employee_id: str, task_id: str):
        """释放员工"""
        if employee_id not in self.employees:
            return
            
        employee = self.employees[employee_id]
        
        if employee.current_task == task_id:
            employee.current_task = None
            employee.state = EmployeeState.IDLE
            employee.last_activity = datetime.utcnow()
            
            # 更新绩效指标
            await self._update_performance_metrics(employee_id, task_id, success=True)
            
            # 断开会话
            await self._disconnect_session(employee_id)
            
            self.logger.info(f"Released employee {employee.name} from task {task_id}")
            
    async def get_available_count(self) -> int:
        """获取可用员工数量"""
        return len([
            emp for emp in self.employees.values()
            if emp.state in [EmployeeState.IDLE, EmployeeState.BREAK]
        ])
        
    async def get_employee_status(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """获取员工状态"""
        if employee_id not in self.employees:
            return None
            
        employee = self.employees[employee_id]
        return {
            "id": employee.id,
            "name": employee.name,
            "role": employee.role.value,
            "state": employee.state.value,
            "current_task": employee.current_task,
            "skills": employee.skills,
            "performance": employee.performance_metrics,
            "session_info": employee.session_info,
            "last_activity": employee.last_activity.isoformat()
        }
        
    async def get_all_employees(self) -> List[Dict[str, Any]]:
        """获取所有员工状态"""
        return [
            await self.get_employee_status(emp_id)
            for emp_id in self.employees.keys()
        ]
        
    async def update_employee_state(self, employee_id: str, new_state: EmployeeState):
        """更新员工状态"""
        if employee_id not in self.employees:
            return False
            
        employee = self.employees[employee_id]
        old_state = employee.state
        employee.state = new_state
        employee.last_activity = datetime.utcnow()
        
        self.logger.info(
            f"Employee {employee.name} state changed from {old_state.value} to {new_state.value}"
        )
        
        return True
        
    async def get_employees_by_role(self, role: EmployeeRole) -> List[VirtualEmployee]:
        """按角色获取员工"""
        return [
            emp for emp in self.employees.values()
            if emp.role == role
        ]
        
    async def get_system_overview(self) -> Dict[str, Any]:
        """获取系统概览"""
        total_employees = len(self.employees)
        
        role_distribution = {}
        state_distribution = {}
        
        for employee in self.employees.values():
            role = employee.role.value
            state = employee.state.value
            
            role_distribution[role] = role_distribution.get(role, 0) + 1
            state_distribution[state] = state_distribution.get(state, 0) + 1
            
        return {
            "total_employees": total_employees,
            "role_distribution": role_distribution,
            "state_distribution": state_distribution,
            "active_sessions": len(self.session_bindings),
            "idle_employees": len([
                emp for emp in self.employees.values()
                if emp.state == EmployeeState.IDLE
            ])
        }
        
    def _initialize_role_templates(self):
        """初始化角色模板"""
        self.role_templates = {
            EmployeeRole.CEO: {
                "skills": ["decision_making", "strategy", "leadership", "analysis"],
                "max_concurrent_tasks": 3,
                "priority_weight": 1.5
            },
            EmployeeRole.SECRETARY: {
                "skills": ["communication", "scheduling", "documentation", "coordination"],
                "max_concurrent_tasks": 5,
                "priority_weight": 1.3
            },
            EmployeeRole.DEVELOPER: {
                "skills": ["programming", "debugging", "testing", "automation"],
                "max_concurrent_tasks": 2,
                "priority_weight": 1.0
            },
            EmployeeRole.ANALYST: {
                "skills": ["data_analysis", "reporting", "monitoring", "metrics"],
                "max_concurrent_tasks": 3,
                "priority_weight": 1.1
            },
            EmployeeRole.OPERATOR: {
                "skills": ["system_operation", "monitoring", "troubleshooting"],
                "max_concurrent_tasks": 4,
                "priority_weight": 0.9
            },
            EmployeeRole.MONITOR: {
                "skills": ["observation", "alerting", "reporting", "escalation"],
                "max_concurrent_tasks": 6,
                "priority_weight": 0.8
            }
        }
        
    async def _create_default_employees(self):
        """创建默认员工"""
        default_employees = [
            ("Alice", EmployeeRole.CEO),
            ("Bob", EmployeeRole.SECRETARY),
            ("Charlie", EmployeeRole.DEVELOPER),
            ("Diana", EmployeeRole.ANALYST),
            ("Eve", EmployeeRole.OPERATOR),
            ("Frank", EmployeeRole.MONITOR)
        ]
        
        for name, role in default_employees:
            await self.create_employee(name, role)
            
    def _get_default_skills(self, role: EmployeeRole) -> List[str]:
        """获取角色的默认技能"""
        if role in self.role_templates:
            return self.role_templates[role]["skills"]
        return []
        
    async def _find_suitable_employees(self, task) -> List[VirtualEmployee]:
        """找到适合任务的员工"""
        suitable = []
        
        for employee in self.employees.values():
            # 检查状态
            if employee.state not in [EmployeeState.IDLE, EmployeeState.BREAK]:
                continue
                
            # 检查技能匹配
            if hasattr(task, 'required_skills'):
                if not any(skill in employee.skills for skill in task.required_skills):
                    continue
                    
            suitable.append(employee)
            
        return suitable
        
    async def _bind_session(self, employee_id: str, task) -> Dict[str, Any]:
        """绑定操作系统会话"""
        # 模拟会话绑定
        session_info = {
            "session_id": str(uuid.uuid4()),
            "employee_id": employee_id,
            "task_id": task.id,
            "os_session": f"session_{employee_id}_{task.id}",
            "permissions": ["desktop_access", "window_control", "input_simulation"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.session_bindings[employee_id] = session_info
        return session_info
        
    async def _disconnect_session(self, employee_id: str):
        """断开会话"""
        if employee_id in self.session_bindings:
            del self.session_bindings[employee_id]
            
    async def _update_performance_metrics(self, employee_id: str, task_id: str, success: bool):
        """更新绩效指标"""
        if employee_id not in self.employees:
            return
            
        employee = self.employees[employee_id]
        metrics = employee.performance_metrics
        
        # 更新任务完成数
        metrics["tasks_completed"] += 1
        
        # 更新成功率
        total_tasks = metrics["tasks_completed"]
        if success:
            metrics["success_rate"] = (
                (metrics["success_rate"] * (total_tasks - 1) + 1) / total_tasks
            )
        else:
            metrics["success_rate"] = (
                (metrics["success_rate"] * (total_tasks - 1)) / total_tasks
            )