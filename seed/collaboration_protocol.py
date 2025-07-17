"""
基础协作通信协议

定义和实现AI员工间的协作通信协议，包括：
- 消息格式标准化
- 通信可靠性保证
- 协议扩展性设计
- 任务协调机制
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
import weakref

# 配置日志
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """消息类型枚举"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    COLLABORATION_REQUEST = "collaboration_request"
    COLLABORATION_RESPONSE = "collaboration_response"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    BROADCAST = "broadcast"

class MessagePriority(Enum):
    """消息优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class EmployeeRole(Enum):
    """员工角色枚举"""
    DEVELOPER = "developer"
    ANALYST = "analyst"
    DESIGNER = "designer"
    QA_ENGINEER = "qa_engineer"
    PROJECT_MANAGER = "project_manager"
    COORDINATOR = "coordinator"

@dataclass
class MessageHeader:
    """消息头信息"""
    message_id: str
    sender_id: str
    receiver_id: Optional[str]  # None表示广播
    message_type: MessageType
    priority: MessagePriority
    timestamp: datetime
    correlation_id: Optional[str] = None  # 用于关联请求和响应
    ttl: Optional[timedelta] = None  # 消息生存时间
    
    def __post_init__(self):
        if isinstance(self.message_type, str):
            self.message_type = MessageType(self.message_type)
        if isinstance(self.priority, int):
            self.priority = MessagePriority(self.priority)

@dataclass
class MessagePayload:
    """消息载荷"""
    action: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProtocolMessage:
    """协议消息完整结构"""
    header: MessageHeader
    payload: MessagePayload
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "header": {
                "message_id": self.header.message_id,
                "sender_id": self.header.sender_id,
                "receiver_id": self.header.receiver_id,
                "message_type": self.header.message_type.value,
                "priority": self.header.priority.value,
                "timestamp": self.header.timestamp.isoformat(),
                "correlation_id": self.header.correlation_id,
                "ttl": self.header.ttl.total_seconds() if self.header.ttl else None
            },
            "payload": {
                "action": self.payload.action,
                "data": self.payload.data,
                "metadata": self.payload.metadata
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProtocolMessage':
        """从字典创建消息"""
        header_data = data["header"]
        payload_data = data["payload"]
        
        header = MessageHeader(
            message_id=header_data["message_id"],
            sender_id=header_data["sender_id"],
            receiver_id=header_data.get("receiver_id"),
            message_type=MessageType(header_data["message_type"]),
            priority=MessagePriority(header_data["priority"]),
            timestamp=datetime.fromisoformat(header_data["timestamp"]),
            correlation_id=header_data.get("correlation_id"),
            ttl=timedelta(seconds=header_data["ttl"]) if header_data.get("ttl") else None
        )
        
        payload = MessagePayload(
            action=payload_data["action"],
            data=payload_data["data"],
            metadata=payload_data.get("metadata", {})
        )
        
        return cls(header=header, payload=payload)

class MessageValidator:
    """消息验证器"""
    
    @staticmethod
    def validate_message(message: ProtocolMessage) -> List[str]:
        """验证消息格式"""
        errors = []
        
        # 验证消息头
        if not message.header.message_id:
            errors.append("消息ID不能为空")
        
        if not message.header.sender_id:
            errors.append("发送者ID不能为空")
        
        if not isinstance(message.header.message_type, MessageType):
            errors.append("无效的消息类型")
        
        if not isinstance(message.header.priority, MessagePriority):
            errors.append("无效的消息优先级")
        
        # 验证消息载荷
        if not message.payload.action:
            errors.append("动作不能为空")
        
        if not isinstance(message.payload.data, dict):
            errors.append("数据必须是字典类型")
        
        # 检查TTL
        if message.header.ttl and message.header.ttl.total_seconds() <= 0:
            errors.append("TTL必须大于0")
        
        return errors
    
    @staticmethod
    def is_message_expired(message: ProtocolMessage) -> bool:
        """检查消息是否过期"""
        if not message.header.ttl:
            return False
        
        elapsed = datetime.now() - message.header.timestamp
        return elapsed > message.header.ttl

class MessageQueue:
    """消息队列"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._queues: Dict[MessagePriority, asyncio.Queue] = {
            priority: asyncio.Queue(maxsize=max_size // len(MessagePriority))
            for priority in MessagePriority
        }
        self._total_size = 0
    
    async def put(self, message: ProtocolMessage) -> bool:
        """添加消息到队列"""
        if self._total_size >= self.max_size:
            logger.warning("消息队列已满，丢弃低优先级消息")
            # 尝试丢弃低优先级消息
            if not await self._drop_low_priority_message():
                return False
        
        # 验证消息
        errors = MessageValidator.validate_message(message)
        if errors:
            logger.error(f"消息验证失败: {errors}")
            return False
        
        # 检查消息是否过期
        if MessageValidator.is_message_expired(message):
            logger.warning(f"消息已过期: {message.header.message_id}")
            return False
        
        queue = self._queues[message.header.priority]
        try:
            await queue.put(message)
            self._total_size += 1
            return True
        except asyncio.QueueFull:
            logger.warning(f"优先级 {message.header.priority} 队列已满")
            return False
    
    async def get(self) -> Optional[ProtocolMessage]:
        """按优先级获取消息"""
        # 按优先级从高到低检查队列
        for priority in sorted(MessagePriority, key=lambda x: x.value, reverse=True):
            queue = self._queues[priority]
            if not queue.empty():
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=0.1)
                    self._total_size -= 1
                    
                    # 再次检查过期
                    if MessageValidator.is_message_expired(message):
                        logger.warning(f"获取的消息已过期: {message.header.message_id}")
                        continue
                    
                    return message
                except asyncio.TimeoutError:
                    continue
        
        return None
    
    async def _drop_low_priority_message(self) -> bool:
        """丢弃低优先级消息"""
        for priority in sorted(MessagePriority, key=lambda x: x.value):
            queue = self._queues[priority]
            if not queue.empty():
                try:
                    await asyncio.wait_for(queue.get(), timeout=0.1)
                    self._total_size -= 1
                    return True
                except asyncio.TimeoutError:
                    continue
        return False
    
    def size(self) -> int:
        """获取队列总大小"""
        return self._total_size
    
    def stats(self) -> Dict[str, int]:
        """获取队列统计信息"""
        return {
            priority.name: queue.qsize()
            for priority, queue in self._queues.items()
        }

