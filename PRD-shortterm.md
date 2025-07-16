# AI-Corp 短期产品需求文档 (PRD)

**文档版本**：v0.1  
**创建日期**：2025年7月16日  
**状态**：草稿  
**作者**：AI-Corp 产品团队

## 1. 产品概述

### 1.1 产品愿景

AI-Corp 短期目标是开发一个实用的虚拟智能公司中控系统，通过命令行工具管理 AI 员工团队，实现软件开发流程的自动化和智能化。

注意：本 PRD 是根据 mathematical-ai-bootstrapping.md

### 1.2 产品定位

本产品是一个面向开发者和小型团队的命令行工具，提供 AI 员工管理、模型配置和系统监控的基础功能，为未来更复杂的 AI 自举系统奠定基础。

### 1.3 核心价值主张

- **虚拟团队管理**：创建和管理 AI 员工团队，分配不同角色和职责
- **灵活模型配置**：为不同 AI 员工配置不同的工作模式和模型
- **系统化工作流**：通过命令行工具实现标准化的工作流程
- **可扩展架构**：模块化设计，便于未来功能扩展

## 2. 产品架构

### 2.1 系统架构概览



```
┌─────────────────────────────────────┐
│           aicorp.py (主入口)          │
│  命令解析与分发、全局配置、帮助系统    │
└───────────┬─────────────┬───────────┘
            │             │             
┌───────────▼─────┐ ┌─────▼───────────┐ ┌───────────────────┐
│  AI 员工管理模块    │ │  模型配置模块    │ │  系统监控模块     │
│ (employee/)     │ │ (model/)        │ │ (monitor/)        │
└─────────┬───────┘ └─────────────────┘ └───────────────────┘
          │
          ▼
┌─────────────────────┐
│  客户端模块          │
│ (clients/)          │
└─────────────────────┘
```

### 2.2 目录结构

```
aicorp/
├── aicorp.py           # 主入口脚本
├── config/             # 配置文件目录
│   ├── default.json    # 默认配置
│   └── instances/      # 实例配置
├── employee/           # AI 员工管理模块
│   ├── __init__.py
│   ├── crud.py         # AI 员工CRUD操作
│   └── roles.py        # 角色定义
├── model/              # 模型配置模块
│   ├── __init__.py
│   ├── config.py       # 模型配置管理
│   └── adapters/       # 不同模型适配器
├── monitor/            # 系统监控模块
│   ├── __init__.py
│   ├── performance.py  # 性能监控
│   └── status.py       # 状态报告
└── clients/            # 客户端模块
    ├── __init__.py
    ├── README.md       # 客户端文档
    └── win-client/     # Windows桌面客户端
        ├── __init__.py
        ├── main.py     # 主入口
        ├── session.py  # 会话管理
        ├── ui/         # 界面组件
        └── utils/      # 工具函数
```

## 3. 功能需求

### 3.1 命令行接口 (aicorp.py)

| 功能 ID | 命令格式 | 功能描述 | 优先级 |
|:-------:|:--------:|:--------|:-----:|
| CLI-001 | `python aicorp.py employee <subcommand> [args]` | AI 员工管理相关命令 | P0 |
| CLI-002 | `python aicorp.py model <subcommand> [args]` | 模型配置相关命令 | P0 |
| CLI-003 | `python aicorp.py monitor <subcommand> [args]` | 系统监控相关命令 | P1 |
| CLI-004 | `python aicorp.py client <client_type> [args]` | 客户端管理命令 | P0 |
| CLI-005 | `python aicorp.py help [command]` | 显示帮助信息 | P0 |
| CLI-006 | `python aicorp.py version` | 显示版本信息 | P2 |

### 3.2 AI 员工管理模块

#### 3.2.1 AI 员工 CRUD 操作

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
| 开发者 | Dev2 | 负责辅助功能开发，使用 claude-code-cli |

### 3.3 模型配置模块

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

### 3.5 客户端模块

#### 3.5.1 Windows桌面客户端

| 功能 ID | 命令格式 | 功能描述 | 优先级 |
|:-------:|:--------:|:--------|:-----:|
| WIN-001 | `client win-client [--no-gui]` | 启动Windows客户端 | P0 |
| WIN-002 | `client win-client session create <username>` | 创建Windows会话 | P0 |
| WIN-003 | `client win-client session list` | 列出所有Windows会话 | P0 |
| WIN-004 | `client win-client session close <session_id>` | 关闭指定Windows会话 | P0 |
| WIN-005 | `client win-client exec <session_id> <command>` | 在指定会话中执行命令 | P0 |

#### 3.5.2 Windows客户端图形界面功能

| 功能 ID | 功能描述 | 优先级 |
|:-------:|:--------|:-----:|
| WINGUI-001 | 会话管理面板：创建、查看和关闭会话 | P0 |
| WINGUI-002 | 命令执行面板：在选定会话中执行命令 | P0 |
| WINGUI-003 | 状态监控面板：显示会话状态和性能指标 | P1 |
| WINGUI-004 | 日志查看器：查看操作日志 | P2 |

## 4. 技术规格

### 4.1 aicorp.py 主入口

- **语言**：Python 3.9+
- **依赖管理**：使用 requirements.txt 或 Poetry
- **命令解析**：使用 argparse 或 Click 库
- **配置管理**：JSON 格式配置文件

### 4.2 AI 员工管理模块

- **数据存储**：JSON 文件存储 AI 员工信息
- **唯一标识**：每个 AI 员工分配唯一 ID
- **角色验证**：确保角色符合预定义类型
- **事件通知**：AI 员工变更时触发通知

### 4.3 模型配置模块

- **适配器模式**：为不同模型类型实现适配器
- **配置验证**：验证模型参数的有效性
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
python aicorp.py employee init

# 查看所有 AI 员工
python aicorp.py employee list

# 为经理设置 cursor-ide 模型
python aicorp.py model set PM cursor-ide

# 为开发者设置不同模型
python aicorp.py model set Dev1 vscode-augment
python aicorp.py model set Dev2 claude-code-cli

# 查看系统状态
python aicorp.py monitor status
```

### 7.2 Windows客户端使用示例

```bash
# 启动Windows客户端图形界面
python aicorp.py client win-client

# 仅命令行模式启动
python aicorp.py client win-client --no-gui

# 创建Windows会话
python aicorp.py client win-client session create dev-user

# 列出所有Windows会话
python aicorp.py client win-client session list

# 在指定会话中执行命令
python aicorp.py client win-client exec win-dev-user-0 "notepad.exe"

# 关闭指定会话
python aicorp.py client win-client session close win-dev-user-0
```

### 7.3 添加董秘角色示例

```bash
# 添加董秘角色
python aicorp.py employee add Secretary "董秘" "协调董事与经理之间的沟通，整理会议记录"

# 为董秘设置模型
python aicorp.py model set Secretary claude-code-cli
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

AI-Corp 短期产品计划专注于构建一个实用的虚拟智能公司中控系统，通过命令行工具管理 AI 员工团队。这一系统将为未来更复杂的 AI 自举系统奠定基础，同时提供立即可用的价值。

模块化的设计确保了系统的可扩展性，使我们能够逐步添加新功能和改进现有功能。通过这种渐进式的开发方法，我们可以快速交付有价值的功能，同时为长期愿景铺平道路。

Windows桌面客户端的引入为管理分布式AI员工提供了关键支持，使系统能够在实际工作环境中更加灵活地部署和管理AI员工。这一客户端架构也为未来支持更多平台和环境提供了可扩展的基础。
