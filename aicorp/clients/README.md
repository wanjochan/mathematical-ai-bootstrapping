# AI-Corp 客户端模块

本目录包含AI-Corp各种平台的客户端实现，用于管理分布在不同环境中的AI员工。

## 目录结构

- `win-client/`: Windows桌面会话客户端
  - 管理Windows桌面环境中的AI员工会话
  - 提供命令行和图形界面
  - 支持与Windows API交互

## Windows客户端

Windows客户端(`win-client`)提供以下功能：

1. 创建和管理Windows桌面会话
2. 在会话中执行命令
3. 监控会话状态和性能
4. 提供图形界面进行可视化管理

### 使用方法

```bash
# 启动图形界面
python -m aicorp.clients.win-client.main

# 仅使用命令行
python -m aicorp.clients.win-client.main --no-gui

# 创建会话
python -m aicorp.clients.win-client.main session create <username>

# 列出会话
python -m aicorp.clients.win-client.main session list

# 关闭会话
python -m aicorp.clients.win-client.main session close <session_id>

# 执行命令
python -m aicorp.clients.win-client.main exec <session_id> "<command>"
```

## 开发计划

- [ ] 实现Windows API交互
- [ ] 完成图形界面设计
- [ ] 添加会话监控功能
- [ ] 支持多会话并行管理
- [ ] 集成到AI-Corp主系统

## 依赖

- Python 3.9+
- PyQt5/PySide6 (图形界面)
- pywin32 (Windows API交互)

## 注意事项

- 需要管理员权限创建和管理Windows会话
- 目前仅支持Windows平台，未来将添加Linux和macOS支持 