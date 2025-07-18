"""
AI中控助理API接口

提供RESTful和WebSocket接口，让用户能够通过HTTP请求或实时连接
使用AI中控助理的各种功能。
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import json

from ..core.ai_orchestrator import AIOrchestrator, AIMode, ToolType, TaskContext
from ..core.colleague import ColleagueManager

router = APIRouter(prefix="/ai-orchestrator", tags=["ai-orchestrator"])

# 全局实例
manager = ColleagueManager()
orchestrator = AIOrchestrator(manager)

# Pydantic模型
class TaskRequest(BaseModel):
    """任务请求模型"""
    description: str = Field(..., description="任务描述")
    mode: Optional[str] = Field(None, description="指定AI模式(可选)")
    preferred_tools: Optional[List[str]] = Field(default_factory=list, description="首选工具列表")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")
    priority: Optional[str] = Field("normal", description="任务优先级")

class TaskResponse(BaseModel):
    """任务响应模型"""
    success: bool
    task_id: str
    mode: str
    result: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None

class SystemStatus(BaseModel):
    """系统状态模型"""
    is_running: bool
    active_tasks: int
    completed_tasks: int
    available_tools: List[str]
    available_modes: List[str]

@router.on_event("startup")
async def startup_event():
    """启动时初始化AI中控助理"""
    await orchestrator.start()

@router.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    await orchestrator.stop()

@router.post("/tasks", response_model=TaskResponse, summary="执行任务")
async def execute_task(task_request: TaskRequest) -> TaskResponse:
    """
    执行AI任务的主要接口
    
    - **description**: 任务描述，AI会自动分析并选择合适的处理方式
    - **mode**: 可选的AI模式指定 (architect/code/debug/orchestrator/ask)
    - **preferred_tools**: 首选的工具列表
    - **context**: 任务相关的上下文信息
    - **priority**: 任务优先级 (low/normal/high/urgent)
    """
    try:
        # 处理任务请求
        result = await orchestrator.process_request(
            request=task_request.description,
            context=task_request.context
        )
        
        return TaskResponse(
            success=result["success"],
            task_id=result.get("task_id", ""),
            mode=result.get("mode", "unknown"),
            result=result.get("result", {}),
            execution_time=result.get("execution_time", 0),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务执行失败: {str(e)}")

@router.get("/status", response_model=SystemStatus, summary="获取系统状态")
async def get_system_status() -> SystemStatus:
    """获取AI中控助理的当前状态"""
    
    return SystemStatus(
        is_running=True,
        active_tasks=len(orchestrator.active_sessions),
        completed_tasks=orchestrator.metrics["tasks_completed"],
        available_tools=[tool.value for tool in ToolType],
        available_modes=[mode.value for mode in AIMode]
    )

@router.get("/metrics", summary="获取性能指标")
async def get_metrics() -> Dict[str, Any]:
    """获取AI中控助理的性能指标和统计信息"""
    return orchestrator.metrics

@router.get("/task-history", summary="获取任务历史")
async def get_task_history(limit: int = 10) -> Dict[str, Any]:
    """获取最近的任务执行历史"""
    
    recent_tasks = orchestrator.task_history[-limit:] if orchestrator.task_history else []
    
    return {
        "total_tasks": len(orchestrator.task_history),
        "recent_tasks": [
            {
                "task_id": task.task_id,
                "description": task.description,
                "requirements": task.requirements,
                "preferred_tools": [tool.value for tool in task.preferred_tools]
            }
            for task in recent_tasks
        ]
    }

@router.post("/mode-preference", summary="设置模式偏好")
async def set_mode_preference(
    task_type: str,
    preferred_mode: str,
    confidence: float = Field(0.8, ge=0.0, le=1.0)
):
    """
    为特定类型的任务设置模式偏好
    
    - **task_type**: 任务类型关键词
    - **preferred_mode**: 首选的AI模式  
    - **confidence**: 偏好的置信度
    """
    
    # 验证模式有效性
    try:
        AIMode(preferred_mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的AI模式: {preferred_mode}")
    
    # 保存偏好设置到上下文记忆
    if "mode_preferences" not in orchestrator.context_memory:
        orchestrator.context_memory["mode_preferences"] = {}
    
    orchestrator.context_memory["mode_preferences"][task_type] = {
        "mode": preferred_mode,
        "confidence": confidence,
        "updated_at": datetime.now().isoformat()
    }
    
    return {"message": f"已设置任务类型 '{task_type}' 的模式偏好为 '{preferred_mode}'"}

@router.websocket("/ws/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    """
    WebSocket接口，提供实时任务处理和状态更新
    
    客户端可以通过此接口：
    1. 实时发送任务请求
    2. 接收任务执行状态更新
    3. 获取实时系统状态
    """
    await websocket.accept()
    
    # 注册WebSocket会话
    orchestrator.active_sessions[session_id] = {
        "websocket": websocket,
        "connected_at": datetime.now(),
        "tasks_processed": 0
    }
    
    try:
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "available_commands": [
                "execute_task",
                "get_status", 
                "get_metrics",
                "cancel_task"
            ]
        })
        
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "execute_task":
                # 异步执行任务并发送状态更新
                task_description = data.get("description", "")
                context = data.get("context", {})
                
                await websocket.send_json({
                    "type": "task_started",
                    "task_description": task_description,
                    "timestamp": datetime.now().isoformat()
                })
                
                # 执行任务
                result = await orchestrator.process_request(task_description, context)
                
                await websocket.send_json({
                    "type": "task_completed",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                orchestrator.active_sessions[session_id]["tasks_processed"] += 1
                
            elif command == "get_status":
                # 发送系统状态
                status = {
                    "type": "system_status",
                    "is_running": True,
                    "active_tasks": len(orchestrator.active_sessions),
                    "completed_tasks": orchestrator.metrics["tasks_completed"],
                    "session_info": {
                        "session_id": session_id,
                        "tasks_processed": orchestrator.active_sessions[session_id]["tasks_processed"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_json(status)
                
            elif command == "get_metrics":
                # 发送性能指标
                await websocket.send_json({
                    "type": "metrics",
                    "data": orchestrator.metrics,
                    "timestamp": datetime.now().isoformat()
                })
                
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"未知命令: {command}",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"WebSocket错误: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
    finally:
        # 清理会话
        if session_id in orchestrator.active_sessions:
            del orchestrator.active_sessions[session_id]

# 便捷的快速任务接口
@router.post("/quick/code", summary="快速编程任务")
async def quick_code_task(description: str, language: str = "python"):
    """快速编程任务接口"""
    task_request = TaskRequest(
        description=f"用{language}实现: {description}",
        mode="code",
        preferred_tools=["ide_cursor", "ide_vscode"],
        context={"language": language}
    )
    return await execute_task(task_request)

@router.post("/quick/debug", summary="快速调试任务")
async def quick_debug_task(description: str, error_details: str = ""):
    """快速调试任务接口"""
    task_request = TaskRequest(
        description=f"调试问题: {description}",
        mode="debug", 
        preferred_tools=["computer_use"],
        context={"error_details": error_details}
    )
    return await execute_task(task_request)

@router.post("/quick/ask", summary="快速询问")
async def quick_ask(question: str):
    """快速询问接口"""
    task_request = TaskRequest(
        description=question,
        mode="ask"
    )
    return await execute_task(task_request)

@router.post("/batch", summary="批量任务处理")
async def batch_tasks(
    tasks: List[TaskRequest],
    background_tasks: BackgroundTasks
):
    """
    批量处理多个任务
    
    支持并行处理多个不相关的任务，提高效率
    """
    
    task_ids = []
    
    async def process_batch():
        results = []
        for task_request in tasks:
            result = await orchestrator.process_request(
                request=task_request.description,
                context=task_request.context
            )
            results.append(result)
        
        # 保存批量处理结果
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        orchestrator.context_memory[f"batch_results_{batch_id}"] = results
    
    # 在后台异步处理
    background_tasks.add_task(process_batch)
    
    return {
        "message": f"已启动批量处理，共{len(tasks)}个任务",
        "estimated_completion": datetime.now().isoformat()
    } 