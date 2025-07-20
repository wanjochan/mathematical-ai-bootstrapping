# 工作笔记 cybercorp_claudecode

本文档包含工作流 cybercorp_claudecode 的上下文、经验和工作会话笔记，以保持AI会话之间的连续性。

## 工作流信息
- 工作ID: cybercorp_claudecode
- 创建时间: 2025-01-20
- 关联计划: [工作计划文档](workplan_cybercorp_claudecode.md)
- 特别注意：不要做历史纪录，只更新最后结果！

## 会话

### 会话：2025-01-20

#### 上下文
- 分析了PRD-claude-code.md中的五大CRUD对象设计
- 评估了cybercorp_node的Windows依赖性
- 用户需求：让专家系统与Claude命令对应，支持跨机器部署

#### 挑战
- 挑战1：cybercorp_node严重依赖Windows API
  - 解决方案：设计轻量级的跨平台方案，避免GUI自动化
- 挑战2：跨机器的LLM专家协调
  - 解决方案：基于Socket通信，使用session_id进行任务调度

#### 状态追踪更新
- 当前状态: PLANNING
- 状态变更原因: 用户决定采用重构方案，在cybercorp_node内实现Linux支持
- 下一步计划: 开始重构cybercorp_node为跨平台架构

## 知识库

### 系统架构

#### PRD-claude-code五大CRUD对象
1. **Session（会话）**: AI专家会话管理
2. **Message（消息）**: 会话交互记录
3. **Task（任务）**: 工作任务抽象
4. **Knowledge（知识）**: 企业知识库
5. **Agent（智能体）**: AI专家角色模板

#### cybercorp_node Windows依赖
- **核心依赖**: pywin32, pywinauto, ctypes.wintypes
- **功能依赖**: 窗口管理、输入模拟、进程控制
- **关键文件**: win32_backend.py, cursor_controller.py

### 关键组件

#### 本地专家管理器设计
```python
class LocalExpertManager:
    def __init__(self):
        self.sessions = {}  # session_id -> process
        self.agents = {}    # agent_id -> config
        
    def create_session(self, agent_id: str):
        """创建新的专家会话"""
        session_id = f"expert_{agent_id}_{int(time.time())}"
        agent = self.agents[agent_id]
        cmd = agent['command'].format(session_id=session_id)
        process = subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE)
        self.sessions[session_id] = process
        return session_id
```

#### 跨平台通信协议设计
```python
{
    "type": "expert_request",
    "session_id": "expert_backend_1234567890",
    "action": "execute",
    "payload": {
        "prompt": "Implement the user authentication module",
        "context": {...}
    }
}
```

### 重要模式

#### 轻量级跨机器通信
- 不依赖GUI自动化
- 基于Socket/WebSocket通信
- 使用JSON协议传输命令和结果
- session_id作为任务追踪标识

#### 专家生命周期管理
1. 创建：根据Agent模板spawn进程
2. 执行：通过stdin/stdout或Socket通信
3. 监控：心跳检测和状态追踪
4. 清理：任务完成后的资源回收

## 工作流状态历史

### 状态变更记录
| 时间 | 从状态 | 到状态 | 变更原因 | 备注 |
|------|--------|--------|----------|------|
| 2025-01-20 | INIT | PLANNING | 初始化完成 | 已分析需求和现有代码 |

### 关键里程碑
- 里程碑1: 2025-01-20 - 完成cybercorp_node Windows依赖分析
- 里程碑2: 2025-01-20 - 制定轻量级跨平台方案

## 参考资料

- PRD-claude-code.md: 产品需求文档
- cybercorp_node/server.py: 现有服务器实现
- docs/workflow.md: 工作流程指南

## 改进建议

### 基于本次执行的建议
- 建议1：优先实现不依赖GUI的专家通信方案
- 建议2：考虑使用gRPC替代原始Socket通信
- 建议3：为每个专家创建独立的Docker容器

### 技术决策
- **重构而非重写**: 用户选择在cybercorp_node内重构，而非创建独立项目
- **平台抽象层设计**: 创建backends/目录结构，实现平台特定功能分离
- **渐进式重构**: 先保证Windows功能不变，再逐步添加Linux支持

### 重构架构决策（2025-01-20更新）
经过评估两种方案：
1. 创建独立的cybercorp_node_linux/（不推荐）
2. 在cybercorp_node内重构添加Linux支持（推荐）

选择方案2的原因：
- 约60%代码可复用（配置管理、通信协议、日志等）
- 统一维护，降低长期成本
- 强制良好的抽象设计
- 符合DRY原则

重构关键点：
- 创建backends/目录分离平台特定代码
- 保持utils/中平台无关代码不变
- client.py作为统一入口，自动选择平台实现
- 分层的requirements管理

## 下一步行动
1. 开始实现LocalExpertManager
2. 设计专家通信协议
3. 创建简单的测试用例验证概念