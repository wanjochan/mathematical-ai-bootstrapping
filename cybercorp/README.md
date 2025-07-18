# CyberCorp 动态规划系统

## 项目概述

CyberCorp 动态规划系统是一个基于AI的智能任务管理与员工调度系统，通过虚拟员工和智能助理实现企业级自动化运营。

## 核心功能

### 🧠 智能规划引擎
- **动态任务分解**：自动将复杂任务分解为可执行子任务
- **智能优先级排序**：基于业务影响和资源可用性动态调整任务优先级
- **实时优化**：根据执行反馈持续优化任务分配策略

### 👥 虚拟员工管理
- **多角色支持**：开发者、财务、市场、人事等多种角色
- **技能等级系统**：基于AI评估的员工能力模型
- **工作负载管理**：动态监控和调整员工工作负载
- **绩效追踪**：完整的员工表现历史记录

### 🎯 智能助理系统
- **总裁助理**：战略决策制定、业务分析、危机处理
- **董秘助理**：日常事务管理、会议安排、沟通协调

### 📊 实时监控
- **业务仪表板**：实时展示关键业务指标
- **员工状态监控**：可视化员工工作状态和负载
- **任务进度追踪**：实时任务执行状态更新

## 系统架构

```
cybercorp/
├── dynplan/                 # 动态规划核心模块
│   ├── __init__.py         # 模块初始化
│   ├── dynamic_planning_engine.py  # 动态规划引擎
│   ├── task_scheduler.py   # 任务调度器
│   ├── employee_manager.py # 员工管理器
│   ├── task_manager.py     # 任务管理器
│   ├── ceo_assistant.py    # 总裁助理
│   └── secretary_assistant.py # 董秘助理
├── server.py               # FastAPI服务端
├── requirements.txt        # 依赖列表
└── README.md              # 项目文档
```

## 快速开始

### 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd cybercorp

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 启动服务

```bash
# 启动服务器
python server.py

# 或使用uvicorn
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### API文档

启动服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API使用示例

### 创建任务
```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "开发新功能",
    "description": "实现用户认证系统",
    "priority": 3,
    "estimated_duration": 7200
  }'
```

### 创建员工
```bash
curl -X POST "http://localhost:8000/api/employees" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新开发者",
    "role": "developer",
    "skill_level": 0.8
  }'
```

### 获取业务分析
```bash
curl "http://localhost:8000/api/business-analysis"
```

### 获取监控数据
```bash
curl "http://localhost:8000/api/monitoring/dashboard"
```

## WebSocket实时通信

连接到 `ws://localhost:8000/ws` 获取实时更新：
- 任务状态变化
- 员工状态更新
- 系统事件通知

## 配置说明

### 环境变量
```bash
# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=true

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=cybercorp.log

# 数据库配置（未来版本）
DATABASE_URL=sqlite:///cybercorp.db
```

## 开发指南

### 添加新角色
在 `dynplan/employee_manager.py` 中扩展 `EmployeeRole` 枚举。

### 自定义任务类型
在 `dynplan/task_manager.py` 中扩展 `TaskStatus` 和 `TaskPriority`。

### 扩展智能助理
继承 `CEOAssistant` 或 `SecretaryAssistant` 类实现自定义逻辑。

## 性能优化

### 缓存策略
- 员工状态缓存：5分钟
- 任务队列缓存：1分钟
- 业务分析缓存：30秒

### 并发处理
- 使用asyncio处理并发任务
- WebSocket连接池管理
- 数据库连接池（未来版本）

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   lsof -i :8000  # 查看占用进程
   kill -9 <PID>  # 终止进程
   ```

2. **依赖安装失败**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --no-cache-dir
   ```

3. **WebSocket连接问题**
   - 检查防火墙设置
   - 确认端口开放
   - 验证网络连接

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证

MIT License - 详见 LICENSE 文件

## 联系方式

- 项目维护：CyberCorp AI Team
- 邮箱：ai@cybercorp.com
- 技术支持：support@cybercorp.com