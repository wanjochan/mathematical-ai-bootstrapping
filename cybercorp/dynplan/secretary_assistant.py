"""董秘智能助理 - 日常事务管理与协调"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .employee_manager import EmployeeManager, VirtualEmployee
from .task_manager import TaskManager, Task, TaskPriority, TaskStatus
from .ceo_assistant import CEOAssistant


class SecretaryTaskType(Enum):
    """董秘任务类型"""
    SCHEDULING = "scheduling"
    COMMUNICATION = "communication"
    DOCUMENTATION = "documentation"
    COORDINATION = "coordination"
    REPORTING = "reporting"


@dataclass
class Meeting:
    """会议数据结构"""
    id: str
    title: str
    participants: List[str]
    start_time: datetime
    duration: timedelta
    agenda: str
    location: str = "会议室"
    status: str = "scheduled"


@dataclass
class Communication:
    """沟通记录"""
    id: str
    type: str
    sender: str
    recipient: str
    content: str
    timestamp: datetime
    priority: TaskPriority
    status: str = "pending"


class SecretaryAssistant:
    """董秘智能助理"""
    
    def __init__(self, employee_manager: EmployeeManager, task_manager: TaskManager, ceo_assistant: CEOAssistant):
        self.logger = logging.getLogger(__name__)
        self.employee_manager = employee_manager
        self.task_manager = task_manager
        self.ceo_assistant = ceo_assistant
        
        self.meetings: List[Meeting] = []
        self.communications: List[Communication] = []
        self.daily_schedule: List[Dict[str, Any]] = []
        
    async def initialize(self):
        """初始化董秘助理"""
        self.logger.info("Initializing Secretary Assistant...")
        
        # 初始化日程安排
        self.meetings = []
        self.communications = []
        self.daily_schedule = []
        
        self.logger.info("Secretary Assistant initialized")
        
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up Secretary Assistant...")
        
        self.meetings.clear()
        self.communications.clear()
        self.daily_schedule.clear()
        
        self.logger.info("Secretary Assistant cleaned up")
        
    async def schedule_meeting(self, title: str, participants: List[str], 
                             start_time: datetime, duration: timedelta, 
                             agenda: str) -> str:
        """安排会议"""
        meeting_id = f"meeting_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        meeting = Meeting(
            id=meeting_id,
            title=title,
            participants=participants,
            start_time=start_time,
            duration=duration,
            agenda=agenda
        )
        
        self.meetings.append(meeting)
        
        # 创建相关任务
        meeting_task = Task(
            id=f"task_{meeting_id}",
            name=f"会议准备: {title}",
            description=f"准备{title}会议，参与者: {', '.join(participants)}",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            estimated_duration=duration.total_seconds()
        )
        
        await self.task_manager.submit_task(meeting_task)
        
        self.logger.info(f"Meeting scheduled: {meeting_id}")
        return meeting_id
        
    async def send_communication(self, comm_type: str, sender: str, 
                               recipient: str, content: str, 
                               priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        """发送沟通信息"""
        comm_id = f"comm_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        communication = Communication(
            id=comm_id,
            type=comm_type,
            sender=sender,
            recipient=recipient,
            content=content,
            timestamp=datetime.utcnow(),
            priority=priority
        )
        
        self.communications.append(communication)
        
        # 创建沟通任务
        comm_task = Task(
            id=f"task_{comm_id}",
            name=f"沟通处理: {comm_type}",
            description=f"处理{comm_type}沟通，从{sender}到{recipient}",
            priority=priority,
            status=TaskStatus.PENDING,
            estimated_duration=1800  # 30分钟
        )
        
        await self.task_manager.submit_task(comm_task)
        
        self.logger.info(f"Communication sent: {comm_id}")
        return comm_id
        
    async def manage_daily_schedule(self) -> List[Dict[str, Any]]:
        """管理日常日程"""
        today = datetime.utcnow().date()
        
        # 获取今日任务
        all_tasks = await self.task_manager.get_all_tasks()
        today_tasks = [t for t in all_tasks if t.created_at.date() == today]
        
        # 获取今日会议
        today_meetings = [m for m in self.meetings if m.start_time.date() == today]
        
        # 生成日程安排
        schedule = []
        
        # 添加会议
        for meeting in today_meetings:
            schedule.append({
                "type": "meeting",
                "time": meeting.start_time.strftime("%H:%M"),
                "duration": str(meeting.duration),
                "title": meeting.title,
                "participants": meeting.participants,
                "location": meeting.location
            })
            
        # 添加高优先级任务
        high_priority_tasks = [t for t in today_tasks if t.priority == TaskPriority.HIGH]
        for task in high_priority_tasks:
            schedule.append({
                "type": "task",
                "time": "待定",
                "title": task.name,
                "priority": task.priority.value,
                "assigned_to": task.assigned_employee
            })
            
        # 按时间排序
        schedule.sort(key=lambda x: x["time"])
        
        self.daily_schedule = schedule
        return schedule
        
    async def coordinate_team_activities(self) -> Dict[str, Any]:
        """协调团队活动"""
        # 获取所有员工
        employees = await self.employee_manager.get_all_employees()
        
        # 分析团队状态
        team_status = {
            "total_members": len(employees),
            "available_members": len([e for e in employees if e.status == "available"]),
            "busy_members": len([e for e in employees if e.status == "working"]),
            "idle_members": len([e for e in employees if e.status == "idle"]),
            "coordination_needs": []
        }
        
        # 识别需要协调的情况
        for employee in employees:
            if employee.workload > 0.9:
                team_status["coordination_needs"].append({
                    "employee": employee.name,
                    "issue": "工作负载过重",
                    "suggestion": "重新分配任务"
                })
                
        return team_status
        
    async def prepare_daily_report(self) -> Dict[str, Any]:
        """准备日报"""
        # 获取业务数据
        business_data = await self.ceo_assistant.analyze_business_situation()
        
        # 获取团队状态
        team_status = await self.coordinate_team_activities()
        
        # 获取今日任务
        schedule = await self.manage_daily_schedule()
        
        # 生成日报
        report = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "business_overview": business_data,
            "team_status": team_status,
            "daily_schedule": schedule,
            "pending_communications": len([c for c in self.communications if c.status == "pending"]),
            "upcoming_meetings": len([m for m in self.meetings if m.start_time.date() >= datetime.utcnow().date()]),
            "key_metrics": {
                "task_completion_rate": business_data.get("task_completion_rate", 0),
                "employee_utilization": business_data.get("employee_utilization", 0),
                "pending_tasks": business_data.get("pending_tasks", 0)
            }
        }
        
        return report
        
    async def handle_urgent_request(self, request_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """处理紧急请求"""
        self.logger.warning(f"Urgent request received: {request_type}")
        
        # 创建紧急任务
        urgent_task = Task(
            id=f"urgent_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            name=f"紧急处理: {request_type}",
            description=f"紧急处理{request_type}请求",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            estimated_duration=1800  # 30分钟
        )
        
        # 立即委派给可用员工
        available_employees = await self.employee_manager.get_available_employees()
        if available_employees:
            best_employee = min(available_employees, key=lambda e: e.workload)
            await self.ceo_assistant.delegate_task(urgent_task, best_employee)
            
        return {
            "request_type": request_type,
            "task_id": urgent_task.id,
            "assigned_employee": best_employee.id if available_employees else None,
            "response_time": datetime.utcnow().isoformat()
        }
        
    async def manage_documentation(self) -> Dict[str, Any]:
        """管理文档"""
        # 获取所有任务和会议
        all_tasks = await self.task_manager.get_all_tasks()
        all_meetings = self.meetings
        
        # 生成文档摘要
        documentation = {
            "total_tasks": len(all_tasks),
            "completed_tasks": len([t for t in all_tasks if t.status == TaskStatus.COMPLETED]),
            "total_meetings": len(all_meetings),
            "communications": len(self.communications),
            "key_documents": [
                "项目进度报告",
                "会议纪要",
                "团队沟通记录",
                "任务分配记录"
            ]
        }
        
        return documentation
        
    async def send_reminders(self) -> List[Dict[str, Any]]:
        """发送提醒"""
        reminders = []
        now = datetime.utcnow()
        
        # 检查即将开始的会议
        for meeting in self.meetings:
            time_until_meeting = meeting.start_time - now
            if timedelta(minutes=0) < time_until_meeting <= timedelta(minutes=15):
                reminders.append({
                    "type": "meeting_reminder",
                    "meeting": meeting.title,
                    "time": meeting.start_time.strftime("%H:%M"),
                    "participants": meeting.participants
                })
                
        # 检查逾期任务
        overdue_tasks = await self.task_manager.get_tasks_by_status(TaskStatus.PENDING)
        for task in overdue_tasks:
            if task.created_at < now - timedelta(hours=24):
                reminders.append({
                    "type": "task_overdue",
                    "task": task.name,
                    "assigned_to": task.assigned_employee,
                    "overdue_by": str(now - task.created_at)
                })
                
        return reminders
        
    async def optimize_workflow(self) -> Dict[str, Any]:
        """优化工作流程"""
        # 分析当前工作流程
        workflow_analysis = {
            "bottlenecks": await self.ceo_assistant._identify_bottlenecks(),
            "opportunities": await self.ceo_assistant._identify_opportunities(),
            "suggestions": []
        }
        
        # 生成优化建议
        if workflow_analysis["bottlenecks"]:
            workflow_analysis["suggestions"].append("重新分配任务负载")
            
        if workflow_analysis["opportunities"]:
            workflow_analysis["suggestions"].append("利用空闲员工资源")
            
        # 检查沟通效率
        pending_comms = len([c for c in self.communications if c.status == "pending"])
        if pending_comms > 10:
            workflow_analysis["suggestions"].append("优化沟通流程")
            
        return workflow_analysis