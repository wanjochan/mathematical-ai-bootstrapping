# CyberCorp Seed - 多实例管理与协作通信系统

本文档介绍CyberCorp Seed服务器的多实例管理和协作通信功能，这些功能为构建分布式AI员工系统提供了基础设施。

## 功能概述

### 多实例管理系统
- **实例注册与发现**: 动态注册和管理多个seed实例
- **负载均衡**: 支持4种负载均衡策略（轮询、最少连接、随机、权重）
- **健康检查**: 自动心跳检测和故障恢复
- **集群监控**: 实时集群状态和性能监控
- **故障切换**: 自动故障检测和实例切换

### 协作通信协议
- **消息格式标准化**: 统一的消息结构和验证
- **优先级队列**: 4级消息优先级管理
- **可靠性保证**: TTL机制和消息验证
- **会话管理**: 多人协作会话支持
- **实时监控**: WebSocket实时状态更新

## 架构设计

### 多实例管理架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Seed实例 A    │    │   Seed实例 B    │    │   Seed实例 C    │
│   localhost:8000│    │   localhost:8001│    │   localhost:8002│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  实例管理器     │
                    │  - 注册管理     │
                    │  - 负载均衡     │
                    │  - 健康检查     │
                    │  - 故障切换     │
                    └─────────────────┘
```

### 协作通信架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI员工 Dev    │    │   AI员工 QA     │    │  AI员工 Designer│
│   - 消息队列    │◄──►│   - 消息队列    │◄──►│   - 消息队列    │
│   - 协议处理    │    │   - 协议处理    │    │   - 协议处理    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   通信协议      │
                    │  - 消息路由     │
                    │  - 优先级处理   │
                    │  - 会话管理     │
                    │  - 状态同步     │
                    └─────────────────┘
```

## API接口说明

### 多实例管理API

#### 1. 注册实例
```http
POST /api/v1/multi-instance/instances
Content-Type: application/json

{
    "host": "localhost",
    "port": 8001,
    "weight": 2,
    "metadata": {
        "version": "1.0.0",
        "features": ["ai", "ml"]
    }
}
```

#### 2. 获取负载均衡实例
```http
GET /api/v1/multi-instance/instances/loadbalance

响应:
{
    "success": true,
    "instance": {
        "id": "uuid-string",
        "host": "localhost",
        "port": 8001,
        "status": "active",
        "weight": 2
    },
    "url": "http://localhost:8001"
}
```

#### 3. 集群统计
```http
GET /api/v1/multi-instance/cluster/stats

响应:
{
    "success": true,
    "cluster_stats": {
        "total_instances": 3,
        "healthy_instances": 2,
        "unhealthy_instances": 1,
        "total_connections": 150,
        "avg_cpu_usage": 45.2,
        "avg_memory_usage": 68.7,
        "load_balance_strategy": "round_robin"
    }
}
```

### 协作通信API

#### 1. 注册AI员工
```http
POST /api/v1/collaboration/employees/register
Content-Type: application/json

{
    "employee_id": "dev_001",
    "role": "developer"
}
```

#### 2. 建立员工连接
```http
POST /api/v1/collaboration/employees/dev_001/connect
Content-Type: application/json

{
    "target_employee_id": "qa_001"
}
```

#### 3. 发送消息
```http
POST /api/v1/collaboration/employees/dev_001/messages
Content-Type: application/json

{
    "receiver_id": "qa_001",
    "message_type": "task_request",
    "action": "test_code",
    "data": {
        "file_path": "src/main.py",
        "test_type": "unit"
    },
    "priority": 3,
    "ttl_seconds": 300
}
```

#### 4. 创建协作会话
```http
POST /api/v1/collaboration/employees/dev_001/conversations
Content-Type: application/json

{
    "participants": ["dev_001", "qa_001", "designer_001"],
    "topic": "新功能开发讨论",
    "initial_message": {
        "content": "开始讨论新的用户界面功能"
    }
}
```

## 使用示例

### Python客户端示例

#### 多实例管理
```python
import asyncio
import aiohttp

async def register_instance():
    """注册实例到集群"""
    async with aiohttp.ClientSession() as session:
        data = {
            "host": "localhost",
            "port": 8001,
            "weight": 2
        }
        
        async with session.post(
            "http://localhost:8000/api/v1/multi-instance/instances",
            json=data
        ) as response:
            result = await response.json()
            print(f"实例注册结果: {result}")

async def get_load_balanced_instance():
    """获取负载均衡实例"""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "http://localhost:8000/api/v1/multi-instance/instances/loadbalance"
        ) as response:
            result = await response.json()
            print(f"推荐实例: {result['instance']['url']}")

# 运行示例
asyncio.run(register_instance())
asyncio.run(get_load_balanced_instance())
```