class CollaborationProtocol:
    """协作通信协议管理器"""
    
    def __init__(self, employee_id: str, role: EmployeeRole):
        self.employee_id = employee_id
        self.role = role
        self.message_queue = MessageQueue()
        self.active_conversations: Dict[str, List[str]] = {}  # conversation_id -> message_ids
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.running = False
        self._process_task: Optional[asyncio.Task] = None
        
        # 消息统计
        self.stats = {
            "sent": 0,
            "received": 0,
            "processed": 0,
            "errors": 0
        }
        
        # 连接的其他员工
        self.connections: Dict[str, weakref.ref] = {}
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[message_type] = handler
        logger.info(f"为 {message_type.value} 注册处理器")
    
    def connect_employee(self, employee_id: str, protocol_instance: 'CollaborationProtocol'):
        """连接到其他员工"""
        self.connections[employee_id] = weakref.ref(protocol_instance)
        logger.info(f"员工 {self.employee_id} 连接到 {employee_id}")
    
    def disconnect_employee(self, employee_id: str):
        """断开与其他员工的连接"""
        if employee_id in self.connections:
            del self.connections[employee_id]
            logger.info(f"员工 {self.employee_id} 断开与 {employee_id} 的连接")
    
    async def start(self):
        """启动协议处理"""
        if self.running:
            return
        
        self.running = True
        self._process_task = asyncio.create_task(self._process_messages())
        logger.info(f"员工 {self.employee_id} 协作协议已启动")
    
    async def stop(self):
        """停止协议处理"""
        self.running = False
        
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"员工 {self.employee_id} 协作协议已停止")
    
    async def send_message(self, 
                          receiver_id: Optional[str],
                          message_type: MessageType,
                          action: str,
                          data: Dict[str, Any],
                          priority: MessagePriority = MessagePriority.NORMAL,
                          correlation_id: Optional[str] = None,
                          ttl: Optional[timedelta] = None) -> str:
        """发送消息"""
        
        message_id = str(uuid.uuid4())
        
        header = MessageHeader(
            message_id=message_id,
            sender_id=self.employee_id,
            receiver_id=receiver_id,
            message_type=message_type,
            priority=priority,
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            ttl=ttl
        )
        
        payload = MessagePayload(
            action=action,
            data=data,
            metadata={"sender_role": self.role.value}
        )
        
        message = ProtocolMessage(header=header, payload=payload)
        
        # 发送到目标员工或广播
        if receiver_id:
            await self._send_to_employee(receiver_id, message)
        else:
            await self._broadcast_message(message)
        
        self.stats["sent"] += 1
        logger.debug(f"消息已发送: {message_id}")
        
        return message_id
    
    async def _send_to_employee(self, employee_id: str, message: ProtocolMessage):
        """发送消息到指定员工"""
        if employee_id in self.connections:
            employee_ref = self.connections[employee_id]
            employee = employee_ref()
            
            if employee:
                success = await employee.message_queue.put(message)
                if not success:
                    logger.error(f"发送消息到 {employee_id} 失败")
                    self.stats["errors"] += 1
            else:
                logger.warning(f"员工 {employee_id} 已不可用")
                del self.connections[employee_id]
        else:
            logger.warning(f"员工 {employee_id} 未连接")
    
    async def _broadcast_message(self, message: ProtocolMessage):
        """广播消息"""
        for employee_id in list(self.connections.keys()):
            await self._send_to_employee(employee_id, message)
    
    async def _process_messages(self):
        """处理消息循环"""
        while self.running:
            try:
                message = await self.message_queue.get()
                if message:
                    await self._handle_message(message)
                else:
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"处理消息时出错: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(1)
    
    async def _handle_message(self, message: ProtocolMessage):
        """处理单个消息"""
        try:
            self.stats["received"] += 1
            
            # 检查是否有注册的处理器
            handler = self.message_handlers.get(message.header.message_type)
            
            if handler:
                await handler(message)
                self.stats["processed"] += 1
                logger.debug(f"消息已处理: {message.header.message_id}")
            else:
                logger.warning(f"未找到消息类型 {message.header.message_type.value} 的处理器")
        
        except Exception as e:
            logger.error(f"处理消息 {message.header.message_id} 时出错: {e}")
            self.stats["errors"] += 1
    
    async def create_conversation(self, 
                                participants: List[str],
                                topic: str,
                                initial_message: Optional[Dict[str, Any]] = None) -> str:
        """创建会话"""
        conversation_id = str(uuid.uuid4())
        self.active_conversations[conversation_id] = []
        
        # 发送会话邀请
        for participant_id in participants:
            if participant_id != self.employee_id:
                await self.send_message(
                    receiver_id=participant_id,
                    message_type=MessageType.COLLABORATION_REQUEST,
                    action="join_conversation",
                    data={
                        "conversation_id": conversation_id,
                        "topic": topic,
                        "participants": participants,
                        "creator": self.employee_id,
                        "initial_message": initial_message
                    },
                    priority=MessagePriority.HIGH
                )
        
        logger.info(f"会话已创建: {conversation_id}, 主题: {topic}")
        return conversation_id
    
    def get_stats(self) -> Dict[str, Any]:
        """获取协议统计信息"""
        return {
            "employee_id": self.employee_id,
            "role": self.role.value,
            "message_stats": self.stats.copy(),
            "queue_stats": self.message_queue.stats(),
            "queue_size": self.message_queue.size(),
            "connections": len(self.connections),
            "active_conversations": len(self.active_conversations),
            "running": self.running
        }

