#!/usr/bin/env python3
"""CyberCorp Server - 动态规划系统服务端"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dynplan import (
    DynamicPlanningEngine,
    TaskScheduler,
    EmployeeManager,
    TaskManager,
    CEOAssistant,
    SecretaryAssistant,
    Task,
    TaskPriority,
    TaskStatus,
    EmployeeRole,
    VirtualEmployee
)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI应用
app = FastAPI(
    title="CyberCorp Dynamic Planning Server",
    description="智能动态规划与任务管理系统",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局实例
planning_engine: Optional[DynamicPlanningEngine] = None
task_scheduler: Optional[TaskScheduler] = None
employee_manager: Optional[EmployeeManager] = None
task_manager: Optional[TaskManager] = None
ceo_assistant: Optional[CEOAssistant] = None
secretary_assistant: Optional[SecretaryAssistant] = None

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)
        
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Pydantic模型
class TaskCreate(BaseModel):
    name: str
    description: str
    priority: int = 2
    estimated_duration: float = 3600.0
    dependencies: List[str] = []
    metadata: Dict[str, Any] = {}

class EmployeeCreate(BaseModel):
    name: str
    role: str
    skill_level: float = 0.5
    max_workload: float = 1.0

class StrategicDecisionCreate(BaseModel):
    title: str
    description: str
    priority: int = 3
    estimated_impact: float = 0.5
    required_resources: List[str] = []
    timeline_hours: float = 24.0

class MeetingCreate(BaseModel):
    title: str
    participants: List[str]
    start_time: str
    duration_minutes: int
    agenda: str

# 初始化函数
async def initialize_system():
    """初始化系统组件"""
    global planning_engine, task_scheduler, employee_manager, task_manager
    global ceo_assistant, secretary_assistant
    
    logger.info("Initializing CyberCorp Dynamic Planning System...")
    
    try:
        # 初始化核心组件
        planning_engine = DynamicPlanningEngine()
        task_scheduler = TaskScheduler()
        employee_manager = EmployeeManager()
        task_manager = TaskManager()
        
        # 初始化组件
        await planning_engine.initialize()
        await task_scheduler.initialize()
        await employee_manager.initialize()
        await task_manager.initialize()
        
        # 初始化智能助理
        ceo_assistant = CEOAssistant(employee_manager, task_manager, planning_engine)
        secretary_assistant = SecretaryAssistant(employee_manager, task_manager, ceo_assistant)
        
        await ceo_assistant.initialize()
        await secretary_assistant.initialize()
        
        # 创建初始员工
        await create_initial_employees()
        
        logger.info("CyberCorp Dynamic Planning System initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise

async def create_initial_employees():
    """创建初始员工"""
    initial_employees = [
        {"name": "张三", "role": "developer", "skill_level": 0.8},
        {"name": "李四", "role": "analyst", "skill_level": 0.7},
        {"name": "王五", "role": "operator", "skill_level": 0.6},
        {"name": "赵六", "role": "monitor", "skill_level": 0.5},
        {"name": "钱七", "role": "developer", "skill_level": 0.9},
    ]
    
    for emp_data in initial_employees:
        await employee_manager.create_employee(
            name=emp_data['name'],
            role=EmployeeRole(emp_data['role'])
        )
        
    logger.info(f"Created {len(initial_employees)} initial employees")

# API路由
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    await initialize_system()

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Shutting down CyberCorp Dynamic Planning System...")
    
    if planning_engine:
        await planning_engine.cleanup()
    if task_scheduler:
        await task_scheduler.cleanup()
    if employee_manager:
        await employee_manager.cleanup()
    if task_manager:
        await task_manager.cleanup()
    if ceo_assistant:
        await ceo_assistant.cleanup()
    if secretary_assistant:
        await secretary_assistant.cleanup()

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "CyberCorp Dynamic Planning Server",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "planning_engine": planning_engine is not None,
            "task_scheduler": task_scheduler is not None,
            "employee_manager": employee_manager is not None,
            "task_manager": task_manager is not None,
            "ceo_assistant": ceo_assistant is not None,
            "secretary_assistant": secretary_assistant is not None
        }
    }

# 任务管理API
@app.post("/api/tasks")
async def create_task(task: TaskCreate):
    """创建新任务"""
    try:
        new_task = Task(
            id=f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            name=task.name,
            description=task.description,
            priority=TaskPriority(task.priority),
            status=TaskStatus.PENDING,
            estimated_duration=task.estimated_duration,
            dependencies=task.dependencies,
            metadata=task.metadata
        )
        
        task_id = await task_manager.submit_task(new_task)
        
        # 广播更新
        await manager.broadcast(json.dumps({
            "type": "task_created",
            "task_id": task_id,
            "task_name": task.name
        }))
        
        return {"task_id": task_id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks")
async def get_tasks():
    """获取所有任务"""
    try:
        tasks = await task_manager.get_all_tasks()
        return [
            {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "priority": task.priority.value,
                "status": task.status.value,
                "assigned_employee": task.assigned_employee,
                "estimated_duration": task.estimated_duration,
                "created_at": task.created_at.isoformat()
            }
            for task in tasks
        ]
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """获取特定任务"""
    try:
        task = await task_manager.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        return await task_manager.get_task_status(task_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tasks/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    try:
        success = await task_manager.cancel_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
            
        await manager.broadcast(json.dumps({
            "type": "task_cancelled",
            "task_id": task_id
        }))
        
        return {"status": "cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 员工管理API
@app.post("/api/employees")
async def create_employee(employee: EmployeeCreate):
    """创建新员工"""
    try:
        new_employee = VirtualEmployee(
            id=f"emp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            name=employee.name,
            role=EmployeeRole(employee.role),
            skill_level=employee.skill_level,
            max_workload=employee.max_workload
        )
        
        await employee_manager.add_employee(new_employee)
        
        await manager.broadcast(json.dumps({
            "type": "employee_created",
            "employee_id": new_employee.id,
            "employee_name": new_employee.name
        }))
        
        return {"employee_id": new_employee.id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Error creating employee: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/employees")
async def get_employees():
    """获取所有员工"""
    try:
        employees = await employee_manager.get_all_employees()
        return employees  # 已经是字典格式
    except Exception as e:
        logger.error(f"Error getting employees: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/employees/{employee_id}")
async def get_employee(employee_id: str):
    """获取特定员工"""
    try:
        employee = await employee_manager.get_employee(employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
            
        return {
            "id": employee.id,
            "name": employee.name,
            "role": employee.role.value,
            "skill_level": employee.skill_level,
            "status": employee.status,
            "workload": employee.workload,
            "current_task": employee.current_task,
            "performance_history": employee.performance_history
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting employee {employee_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 智能助理API
@app.post("/api/strategic-decisions")
async def create_strategic_decision(decision: StrategicDecisionCreate):
    """创建战略决策"""
    try:
        strategic_decision = StrategicDecision(
            id=f"strategic_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            type="strategic",
            title=decision.title,
            description=decision.description,
            priority=TaskPriority(decision.priority),
            estimated_impact=decision.estimated_impact,
            required_resources=decision.required_resources,
            timeline=timedelta(hours=decision.timeline_hours),
            created_at=datetime.utcnow()
        )
        
        ceo_assistant.strategic_decisions.append(strategic_decision)
        
        return {"decision_id": strategic_decision.id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Error creating strategic decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/business-analysis")
async def get_business_analysis():
    """获取业务分析"""
    try:
        analysis = await ceo_assistant.analyze_business_situation()
        return analysis
    except Exception as e:
        logger.error(f"Error getting business analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/daily-report")
async def get_daily_report():
    """获取日报"""
    try:
        report = await secretary_assistant.prepare_daily_report()
        return report
    except Exception as e:
        logger.error(f"Error getting daily report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 会议管理API
@app.post("/api/meetings")
async def create_meeting(meeting: MeetingCreate):
    """创建会议"""
    try:
        start_time = datetime.fromisoformat(meeting.start_time)
        duration = timedelta(minutes=meeting.duration_minutes)
        
        meeting_id = await secretary_assistant.schedule_meeting(
            title=meeting.title,
            participants=meeting.participants,
            start_time=start_time,
            duration=duration,
            agenda=meeting.agenda
        )
        
        return {"meeting_id": meeting_id, "status": "scheduled"}
        
    except Exception as e:
        logger.error(f"Error creating meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/meetings")
async def get_meetings():
    """获取所有会议"""
    try:
        meetings = secretary_assistant.meetings
        return [
            {
                "id": meeting.id,
                "title": meeting.title,
                "participants": meeting.participants,
                "start_time": meeting.start_time.isoformat(),
                "duration": str(meeting.duration),
                "agenda": meeting.agenda,
                "status": meeting.status
            }
            for meeting in meetings
        ]
    except Exception as e:
        logger.error(f"Error getting meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket端点
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理不同类型的消息
            if message.get("type") == "ping":
                await manager.send_personal_message(json.dumps({"type": "pong"}), websocket)
            elif message.get("type") == "subscribe":
                # 处理订阅逻辑
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 监控API
@app.get("/api/monitoring/dashboard")
async def get_dashboard_data():
    """获取监控大屏数据"""
    try:
        # 获取综合数据
        business_analysis = await ceo_assistant.analyze_business_situation()
        employee_performance = await ceo_assistant.monitor_employee_performance()
        daily_report = await secretary_assistant.prepare_daily_report()
        
        # 获取系统状态
        system_overview = await employee_manager.get_system_overview()
        all_tasks = await task_manager.get_all_tasks()
        
        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "business_overview": business_analysis,
            "employee_performance": employee_performance,
            "daily_summary": daily_report,
            "system_status": {
                "total_employees": system_overview["total_employees"],
                "total_tasks": len(all_tasks),
                "active_tasks": len([t for t in all_tasks if t["status"] == "in_progress"]),
                "completed_tasks": len([t for t in all_tasks if t["status"] == "completed"])
            }
        }
        
        return dashboard
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )