#!/usr/bin/env python3
"""
CyberCorp AI员工模拟接口
为CyberCorp AI员工系统提供基础模拟接口和通信协议
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from pydantic import BaseModel
import logging

class EmployeeStatus(Enum):
    """员工状态枚举"""
    IDLE = "idle"                    # 空闲
    WORKING = "working"              # 工作中
    PAUSED = "paused"                # 暂停
    ERROR = "error"                  # 错误状态
    OFFLINE = "offline"              # 离线

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"              # 待执行
    ASSIGNED = "assigned"            # 已分配
    IN_PROGRESS = "in_progress"      # 执行中
    COMPLETED = "completed"          # 已完成
    FAILED = "failed"                # 失败
    CANCELLED = "cancelled"          # 已取消

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

@dataclass
class Task:
    """任务数据结构"""
    id: str
    title: str
    description: str
    priority: TaskPriority
    estimated_duration: int  # 预估执行时间（秒）
    created_at: datetime
    assigned_to: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 转换枚举和日期时间
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data

@dataclass 
class Employee:
    """AI员工数据结构"""
    id: str
    name: str
    role: str
    capabilities: List[str]
    status: EmployeeStatus
    current_task: Optional[str] = None
    created_at: datetime = None
    last_activity: datetime = None
    performance_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()
        if self.performance_metrics is None:
            self.performance_metrics = {
                "tasks_completed": 0,
                "success_rate": 1.0,
                "avg_completion_time": 0,
                "efficiency_score": 1.0
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['last_activity'] = self.last_activity.isoformat() if self.last_activity else None
        return data

class EmployeeSimulator:
    """AI员工模拟器"""
    
    def __init__(self):
        self.employees: Dict[str, Employee] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.assignment_callbacks: List[Callable] = []
        
        # 创建一些默认员工
        self._create_default_employees()
    
    def _create_default_employees(self):
        """创建默认AI员工"""
        default_employees = [
            {
                "id": "emp_001",
                "name": "Alice",
                "role": "Developer",
                "capabilities": ["coding", "debugging", "testing", "code_review"]
            },
            {
                "id": "emp_002", 
                "name": "Bob",
                "role": "Analyst",
                "capabilities": ["data_analysis", "reporting", "research", "documentation"]
            },
            {
                "id": "emp_003",
                "name": "Carol",
                "role": "Designer", 
                "capabilities": ["ui_design", "ux_design", "prototyping", "graphics"]
            },
            {
                "id": "emp_004",
                "name": "David",
                "role": "QA Engineer",
                "capabilities": ["testing", "automation", "quality_assurance", "bug_tracking"]
            }
        ]
        
        for emp_data in default_employees:
            employee = Employee(
                id=emp_data["id"],
                name=emp_data["name"],
                role=emp_data["role"],
                capabilities=emp_data["capabilities"],
                status=EmployeeStatus.IDLE
            )
            self.employees[employee.id] = employee
            self.logger.info(f"创建默认员工: {employee.name} ({employee.role})")
    
    async def start_simulation(self):
        """启动员工模拟"""
        self.is_running = True
        self.logger.info("启动AI员工模拟系统")
        
        # 启动任务分配循环
        asyncio.create_task(self._task_assignment_loop())
        
        # 启动员工状态更新循环
        asyncio.create_task(self._employee_status_loop())
        
        # 启动任务执行模拟循环
        asyncio.create_task(self._task_execution_loop())
    
    async def stop_simulation(self):
        """停止员工模拟"""
        self.is_running = False
        self.logger.info("停止AI员工模拟系统")
    
    async def _task_assignment_loop(self):
        """任务分配循环"""
        while self.is_running:
            try:
                await self._assign_pending_tasks()
                await asyncio.sleep(2)  # 每2秒检查一次
            except Exception as e:
                self.logger.error(f"任务分配循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _employee_status_loop(self):
        """员工状态更新循环"""
        while self.is_running:
            try:
                await self._update_employee_status()
                await asyncio.sleep(5)  # 每5秒更新一次
            except Exception as e:
                self.logger.error(f"员工状态更新循环错误: {e}")
                await asyncio.sleep(10)
    
    async def _task_execution_loop(self):
        """任务执行模拟循环"""
        while self.is_running:
            try:
                await self._simulate_task_progress()
                await asyncio.sleep(3)  # 每3秒更新任务进度
            except Exception as e:
                self.logger.error(f"任务执行模拟循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _assign_pending_tasks(self):
        """分配待执行任务"""
        pending_tasks = [task for task in self.tasks.values() 
                        if task.status == TaskStatus.PENDING]
        
        if not pending_tasks:
            return
        
        # 按优先级排序
        pending_tasks.sort(key=lambda t: t.priority.value, reverse=True)
        
        for task in pending_tasks:
            employee = self._find_suitable_employee(task)
            if employee:
                await self._assign_task(task.id, employee.id)
    
    def _find_suitable_employee(self, task: Task) -> Optional[Employee]:
        """找到合适的员工执行任务"""
        available_employees = [emp for emp in self.employees.values() 
                              if emp.status == EmployeeStatus.IDLE]
        
        if not available_employees:
            return None
        
        # 简单的匹配逻辑：根据角色匹配
        role_mapping = {
            "coding": ["Developer"],
            "testing": ["QA Engineer", "Developer"],
            "design": ["Designer"],
            "analysis": ["Analyst"],
            "documentation": ["Analyst", "Developer"]
        }
        
        # 根据任务描述推断需要的技能
        task_keywords = task.description.lower()
        suitable_employees = []
        
        for keyword, roles in role_mapping.items():
            if keyword in task_keywords:
                suitable_employees.extend([emp for emp in available_employees 
                                         if emp.role in roles])
        
        if suitable_employees:
            # 选择效率分数最高的员工
            return max(suitable_employees, 
                      key=lambda e: e.performance_metrics["efficiency_score"])
        
        # 如果没有特别匹配的，返回第一个可用员工
        return available_employees[0] if available_employees else None
    
    async def _assign_task(self, task_id: str, employee_id: str):
        """分配任务给员工"""
        task = self.tasks.get(task_id)
        employee = self.employees.get(employee_id)
        
        if not task or not employee:
            return
        
        task.assigned_to = employee_id
        task.status = TaskStatus.ASSIGNED
        task.started_at = datetime.now()
        
        employee.current_task = task_id
        employee.status = EmployeeStatus.WORKING
        employee.last_activity = datetime.now()
        
        self.logger.info(f"任务 {task.title} 分配给员工 {employee.name}")
        
        # 调用回调函数
        for callback in self.assignment_callbacks:
            try:
                await callback(task, employee)
            except Exception as e:
                self.logger.error(f"任务分配回调错误: {e}")
    
    async def _update_employee_status(self):
        """更新员工状态"""
        for employee in self.employees.values():
            # 模拟员工状态变化
            if employee.status == EmployeeStatus.WORKING:
                # 检查是否有当前任务
                if not employee.current_task or employee.current_task not in self.tasks:
                    employee.status = EmployeeStatus.IDLE
                    employee.current_task = None
                    employee.last_activity = datetime.now()
    
    async def _simulate_task_progress(self):
        """模拟任务执行进度"""
        for task in self.tasks.values():
            if task.status == TaskStatus.ASSIGNED:
                # 开始执行任务
                task.status = TaskStatus.IN_PROGRESS
                task.progress = 0.1
                continue
            
            if task.status == TaskStatus.IN_PROGRESS:
                # 模拟进度更新
                progress_increment = 0.1 + (0.05 * (task.priority.value / 5))
                task.progress = min(1.0, task.progress + progress_increment)
                
                # 检查是否完成
                if task.progress >= 1.0:
                    await self._complete_task(task.id)
    
    async def _complete_task(self, task_id: str):
        """完成任务"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        task.completed_at = datetime.now()
        task.result = {
            "status": "success",
            "message": f"任务 {task.title} 已完成",
            "completion_time": (task.completed_at - task.started_at).total_seconds()
        }
        
        # 更新员工状态
        if task.assigned_to:
            employee = self.employees.get(task.assigned_to)
            if employee:
                employee.status = EmployeeStatus.IDLE
                employee.current_task = None
                employee.last_activity = datetime.now()
                
                # 更新性能指标
                employee.performance_metrics["tasks_completed"] += 1
                completion_time = (task.completed_at - task.started_at).total_seconds()
                avg_time = employee.performance_metrics["avg_completion_time"]
                tasks_count = employee.performance_metrics["tasks_completed"]
                employee.performance_metrics["avg_completion_time"] = (
                    (avg_time * (tasks_count - 1) + completion_time) / tasks_count
                )
        
        self.logger.info(f"任务完成: {task.title}")
    
    # 公共API方法
    
    def add_employee(self, name: str, role: str, capabilities: List[str]) -> str:
        """添加新员工"""
        employee_id = f"emp_{uuid.uuid4().hex[:8]}"
        employee = Employee(
            id=employee_id,
            name=name,
            role=role,
            capabilities=capabilities,
            status=EmployeeStatus.IDLE
        )
        self.employees[employee_id] = employee
        self.logger.info(f"添加新员工: {name} ({role})")
        return employee_id
    
    def create_task(self, title: str, description: str, 
                   priority: TaskPriority = TaskPriority.NORMAL,
                   estimated_duration: int = 3600) -> str:
        """创建新任务"""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            estimated_duration=estimated_duration,
            created_at=datetime.now()
        )
        self.tasks[task_id] = task
        self.task_queue.append(task_id)
        self.logger.info(f"创建新任务: {title}")
        return task_id
    
    def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """获取员工信息"""
        employee = self.employees.get(employee_id)
        return employee.to_dict() if employee else None
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        task = self.tasks.get(task_id)
        return task.to_dict() if task else None
    
    def list_employees(self, status: Optional[EmployeeStatus] = None) -> List[Dict[str, Any]]:
        """列出员工"""
        employees = self.employees.values()
        if status:
            employees = [emp for emp in employees if emp.status == status]
        return [emp.to_dict() for emp in employees]
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Dict[str, Any]]:
        """列出任务"""
        tasks = self.tasks.values()
        if status:
            tasks = [task for task in tasks if task.status == status]
        return [task.to_dict() for task in tasks]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        total_employees = len(self.employees)
        active_employees = len([emp for emp in self.employees.values() 
                               if emp.status == EmployeeStatus.WORKING])
        
        total_tasks = len(self.tasks)
        completed_tasks = len([task for task in self.tasks.values() 
                              if task.status == TaskStatus.COMPLETED])
        
        return {
            "employees": {
                "total": total_employees,
                "active": active_employees,
                "idle": total_employees - active_employees
            },
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "in_progress": len([task for task in self.tasks.values() 
                                  if task.status == TaskStatus.IN_PROGRESS]),
                "pending": len([task for task in self.tasks.values() 
                              if task.status == TaskStatus.PENDING])
            },
            "performance": {
                "completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
                "avg_efficiency": sum(emp.performance_metrics["efficiency_score"] 
                                    for emp in self.employees.values()) / total_employees
                                    if total_employees > 0 else 0
            }
        }
    
    def add_assignment_callback(self, callback: Callable):
        """添加任务分配回调"""
        self.assignment_callbacks.append(callback)

# 全局员工模拟器实例
employee_simulator = EmployeeSimulator()

# 便捷函数
async def init_employee_system():
    """初始化员工系统"""
    await employee_simulator.start_simulation()

async def shutdown_employee_system():
    """关闭员工系统"""
    await employee_simulator.stop_simulation()

def get_simulator() -> EmployeeSimulator:
    """获取员工模拟器实例"""
    return employee_simulator 