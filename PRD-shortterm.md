# CyberCorp 短期产品需求文档 (PRD)

**文档版本**：v0.2  
**创建日期**：2025年7月17日  
**状态**：草稿  
**作者**：CyberCorp 产品团队
**工作流**: docs/workflow.md

## 1. 产品概述

### 1.1 产品愿景

CyberCorp 短期目标是构建一个由 AI 驱动的虚拟软件公司，通过智能协调两类虚拟员工（命令行AI工具和图形界面IDE）来实现软件开发流程的自动化。

### 1.2 产品定位

本产品是一个轻量级的虚拟公司运营平台，通过"秘书"角色动态管理不同类型的AI员工，实现软件开发项目的自主执行。

### 1.3 核心价值主张

- **双模式AI员工**：
  - 命令行AI工具（如 gemini-cli, claude-code）
  - 图形界面IDE（如 Cursor, VSCode + 插件）
- **智能秘书系统**：自动协调和分配任务
- **轻量级架构**：最小化依赖，快速部署
- **自组织团队**：支持动态角色切换和任务分配

## 2. 产品架构

### 2.1 系统架构概览

```
┌───────────────────────────────────────────────────────────────┐
│                    CyberCorp 虚拟公司                         │
│                                                               │
│  ┌─────────────────┐        ┌───────────────────────────┐     │
│  │                 │        │                           │     │
│  │  cybercorp_web  │◄──────►│      cybercorp_server     │     │
│  │  (前端界面)     │        │      (后端服务)           │     │
│  │                 │        │                           │     │
│  └─────────────────┘        └───────────────┬───────────┘     │
│                                             │                 │
│                                             ▼                 │
│                             ┌───────────────────────────┐     │
│                             │                           │     │
│                             │      cybercorp_oper       │     │
│                             │      (操作控制端)         │     │
│                             │                           │     │
│                             └───────────────────────────┘     │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

1. **cybercorp_server**
   - 纯后端服务，部署在远程服务器上
   - 处理业务逻辑和数据
   - 提供API接口供前端和操作端调用
   - 实现秘书系统功能（任务调度、角色分配）

2. **cybercorp_oper**
   - 虚拟员工操作控制端，部署在客户端
   - 专注于系统操作层面的功能
   - 管理窗口、进程等系统资源
   - 在不同登录会话中运行，控制虚拟员工行为

3. **cybercorp_web**
   - 纯前端界面，负责展示和交互
   - 统一的用户界面体验
   - 通过API与后端服务通信
   - 提供任务管理、监控和配置功能

## 3. 核心工作流

### 3.1 任务执行流程

1. **任务接收**
   - 从版本控制系统获取任务
   - 解析需求文档
   - 创建详细任务清单

2. **角色分配**
   - 秘书评估任务需求
   - 动态分配开发者/经理角色
   - 选择适合的员工类型（CLI/IDE）

3. **任务执行**
   - 命令行AI处理代码生成
   - 图形界面AI进行代码审查
   - 自动测试与集成

4. **结果验证**
   - 代码质量检查
   - 测试覆盖率分析
   - 性能基准测试

## 4. 实施路线图

### 4.1 第一阶段：基础框架（1-2周）
- [ ] 实现 cybercorp_server 核心功能
- [ ] 开发 cybercorp_oper 基础操作能力
- [ ] 构建 cybercorp_web 简易界面

### 4.2 第二阶段：功能完善（2-3周）
- [ ] 完善 cybercorp_server 的任务调度系统
- [ ] 增强 cybercorp_oper 的窗口和进程管理
- [ ] 优化 cybercorp_web 的用户体验

### 4.3 第三阶段：优化扩展（持续）
- [ ] 系统性能优化
- [ ] 组件间通信协议标准化
- [ ] 支持更多操作系统和环境

| 功能 ID | 命令格式 | 功能描述 | 优先级 |
|:-------:|:--------:|:--------|:-----:|
| EMP-001 | `employee list` | 列出所有 AI 员工 | P0 |
| EMP-002 | `employee add <nickname> <role> <description>` | 添加新 AI 员工 | P0 |
| EMP-003 | `employee update <employee_id> [--nickname] [--role] [--description]` | 更新 AI 员工信息 | P0 |
| EMP-004 | `employee remove <employee_id>` | 移除 AI 员工 | P0 |
| EMP-005 | `employee info <employee_id>` | 查看 AI 员工详细信息 | P0 |

#### 3.2.2 默认 AI 员工配置

| 角色 | 昵称 | 职责描述 | 
|:----:|:----:|:--------|
| 经理 | PM | 负责项目规划、任务分配和进度跟踪 |
| 开发者 | Dev1 | 负责核心功能开发，使用 vscode+augment 插件 |
## 5. 成功指标

- 任务完成率 > 90%
- 平均任务处理时间 < 30分钟
- 系统可用性 > 99.5%
- 资源利用率优化 > 30%

| 功能 ID | 命令格式 | 功能描述 | 优先级 |
|:-------:|:--------:|:--------|:-----:|
| MOD-001 | `model list` | 列出所有可用模型配置 | P0 |
| MOD-002 | `model set <employee_id> <model_type>` | 为 AI 员工设置模型类型 | P0 |
| MOD-003 | `model config <model_type> [--param value]` | 配置特定模型参数 | P1 |
| MOD-004 | `model status` | 查看当前模型使用状态 | P1 |

#### 3.3.1 支持的模型类型

| 模型类型 | 描述 | 适用角色 |
|:-------:|:-----|:--------|
| cursor-ide | 基于 Cursor IDE 的开发模式 | 经理 |
| vscode-augment | VSCode 与 Augment 插件集成 | 开发者 |
| claude-code-cli | Claude 命令行代码助手 | 开发者 |

### 3.4 系统监控模块

| 功能 ID | 命令格式 | 功能描述 | 优先级 |
|:-------:|:--------:|:--------|:-----:|
| MON-001 | `monitor status` | 显示系统整体状态 | P1 |
| MON-002 | `monitor performance` | 显示系统性能指标 | P2 |
| MON-003 | `monitor tasks` | 显示当前任务进度 | P1 |
| MON-004 | `monitor logs [--level] [--component]` | 查看系统日志 | P2 |

### 3.5 系统组件模块

#### 3.5.1 cybercorp_oper 操作控制端

| 功能 ID | 命令格式 | 功能描述 | 优先级 |
|:-------:|:--------:|:--------|:-----:|
| OPER-001 | `oper start [--session <session_name>]` | 启动操作控制端 | P0 |
| OPER-002 | `oper window list` | 列出所有可管理窗口 | P0 |
| OPER-003 | `oper window control <window_id> <action>` | 控制指定窗口 | P0 |
| OPER-004 | `oper process list` | 列出所有进程 | P0 |
| OPER-005 | `oper process control <process_id> <action>` | 控制指定进程 | P0 |

#### 3.5.2 cybercorp_web 前端界面

| 功能 ID | 功能描述 | 优先级 |
|:-------:|:--------|:-----:|
| WEB-001 | 员工管理：查看和控制虚拟员工状态 | P0 |
| WEB-002 | 任务管理：创建、分配和监控任务 | P0 |
| WEB-003 | 系统监控：查看系统资源和性能指标 | P1 |
| WEB-004 | 配置中心：管理系统配置和参数 | P2 |

#### 3.5.3 cybercorp_server 后端服务

| 功能 ID | API端点 | 功能描述 | 优先级 |
|:-------:|:--------|:--------|:-----:|
| SRV-001 | `/api/employees` | 员工管理API | P0 |
| SRV-002 | `/api/tasks` | 任务管理API | P0 |
| SRV-003 | `/api/system` | 系统管理API | P1 |
| SRV-004 | `/api/config` | 配置管理API | P1 |

## 4. 技术规格

### 4.1 cybercorp_server 后端服务

- **语言**：Python 3.9+
- **框架**：FastAPI 或 Flask
- **数据存储**：PostgreSQL 或 SQLite
- **API文档**：OpenAPI/Swagger
- **认证**：JWT 令牌认证

### 4.2 cybercorp_oper 操作控制端

- **语言**：Python 3.9+
- **UI框架**：PyQt 或 Tkinter
- **系统交互**：pywin32 (Windows)，对应Linux库
- **通信**：WebSocket 和 HTTP API
- **日志**：结构化日志，支持远程传输

### 4.3 cybercorp_web 前端界面

- **框架**：React 或 Vue.js
- **UI组件**：Material-UI 或 Ant Design
- **状态管理**：Redux 或 Vuex
- **API客户端**：Axios 或 Fetch API
- **构建工具**：Webpack 或 Vite
- **动态加载**：支持运行时切换模型配置
- **资源管理**：监控和限制模型资源使用

### 4.4 系统监控模块

- **性能指标**：CPU、内存、API 调用频率等
- **状态报告**：定期生成系统状态报告
- **日志级别**：支持 DEBUG、INFO、WARNING、ERROR
- **可视化**：基础的命令行可视化

### 4.5 Windows客户端模块

- **语言**：Python 3.9+
- **UI框架**：PyQt5或PySide6（可配置）
- **系统要求**：Windows 10/11
- **权限要求**：管理员权限（用于创建和管理会话）
- **会话管理**：基于Windows用户会话
- **API集成**：使用pywin32与Windows API交互
- **日志系统**：文件和控制台双重输出

## 5. 实现计划

### 5.1 第一阶段：基础框架 (1周)

- **目标**：实现命令行框架和基本 AI 员工管理
- **关键任务**：
  - 搭建项目结构
  - 实现命令解析系统
  - 开发 AI 员工 CRUD 基本功能
  - 创建默认配置文件

### 5.2 第二阶段：模型集成 (2周)

- **目标**：实现不同模型类型的配置和集成
- **关键任务**：
  - 开发模型配置模块
  - 实现 cursor-ide 适配器
  - 实现 vscode-augment 适配器
  - 实现 claude-code-cli 适配器

### 5.3 第三阶段：Windows客户端 (1周)

- **目标**：实现Windows桌面会话客户端
- **关键任务**：
  - 开发会话管理功能
  - 实现命令执行机制
  - 开发基础图形界面
  - 集成Windows API

### 5.4 第四阶段：系统监控 (1周)

- **目标**：实现基础系统监控功能
- **关键任务**：
  - 开发状态监控功能
  - 实现任务进度跟踪
  - 开发简单的日志系统
  - 集成性能监控

### 5.5 第五阶段：测试与优化 (1周)

- **目标**：确保系统稳定性和可用性
- **关键任务**：
  - 编写单元测试
  - 进行集成测试
  - 性能优化
  - 文档完善

## 6. 扩展计划

### 6.1 近期扩展

- **董秘角色**：添加董秘角色，协调董事与经理之间的沟通
- **项目管理**：添加项目和任务管理功能
- **自动化工作流**：定义标准化工作流程
- **报告生成**：自动生成工作报告和统计数据

### 6.2 中期扩展

- **Web 界面**：开发简单的 Web 管理界面
- **多实例支持**：支持多个虚拟公司实例
- **API 集成**：提供 REST API 接口
- **插件系统**：支持第三方插件扩展功能

## 7. 使用示例

### 7.1 基本使用流程

```bash
# 初始化默认团队
python cybercorp.py employee init

