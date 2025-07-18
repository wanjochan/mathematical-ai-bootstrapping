# CyberCorp 操作控制端 (cybercorp_oper)

## 概述

CyberCorp 操作控制端是虚拟公司三层架构中的客户端组件，负责窗口和进程管理、系统监控以及与后端服务器的通信。该组件部署在客户端，提供对本地系统资源的访问和控制能力。

## 主要功能

- **窗口管理**：监控和控制系统窗口，包括窗口列表、窗口属性和窗口操作
- **进程控制**：监控和控制系统进程，包括进程列表、进程状态和进程操作
- **系统监控**：收集系统资源使用情况，包括CPU、内存和磁盘使用率
- **与服务器通信**：通过API和WebSocket与后端服务器进行通信
- **本地UI界面**：提供简洁的本地操作界面

## 技术栈

- **语言**：Python 3.9+
- **UI框架**：PyQt 或 Tkinter
- **系统交互**：pywin32 (Windows)，对应Linux库
- **通信**：WebSocket 和 HTTP API
- **日志**：结构化日志，支持远程传输

## 目录结构

```
cybercorp_oper/
├── docs/                 # 文档
│   ├── ARCHITECTURE.md   # 架构文档
│   └── API.md            # API文档
├── src/                  # 源代码
│   ├── window/           # 窗口管理模块
│   ├── process/          # 进程控制模块
│   ├── communication/    # 通信模块
│   ├── ui/               # 用户界面
│   └── main.py           # 主入口
├── tests/                # 测试
├── requirements.txt      # 依赖管理
└── README.md            # 说明文档
```

## 安装与运行

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python src/main.py
```

## 与其他组件的关系

- **cybercorp_server**：通过API和WebSocket与后端服务器通信，获取任务和配置，上报状态和结果
- **cybercorp_web**：不直接通信，通过后端服务器间接交互

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