#### 协作通信
```python
import asyncio
import aiohttp

async def setup_collaboration():
    """设置协作环境"""
    async with aiohttp.ClientSession() as session:
        # 注册开发者员工
        dev_data = {"employee_id": "dev_001", "role": "developer"}
        await session.post(
            "http://localhost:8000/api/v1/collaboration/employees/register",
            json=dev_data
        )
        
        # 注册QA员工
        qa_data = {"employee_id": "qa_001", "role": "qa_engineer"}
        await session.post(
            "http://localhost:8000/api/v1/collaboration/employees/register",
            json=qa_data
        )
        
        # 建立连接
        connection_data = {"target_employee_id": "qa_001"}
        await session.post(
            "http://localhost:8000/api/v1/collaboration/employees/dev_001/connect",
            json=connection_data
        )
        
        print("协作环境设置完成")

async def send_task_request():
    """发送任务请求"""
    async with aiohttp.ClientSession() as session:
        message_data = {
            "receiver_id": "qa_001",
            "message_type": "task_request",
            "action": "test_code",
            "data": {
                "file_path": "src/main.py",
                "test_type": "unit"
            },
            "priority": 3
        }
        
        async with session.post(
            "http://localhost:8000/api/v1/collaboration/employees/dev_001/messages",
            json=message_data
        ) as response:
            result = await response.json()
            print(f"任务请求发送结果: {result}")

# 运行示例
asyncio.run(setup_collaboration())
asyncio.run(send_task_request())
```

### WebSocket实时监控

#### 多实例集群监控
```javascript
// 连接多实例集群监控
const ws = new WebSocket('ws://localhost:8000/api/v1/multi-instance/monitor');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('集群状态更新:', data.cluster_stats);
    console.log('实例信息:', data.instances);
};
```

#### 员工协作监控
```javascript
// 连接员工协作监控
const ws = new WebSocket('ws://localhost:8000/api/v1/collaboration/employees/dev_001/monitor');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('员工状态:', data.stats);
    console.log('消息统计:', data.stats.message_stats);
};
```

## 配置选项

### 多实例管理配置
```python
# 在多实例管理器中配置
manager = MultiInstanceManager(
    heartbeat_interval=10,      # 心跳间隔（秒）
    instance_timeout=30,        # 实例超时时间（秒）
    load_balance_strategy=LoadBalanceStrategy.ROUND_ROBIN  # 负载均衡策略
)

# 支持的负载均衡策略
- ROUND_ROBIN: 轮询
- LEAST_CONNECTIONS: 最少连接
- RANDOM: 随机
- WEIGHTED: 权重分配
```

### 协作通信配置
```python
# 消息队列配置
queue = MessageQueue(max_size=1000)  # 最大队列大小

# 协议配置
protocol = CollaborationProtocol(
    employee_id="dev_001",
    role=EmployeeRole.DEVELOPER
)

# 消息TTL配置
ttl = timedelta(minutes=5)  # 消息5分钟过期
```

## 最佳实践

### 多实例部署
1. **实例分布**: 在不同服务器上部署实例以提高可用性
2. **权重配置**: 根据服务器性能设置适当的权重
3. **健康检查**: 确保健康检查端点正常工作
4. **监控告警**: 设置集群状态监控和告警

### 协作通信
1. **消息优先级**: 合理设置消息优先级避免重要消息被延迟
2. **TTL设置**: 为时间敏感的消息设置适当的TTL
3. **错误处理**: 实现消息发送失败的重试机制
4. **连接管理**: 定期清理无效的员工连接

## 故障排除

### 常见问题

#### 1. 实例注册失败
```
错误: 实例注册失败: Connection refused
解决: 检查目标实例是否运行，端口是否正确
```

#### 2. 负载均衡无可用实例
```
错误: 当前没有可用的健康实例
解决: 检查实例健康状态，确保心跳正常
```

#### 3. 消息发送失败
```
错误: 员工未连接
解决: 先建立员工连接再发送消息
```

#### 4. 消息队列满
```
错误: 消息队列已满
解决: 增加队列大小或处理积压消息
```

### 调试工具

#### 1. 集群状态检查
```bash
curl http://localhost:8000/api/v1/multi-instance/cluster/stats
```

#### 2. 员工状态检查
```bash
curl http://localhost:8000/api/v1/collaboration/employees/dev_001/stats
```

#### 3. 系统整体状态
```bash
curl http://localhost:8000/api/v1/collaboration/system/stats
```

## 性能调优

### 多实例管理
- 调整心跳间隔平衡及时性和网络负载
- 根据网络延迟调整实例超时时间
- 选择适合业务场景的负载均衡策略

### 协作通信
- 根据业务需求调整消息队列大小
- 优化消息处理器的执行效率
- 合理设置消息TTL避免队列积压

## 扩展开发

### 自定义负载均衡策略
```python
class CustomLoadBalanceStrategy:
    def select_instance(self, instances):
        # 实现自定义选择逻辑
        return selected_instance
```

### 自定义消息处理器
```python
async def custom_message_handler(message: ProtocolMessage):
    # 实现自定义消息处理逻辑
    print(f"处理消息: {message.payload.action}")
```

### 扩展消息类型
```python
class CustomMessageType(Enum):
    CUSTOM_REQUEST = "custom_request"
    CUSTOM_RESPONSE = "custom_response"
```

---

通过以上功能，CyberCorp Seed提供了完整的多实例管理和协作通信基础设施，为构建分布式AI员工系统奠定了坚实的技术基础。 