# 消息构建器辅助类
class MessageBuilder:
    """消息构建器"""
    
    @staticmethod
    def task_request(sender_id: str, 
                    receiver_id: str,
                    task_name: str,
                    task_data: Dict[str, Any],
                    priority: MessagePriority = MessagePriority.NORMAL) -> ProtocolMessage:
        """构建任务请求消息"""
        header = MessageHeader(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=MessageType.TASK_REQUEST,
            priority=priority,
            timestamp=datetime.now()
        )
        
        payload = MessagePayload(
            action="execute_task",
            data={
                "task_name": task_name,
                **task_data
            }
        )
        
        return ProtocolMessage(header=header, payload=payload)
    
    @staticmethod
    def status_update(sender_id: str,
                     status: str,
                     details: Dict[str, Any]) -> ProtocolMessage:
        """构建状态更新消息"""
        header = MessageHeader(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=None,  # 广播
            message_type=MessageType.STATUS_UPDATE,
            priority=MessagePriority.LOW,
            timestamp=datetime.now()
        )
        
        payload = MessagePayload(
            action="update_status",
            data={
                "status": status,
                **details
            }
        )
        
        return ProtocolMessage(header=header, payload=payload)

if __name__ == "__main__":
    # 测试代码
    async def test_collaboration_protocol():
        """测试协作通信协议"""
        print("=== 协作通信协议测试 ===")
        
        # 创建两个员工协议实例
        dev_protocol = CollaborationProtocol("dev_001", EmployeeRole.DEVELOPER)
        qa_protocol = CollaborationProtocol("qa_001", EmployeeRole.QA_ENGINEER)
        
        # 建立连接
        dev_protocol.connect_employee("qa_001", qa_protocol)
        qa_protocol.connect_employee("dev_001", dev_protocol)
        
        # 注册消息处理器
        async def handle_task_request(message: ProtocolMessage):
            print(f"QA收到任务请求: {message.payload.data}")
        
        qa_protocol.register_handler(MessageType.TASK_REQUEST, handle_task_request)
        
        # 启动协议
        await dev_protocol.start()
        await qa_protocol.start()
        
        # 发送测试消息
        await dev_protocol.send_message(
            receiver_id="qa_001",
            message_type=MessageType.TASK_REQUEST,
            action="test_code",
            data={"code_file": "test.py", "test_cases": ["unit", "integration"]},
            priority=MessagePriority.HIGH
        )
        
        # 等待处理
        await asyncio.sleep(1)
        
        # 查看统计
        print(f"开发者统计: {dev_protocol.get_stats()}")
        print(f"QA统计: {qa_protocol.get_stats()}")
        
        # 停止协议
        await dev_protocol.stop()
        await qa_protocol.stop()
        
        print("测试完成")
    
    # 运行测试
    asyncio.run(test_collaboration_protocol()) 