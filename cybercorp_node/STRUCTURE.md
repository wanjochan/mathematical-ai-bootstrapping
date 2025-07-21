# CyberCorp Node 项目结构

## 目录组织

```
cybercorp_node/
├── src/                    # 源代码
│   ├── core/              # 核心功能
│   │   ├── server.py      # WebSocket服务器
│   │   ├── client.py      # 客户端实现
│   │   ├── remote_control.py  # 远程控制接口
│   │   └── ...            # 其他核心模块
│   ├── vision/            # 视觉分析模块
│   │   ├── analyzer.py    # 视觉分析器（原vision_integration.py）
│   │   ├── vision_model.py    # 统一的视觉模型接口
│   │   └── backends/      # 不同的视觉后端
│   │       └── ocr_backend.py
│   └── automation/        # 自动化工具
│       ├── cursor.py      # Cursor IDE自动化（原cursor_automation.py）
│       ├── cursor_ide_controller.py  # Cursor控制器
│       ├── windows.py     # Windows自动化（原win32_backend.py）
│       └── window_cache.py    # 窗口缓存
├── scripts/               # 脚本文件
│   ├── start_server.bat   # 启动服务器
│   ├── start_client.bat   # 启动客户端
│   └── start_client.py    # Python启动脚本
├── tests/                 # 测试文件
│   ├── unit/             # 单元测试
│   └── integration/      # 集成测试
├── docs/                  # 文档
├── plugins/              # 插件系统
├── logs/                 # 日志文件
└── var/                  # 临时数据

```

## 核心模块说明

### Core（核心功能）
- 服务器/客户端通信
- 远程控制协议
- 命令转发和响应处理
- 配置管理
- 健康监控

### Vision（视觉分析）
- 窗口内容分析
- UI元素识别
- OCR文本提取
- 多后端支持

### Automation（自动化）
- Cursor IDE控制
- VSCode自动化
- Windows窗口操作
- 键盘鼠标模拟

## 使用方式

1. 启动服务器：`scripts/start_server.bat`
2. 启动客户端：`scripts/start_client.bat`
3. 运行测试：`python -m pytest tests/`

## 注意事项

- 所有import路径需要更新为新的模块结构
- 配置文件（config.ini, server_config.json）保留在根目录
- 日志文件自动保存到logs/目录
- 临时文件应保存到var/目录