# 查看所有 AI 员工
python cybercorp.py employee list

# 为经理设置 cursor-ide 模型
python cybercorp.py model set PM cursor-ide

# 为开发者设置不同模型
python cybercorp.py model set Dev1 vscode-augment
python cybercorp.py model set Dev2 claude-code-cli

# 查看系统状态
python cybercorp.py monitor status
```

### 7.2 Windows客户端使用示例

```bash
# 启动Windows客户端图形界面
python cybercorp.py client win-client

# 仅命令行模式启动
python cybercorp.py client win-client --no-gui

# 创建Windows会话
python cybercorp.py client win-client session create dev-user

# 列出所有Windows会话
python cybercorp.py client win-client session list

# 在指定会话中执行命令
python cybercorp.py client win-client exec win-dev-user-0 "notepad.exe"

# 关闭指定会话
python cybercorp.py client win-client session close win-dev-user-0
```

### 7.3 添加董秘角色示例

```bash
# 添加董秘角色
python cybercorp.py employee add Secretary "董秘" "协调董事与经理之间的沟通，整理会议记录"

# 为董秘设置模型
python cybercorp.py model set Secretary claude-code-cli
```

## 8. 注意事项与限制

- 中央系统初期版本仅支持命令行界面，Windows客户端提供基础图形界面
- 数据存储使用本地文件，暂不支持数据库
- 需要预先安装相关模型和工具（如 VSCode、Cursor IDE 等）
- 系统监控功能仅提供基础指标，不支持复杂分析
- 不同模型之间的协作机制需要进一步完善
- Windows客户端需要管理员权限才能创建和管理用户会话
- 初期版本仅支持Windows平台客户端，未来将扩展到其他平台

## 9. 结论

CyberCorp 短期产品计划专注于构建一个实用的虚拟智能公司中控系统，通过命令行工具管理 AI 员工团队。这一系统将为未来更复杂的 AI 自举系统奠定基础，同时提供立即可用的价值。

模块化的设计确保了系统的可扩展性，使我们能够逐步添加新功能和改进现有功能。通过这种渐进式的开发方法，我们可以快速交付有价值的功能，同时为长期愿景铺平道路。

Windows桌面客户端的引入为管理分布式AI员工提供了关键支持，使系统能够在实际工作环境中更加灵活地部署和管理AI员工。这一客户端架构也为未来支持更多平台和环境提供了可扩展的基础。
