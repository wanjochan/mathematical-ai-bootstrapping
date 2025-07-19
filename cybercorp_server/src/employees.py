# src/employees.py - Employee Management Module

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class Employee:
    id: str
    name: str
    role: str
    department: str
    email: str
    phone: Optional[str] = None
    status: str = "active"
    created_at: datetime = None
    updated_at: datetime = None

class EmployeeManager:
    def __init__(self):
        self.employees: Dict[str, Employee] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """初始化示例员工数据"""
        sample_employees = [
            Employee(
                id=str(uuid.uuid4()),
                name="张三",
                role="高级开发工程师",
                department="技术部",
                email="zhangsan@cybercorp.ai",
                phone="13800138001"
            ),
            Employee(
                id=str(uuid.uuid4()),
                name="李四",
                role="产品经理",
                department="产品部",
                email="lisi@cybercorp.ai",
                phone="13800138002"
            ),
            Employee(
                id=str(uuid.uuid4()),
                name="王五",
                role="运维工程师",
                department="运维部",
                email="wangwu@cybercorp.ai",
                phone="13800138003"
            ),
            Employee(
                id=str(uuid.uuid4()),
                name="赵六",
                role="安全分析师",
                department="安全部",
                email="zhaoliu@cybercorp.ai",
                phone="13800138004"
            )
        ]
        
        for emp in sample_employees:
            emp.created_at = datetime.now()
            emp.updated_at = datetime.now()
            self.employees[emp.id] = emp
    
    def get_all_employees(self) -> List[Employee]:
        """获取所有员工"""
        return list(self.employees.values())
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """根据ID获取员工"""
        return self.employees.get(employee_id)
    
    def get_employees_by_department(self, department: str) -> List[Employee]:
        """根据部门获取员工"""
        return [emp for emp in self.employees.values() 
                if emp.department == department]
    
    def get_employees_by_role(self, role: str) -> List[Employee]:
        """根据角色获取员工"""
        return [emp for emp in self.employees.values() 
                if emp.role == role]
    
    def create_employee(self, name: str, role: str, department: str, 
                       email: str, phone: Optional[str] = None) -> Employee:
        """创建新员工"""
        employee = Employee(
            id=str(uuid.uuid4()),
            name=name,
            role=role,
            department=department,
            email=email,
            phone=phone,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.employees[employee.id] = employee
        return employee
    
    def update_employee(self, employee_id: str, **kwargs) -> Optional[Employee]:
        """更新员工信息"""
        employee = self.employees.get(employee_id)
        if not employee:
            return None
        
        for key, value in kwargs.items():
            if hasattr(employee, key) and key != 'id':
                setattr(employee, key, value)
        
        employee.updated_at = datetime.now()
        return employee
    
    def delete_employee(self, employee_id: str) -> bool:
        """删除员工"""
        if employee_id in self.employees:
            del self.employees[employee_id]
            return True
        return False
    
    def get_employee_count(self) -> Dict[str, int]:
        """获取员工统计信息"""
        total = len(self.employees)
        by_department = {}
        by_status = {"active": 0, "inactive": 0}
        
        for emp in self.employees.values():
            if emp.department in by_department:
                by_department[emp.department] += 1
            else:
                by_department[emp.department] = 1
            
            if emp.status in by_status:
                by_status[emp.status] += 1
        
        return {
            "total": total,
            "by_department": by_department,
            "by_status": by_status
        }

# 全局员工管理器实例
employee_manager = EmployeeManager()