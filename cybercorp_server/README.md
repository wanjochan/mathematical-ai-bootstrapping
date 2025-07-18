# CyberCorp 后端服务 (cybercorp_server)

## 概述
CyberCorp 后端服务是虚拟公司三层架构中的服务器组件，提供API和数据处理功能，负责任务调度、员工管理和系统配置。该组件是整个系统的核心，连接前端界面和操作控制端。

## 主要功能
- **员工管理API**：管理虚拟员工的创建、配置和状态
- **任务管理API**：处理任务的创建、分配、执行和监控
- **系统管理API**：提供系统配置和监控功能
- **WebSocket服务**：提供实时通信和事件通知
- **数据存储**：管理系统数据和状态
- **安全认证**：处理用户认证和授权

## 技术栈
- **语言**：Python 3.9+
- **框架**：FastAPI 或 Flask
- **数据库**：PostgreSQL 或 SQLite
- **API文档**：OpenAPI/Swagger
- **认证**：JWT 令牌认证

## 目录结构
```
cybercorp_server/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── employees.py      # 员工管理API
│   │   │   ├── tasks.py          # 任务管理API
│   │   │   ├── system.py         # 系统管理API
│   │   │   └── config.py         # 配置管理API
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── auth.py           # 认证中间件
│   │       ├── rate_limit.py     # 速率限制
│   │       └── cors.py           # 跨域资源共享
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理
│   │   ├── security.py           # 安全相关
│   │   └── logger.py             # 日志系统
│   ├── models/
│   │   ├── __init__.py
│   │   ├── employee.py           # 员工模型
│   │   ├── task.py               # 任务模型
│   │   ├── system.py             # 系统模型
│   │   └── config.py             # 配置模型
│   ├── websocket/
│   │   ├── __init__.py
│   │   ├── manager.py            # WebSocket管理器
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── employee_handler.py # 员工事件处理
│   │   │   ├── task_handler.py     # 任务事件处理
│   │   │   └── system_handler.py   # 系统事件处理
│   │   └── events.py             # 事件定义
│   ├── services/
│   │   ├── __init__.py
│   │   ├── employee_service.py   # 员工服务
│   │   ├── task_service.py       # 任务服务
│   │   ├── system_service.py     # 系统服务
│   │   └── scheduler_service.py  # 调度服务
│   └── utils/
│       ├── __init__.py
│       ├── validators.py         # 数据验证
│       └── helpers.py            # 辅助函数
├── docs/
│   ├── ARCHITECTURE.md           # 架构文档
│   ├── API.md                    # API文档
│   └── DEPLOYMENT.md             # 部署文档
├── config/
│   ├── default.json              # 默认配置
│   ├── development.json          # 开发环境配置
│   ├── production.json           # 生产环境配置
│   └── security.json             # 安全配置
├── tests/
│   ├── __init__.py
│   ├── test_api.py               # API测试
│   ├── test_websocket.py         # WebSocket测试
│   └── test_models.py            # 模型测试
├── requirements.txt              # 依赖管理
├── Dockerfile                    # Docker配置
├── docker-compose.yml            # Docker Compose配置
└── README.md                     # 说明文档
```

## 安装与运行

### 安装依赖

```bash
pip install -r requirements.txt
```

### 开发模式运行

```bash
python src/main.py --dev
```

### 生产模式运行

```bash
python src/main.py --prod
```

## 与其他组件的关系

- **cybercorp_web**：通过API提供数据和服务，接收操作请求
- **cybercorp_oper**：通过API和WebSocket进行通信，接收操作指令，返回执行结果

## 开发指南

### 开发环境设置

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 安装开发依赖：`pip install -r requirements-dev.txt`

### 代码规范

- 遵循PEP 8编码规范
- 使用类型注解
- 编写单元测试
- 文档使用Markdown格式

### 贡献流程

1. 创建功能分支
2. 提交代码
3. 运行测试
4. 提交Pull Request

## 许可证

[MIT License](LICENSE)