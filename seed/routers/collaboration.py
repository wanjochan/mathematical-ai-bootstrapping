"""
协作通信协议API路由

提供AI员工协作通信的REST API端点：
- 消息发送和接收
- 会话管理
- 协议状态监控
- 员工连接管理
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import json

from ..collaboration_protocol import (
    CollaborationProtocol,
    MessageType,
    MessagePriority,
    EmployeeRole,
    MessageBuilder,
    ProtocolMessage
)

router = APIRouter(prefix="/collaboration", tags=["collaboration"])

# 全局协议管理器
protocol_instances: Dict[str, CollaborationProtocol] = {}

# Pydantic模型定义
class EmployeeRegistration(BaseModel):
    """员工注册请求模型"""
    employee_id: str = Field(..., description="员工ID")
    role: str = Field(..., description="员工角色")

class MessageRequest(BaseModel):
    """消息发送请求模型"""
    receiver_id: Optional[str] = Field(None, description="接收者ID（None为广播）")
    message_type: str = Field(..., description="消息类型")
    action: str = Field(..., description="动作")
    data: Dict[str, Any] = Field(..., description="消息数据")
    priority: int = Field(2, ge=1, le=4, description="消息优先级（1-4）")
    correlation_id: Optional[str] = Field(None, description="关联ID")
    ttl_seconds: Optional[int] = Field(None, ge=1, description="生存时间（秒）")

class ConversationRequest(BaseModel):
    """会话创建请求模型"""
    participants: List[str] = Field(..., description="参与者ID列表")
    topic: str = Field(..., description="会话主题")
    initial_message: Optional[Dict[str, Any]] = Field(None, description="初始消息")

class ConnectionRequest(BaseModel):
    """连接请求模型"""
    target_employee_id: str = Field(..., description="目标员工ID")

# API端点定义

@router.post("/employees/register", summary="注册员工")
async def register_employee(registration: EmployeeRegistration):
    """
    注册AI员工到协作系统中
    
    - **employee_id**: 员工唯一标识
    - **role**: 员工角色（developer/analyst/designer/qa_engineer/project_manager/coordinator）
    """
    try:
        # 验证角色
        try:
            role_enum = EmployeeRole(registration.role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的员工角色: {registration.role}")
        
        # 检查是否已注册
        if registration.employee_id in protocol_instances:
            raise HTTPException(status_code=409, detail="员工已注册")
        
        # 创建协议实例
        protocol = CollaborationProtocol(registration.employee_id, role_enum)
        protocol_instances[registration.employee_id] = protocol
        
        # 启动协议
        await protocol.start()
        
        return {
            "success": True,
            "employee_id": registration.employee_id,
            "role": registration.role,
            "message": "员工注册成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"员工注册失败: {str(e)}")

@router.delete("/employees/{employee_id}", summary="注销员工")
async def unregister_employee(employee_id: str):
    """
    从协作系统中注销员工
    
    - **employee_id**: 要注销的员工ID
    """
    if employee_id not in protocol_instances:
        raise HTTPException(status_code=404, detail="员工不存在")
    
    try:
        protocol = protocol_instances[employee_id]
        await protocol.stop()
        del protocol_instances[employee_id]
        
        return {
            "success": True,
            "message": "员工注销成功"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"员工注销失败: {str(e)}")

@router.get("/employees", summary="获取所有员工")
async def get_all_employees():
    """
    获取系统中所有注册的员工信息
    
    返回员工列表及其状态信息
    """
    try:
        employees = []
        for employee_id, protocol in protocol_instances.items():
            stats = protocol.get_stats()
            employees.append({
                "employee_id": employee_id,
                "role": stats["role"],
                "running": stats["running"],
                "connections": stats["connections"],
                "message_stats": stats["message_stats"],
                "queue_size": stats["queue_size"]
            })
        
        return {
            "success": True,
            "employees": employees,
            "total_count": len(employees)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取员工列表失败: {str(e)}")

@router.post("/employees/{employee_id}/connect", summary="建立员工连接")
async def connect_employees(employee_id: str, connection: ConnectionRequest):
    """
    建立两个员工之间的通信连接
    
    - **employee_id**: 发起连接的员工ID
    - **target_employee_id**: 目标员工ID
    """
    if employee_id not in protocol_instances:
        raise HTTPException(status_code=404, detail="源员工不存在")
    
    if connection.target_employee_id not in protocol_instances:
        raise HTTPException(status_code=404, detail="目标员工不存在")
    
    try:
        source_protocol = protocol_instances[employee_id]
        target_protocol = protocol_instances[connection.target_employee_id]
        
        # 建立双向连接
        source_protocol.connect_employee(connection.target_employee_id, target_protocol)
        target_protocol.connect_employee(employee_id, source_protocol)
        
        return {
            "success": True,
            "message": f"员工 {employee_id} 与 {connection.target_employee_id} 连接成功"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立连接失败: {str(e)}")

@router.delete("/employees/{employee_id}/disconnect/{target_employee_id}", summary="断开员工连接")
async def disconnect_employees(employee_id: str, target_employee_id: str):
    """
    断开两个员工之间的连接
    
    - **employee_id**: 发起断开的员工ID
    - **target_employee_id**: 目标员工ID
    """
    if employee_id not in protocol_instances:
        raise HTTPException(status_code=404, detail="源员工不存在")
    
    try:
        source_protocol = protocol_instances[employee_id]
        source_protocol.disconnect_employee(target_employee_id)
        
        # 如果目标员工存在，也断开反向连接
        if target_employee_id in protocol_instances:
            target_protocol = protocol_instances[target_employee_id]
            target_protocol.disconnect_employee(employee_id)
        
        return {
            "success": True,
            "message": f"员工 {employee_id} 与 {target_employee_id} 断开连接"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"断开连接失败: {str(e)}")

@router.post("/employees/{employee_id}/messages", summary="发送消息")
async def send_message(employee_id: str, message_request: MessageRequest):
    """
    通过指定员工发送协作消息
    
    - **employee_id**: 发送者员工ID
    - **receiver_id**: 接收者ID（None为广播）
    - **message_type**: 消息类型
    - **action**: 动作名称
    - **data**: 消息数据
    - **priority**: 消息优先级（1-4）
    """
    if employee_id not in protocol_instances:
        raise HTTPException(status_code=404, detail="员工不存在")
    
    try:
        # 验证消息类型
        try:
            msg_type = MessageType(message_request.message_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的消息类型: {message_request.message_type}")
        
        # 验证优先级
        try:
            priority = MessagePriority(message_request.priority)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的消息优先级: {message_request.priority}")
        
        protocol = protocol_instances[employee_id]
        
        # 设置TTL
        ttl = timedelta(seconds=message_request.ttl_seconds) if message_request.ttl_seconds else None
        
        # 发送消息
        message_id = await protocol.send_message(
            receiver_id=message_request.receiver_id,
            message_type=msg_type,
            action=message_request.action,
            data=message_request.data,
            priority=priority,
            correlation_id=message_request.correlation_id,
            ttl=ttl
        )
        
        return {
            "success": True,
            "message_id": message_id,
            "message": "消息发送成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")

@router.post("/employees/{employee_id}/conversations", summary="创建会话")
async def create_conversation(employee_id: str, conversation_request: ConversationRequest):
    """
    创建多人协作会话
    
    - **employee_id**: 会话创建者ID
    - **participants**: 参与者ID列表
    - **topic**: 会话主题
    - **initial_message**: 可选的初始消息
    """
    if employee_id not in protocol_instances:
        raise HTTPException(status_code=404, detail="员工不存在")
    
    try:
        protocol = protocol_instances[employee_id]
        
        # 验证参与者
        for participant_id in conversation_request.participants:
            if participant_id not in protocol_instances:
                raise HTTPException(status_code=400, detail=f"参与者 {participant_id} 不存在")
        
        # 创建会话
        conversation_id = await protocol.create_conversation(
            participants=conversation_request.participants,
            topic=conversation_request.topic,
            initial_message=conversation_request.initial_message
        )
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": "会话创建成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")

@router.get("/employees/{employee_id}/stats", summary="获取员工统计")
async def get_employee_stats(employee_id: str):
    """
    获取指定员工的协作统计信息
    
    - **employee_id**: 员工ID
    """
    if employee_id not in protocol_instances:
        raise HTTPException(status_code=404, detail="员工不存在")
    
    try:
        protocol = protocol_instances[employee_id]
        stats = protocol.get_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/system/stats", summary="获取系统统计")
async def get_system_stats():
    """
    获取整个协作系统的统计信息
    
    包括总员工数、连接状态、消息统计等
    """
    try:
        total_employees = len(protocol_instances)
        total_connections = 0
        total_messages_sent = 0
        total_messages_received = 0
        total_queue_size = 0
        
        employee_stats = []
        
        for employee_id, protocol in protocol_instances.items():
            stats = protocol.get_stats()
            employee_stats.append(stats)
            
            total_connections += stats["connections"]
            total_messages_sent += stats["message_stats"]["sent"]
            total_messages_received += stats["message_stats"]["received"]
            total_queue_size += stats["queue_size"]
        
        return {
            "success": True,
            "system_stats": {
                "total_employees": total_employees,
                "total_connections": total_connections,
                "total_messages_sent": total_messages_sent,
                "total_messages_received": total_messages_received,
                "total_queue_size": total_queue_size,
                "avg_connections_per_employee": round(total_connections / max(total_employees, 1), 2)
            },
            "employee_stats": employee_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}")

# WebSocket端点用于实时消息监控
@router.websocket("/employees/{employee_id}/monitor")
async def websocket_employee_monitor(websocket: WebSocket, employee_id: str):
    """
    WebSocket端点，用于实时监控员工的消息和状态
    
    客户端可以通过此端点实时接收员工的协作活动
    """
    await websocket.accept()
    
    if employee_id not in protocol_instances:
        await websocket.close(code=4004, reason="员工不存在")
        return
    
    try:
        protocol = protocol_instances[employee_id]
        
        while True:
            # 获取员工状态
            stats = protocol.get_stats()
            
            # 发送状态更新
            message = {
                "type": "employee_status",
                "timestamp": datetime.now().isoformat(),
                "employee_id": employee_id,
                "stats": stats
            }
            
            await websocket.send_json(message)
            await asyncio.sleep(2)  # 每2秒发送一次更新
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket监控错误: {e}")
    finally:
        await websocket.close()

@router.get("/message-types", summary="获取支持的消息类型")
async def get_message_types():
    """
    获取系统支持的所有消息类型
    
    返回可用的消息类型列表
    """
    return {
        "success": True,
        "message_types": [msg_type.value for msg_type in MessageType],
        "priorities": [priority.value for priority in MessagePriority],
        "roles": [role.value for role in EmployeeRole]
    }

# 便捷的消息构建端点
@router.post("/messages/task-request", summary="发送任务请求")
async def send_task_request(
    sender_id: str,
    receiver_id: str,
    task_name: str,
    task_data: Dict[str, Any],
    priority: int = 2
):
    """
    便捷的任务请求发送接口
    
    - **sender_id**: 发送者ID
    - **receiver_id**: 接收者ID
    - **task_name**: 任务名称
    - **task_data**: 任务数据
    - **priority**: 优先级（1-4）
    """
    if sender_id not in protocol_instances:
        raise HTTPException(status_code=404, detail="发送者不存在")
    
    try:
        priority_enum = MessagePriority(priority)
        protocol = protocol_instances[sender_id]
        
        message_id = await protocol.send_message(
            receiver_id=receiver_id,
            message_type=MessageType.TASK_REQUEST,
            action="execute_task",
            data={"task_name": task_name, **task_data},
            priority=priority_enum
        )
        
        return {
            "success": True,
            "message_id": message_id,
            "message": "任务请求发送成功"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送任务请求失败: {str(e)}")

@router.post("/messages/status-update", summary="发送状态更新")
async def send_status_update(
    employee_id: str,
    status: str,
    details: Dict[str, Any]
):
    """
    便捷的状态更新广播接口
    
    - **employee_id**: 员工ID
    - **status**: 状态信息
    - **details**: 详细信息
    """
    if employee_id not in protocol_instances:
        raise HTTPException(status_code=404, detail="员工不存在")
    
    try:
        protocol = protocol_instances[employee_id]
        
        message_id = await protocol.send_message(
            receiver_id=None,  # 广播
            message_type=MessageType.STATUS_UPDATE,
            action="update_status",
            data={"status": status, **details},
            priority=MessagePriority.LOW
        )
        
        return {
            "success": True,
            "message_id": message_id,
            "message": "状态更新发送成功"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送状态更新失败: {str(e)}") 