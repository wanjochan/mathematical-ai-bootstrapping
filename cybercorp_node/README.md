# CyberCorp Node - 跨用户会话控制系统

一个强大的系统，用于跨不同 Windows 用户会话控制 VSCode 和开发环境。

## 核心特性

- **稳定的 WebSocket 连接**：自动重连、心跳监控
- **跨用户会话支持**：控制其他用户会话中的 VSCode
- **VSCode 集成**：读取内容、发送按键、执行命令
- **UI 自动化**：即使在后台也能访问窗口内容
- **远程控制**：鼠标、键盘和截屏功能
- **热重载支持**：服务器端插件和配置热更新
- **后台 RPA**：无需切换前台窗口的自动化操作

## 系统架构

```
┌─────────────────────┐         ┌─────────────────────┐
│   中控端 (Server)    │         │   受控端 (Client)    │
│                     │         │  (不同用户会话)      │
│  ┌───────────────┐  │         │  ┌───────────────┐  │
│  │ CyberCorp     │  │ Network │  │ CyberCorp     │  │
│  │ Server        │◄─┼─────────┼──┤ Client        │  │
│  │ (Port 9998)   │  │   WS    │  │               │  │
│  └───────────────┘  │         │  └───────┬───────┘  │
│                     │         │          │           │
│  ┌───────────────┐  │         │  ┌───────▼───────┐  │
│  │ Hot Reload    │  │         │  │ VSCode        │  │
│  │ Plugins       │  │         │  │ (Controlled)  │  │
│  └───────────────┘  │         │  └───────────────┘  │
└─────────────────────┘         └─────────────────────┘
```

## 快速开始

### 1. 配置端口 (config.ini)

```ini
[server]
port = 9998

[client]
server_port = 9998
```

### 2. 启动中控端

```batch
# 标准服务器
start_server_clean.bat

# 或热重载服务器（推荐）
start_hotreload_server.bat
```

### 3. 启动受控端

在目标用户会话中：
```batch
start_client_clean.bat
# 或
client_9998.bat
```

### 4. 使用统一工具

#### 4.1 统一 CLI 工具 (cybercorp_cli.py)

```bash
# 查看系统状态
python cybercorp_cli.py status

# 列出所有客户端
python cybercorp_cli.py list -c

# 发送单个命令
python cybercorp_cli.py command wjchk get_processes

# 交互式控制
python cybercorp_cli.py control wjchk

# Roo Code 操作
python cybercorp_cli.py roo wjchk send -m "你的消息"
python cybercorp_cli.py roo wjchk check

# 批量执行命令
python cybercorp_cli.py batch wjchk examples/batch_commands.json
```

#### 4.2 统一测试套件 (cybercorp_test_suite.py)

```bash
# 查看可用测试
python cybercorp_test_suite.py

# 运行单个测试
python cybercorp_test_suite.py status -t wjchk

# 运行多个测试
python cybercorp_test_suite.py status list ocr drag -t wjchk

# 并行运行测试
python cybercorp_test_suite.py status list processes windows --parallel -t wjchk

# 压力测试
python cybercorp_test_suite.py stress --iterations 100 --command get_screen_size -t wjchk

# 带参数的测试
python cybercorp_test_suite.py ocr --screen --x 100 --y 100 --width 500 --height 300 -t wjchk
```

## 新的工具类架构

### 工具类说明

系统已重构为模块化的工具类，位于 `utils/` 目录：

1. **CyberCorpClient** - WebSocket 客户端基类
   - 处理连接、注册、心跳
   - 统一的请求/响应模式

2. **ClientManager** - 客户端管理
   - 查找和列出客户端
   - 等待客户端连接
   - 按能力过滤客户端

3. **CommandForwarder** - 命令转发
   - 向目标客户端发送命令
   - 批量执行和重试机制
   - 广播命令到多个客户端

4. **DataPersistence** - 数据持久化
   - 时间戳文件保存
   - JSON 数据管理
   - 文件比较和清理

5. **VSCodeUIAnalyzer** - UI 结构分析
   - 解析 VSCode UI 元素
   - 查找 Roo Code 组件
   - 提取文本内容

6. **VSCodeAutomation** - VSCode 自动化
   - 后台输入和点击
   - 窗口内容获取
   - Roo Code 交互

7. **ResponseHandler** - 响应处理
   - 统一的错误处理
   - 重试机制
   - 响应验证

### 新增高级功能模块

8. **Win32Backend** - Windows API 集成
   - 窗口管理和控制
   - 鼠标拖动（支持验证码）
   - 高级键盘输入
   - 窗口截图

9. **OCRBackend** - 多引擎OCR支持
   - Windows OCR API（最快）
   - EasyOCR（多语言）
   - Tesseract（经典）
   - PaddleOCR（中文优化）

10. **UIVisionModel** - 视觉识别模型
    - UI元素检测
    - 布局分析
    - 实时性能（30+ FPS）
    - 轻量级实现

11. **ParallelExecutor** - 并行任务执行框架
    - 依赖管理
    - 优先级调度
    - 超时控制
    - 支持同步/异步任务

## RPA 经验总结

### 1. 后台操作优于前台切换

**问题**：窗口激活和前台切换容易失败，引入不可预知的错误。

**解决方案**：使用 UI Automation 的后台 API：
```bash
# 后台输入文本（无需激活窗口）
python cybercorp_cli.py command wjchk background_input --params '{"element_name":"Type your task here...", "text":"你的消息"}'

# 后台点击按钮
python cybercorp_cli.py command wjchk background_click --params '{"element_name":"Send message"}'
```

### 2. UI 元素定位策略

**最佳实践**：
- 优先使用元素名称和类型组合定位
- 保存 UI 结构快照用于调试
- 实现多种定位策略的降级机制

### 3. 任务追踪和验证

**问题**：发送的任务可能被其他任务替换或进入队列。

**解决方案**：
- 操作前后保存 UI 状态
- 实现任务 ID 和状态追踪
- 定期检查任务处理结果

## 高级功能

### 热重载系统

服务器支持插件热加载，无需重启：

1. 将插件放入 `plugins/` 目录
2. 插件自动加载并注册命令
3. 配置文件 `server_config.json` 修改后自动生效

### 后台 RPA 操作

使用 `background_roo_rpa.py` 实现无窗口切换的自动化：

```python
# 完整的后台 Roo Code 交互
from background_roo_rpa import BackgroundRooCodeRPA

rpa = BackgroundRooCodeRPA("wjchk")
await rpa.execute_background_task("你的任务描述")
```

### 插件开发

创建新插件示例 (`plugins/my_plugin.py`)：

```python
from server_hotreload import register_command

def handle_my_command(client, params):
    # 处理逻辑
    return {'success': True, 'result': 'Done'}

register_command('my_command', handle_my_command)
```

## 可用命令列表

### 系统信息类
- `get_system_info` - 获取系统信息
- `get_processes` - 获取进程列表
- `get_windows` - 获取窗口列表
- `get_screen_size` - 获取屏幕尺寸

### VSCode 控制类
- `vscode_get_content` - 获取 VSCode 内容结构
- `vscode_type_text` - 输入文本
- `vscode_send_command` - 执行 VSCode 命令
- `activate_window` - 激活窗口（不推荐）

### 后台操作类（推荐）
- `background_input` - 后台输入文本
- `background_click` - 后台点击元素
- `send_keys` - 发送按键组合
- `take_screenshot` - 截屏

### 高级控制类（新增）
- `mouse_drag` - 鼠标拖动（支持验证码）
- `ocr_screen` - 屏幕区域文字识别
- `ocr_window` - 窗口文字识别
- `win32_find_window` - 查找特定窗口
- `win32_send_keys` - Win32 API 发送按键

## 故障排除

### 客户端无法连接
1. 检查 `config.ini` 端口设置（应为 9998）
2. 确认防火墙允许该端口
3. 验证服务器正在运行：`python check_status.py`

### 找不到 VSCode
1. 确保 VSCode 在目标会话中运行
2. 客户端必须在 VSCode 相同会话中
3. 检查 UI 自动化权限

### RPA 操作失败
1. 使用后台操作而非前台激活
2. 保存 UI 结构用于调试（查看 `var/` 目录）
3. 实现重试机制和多种操作策略

## 最佳实践

1. **使用配置文件**：所有端口和设置通过 `config.ini` 管理
2. **后台操作优先**：避免窗口切换，使用 `background_*` 命令
3. **调试文件管理**：临时文件保存在 `var/` 目录，已加入 `.gitignore`
4. **热重载开发**：使用 `server_hotreload.py` 支持快速迭代
5. **统一工具使用**：
   - 操作命令：`cybercorp_cli.py`
   - 测试执行：`cybercorp_test_suite.py`
   - 并行任务：使用 `ParallelExecutor` 框架
6. **日志管理**：客户端日志包含参数和结果采样，自动截断长内容

## 开发路线图

- [x] WebSocket 稳定连接
- [x] 跨会话控制
- [x] 热重载支持
- [x] 后台 RPA 操作
- [x] 配置文件管理
- [x] 抽象代码到工具类架构
- [x] 统一 CLI 工具 (cybercorp_cli.py)
- [ ] 任务队列和状态追踪
- [ ] 可视化管理界面
- [ ] 录制和回放功能
- [ ] 多 VSCode 实例支持
- [ ] 智能等待和重试机制

## 安全注意事项

1. **网络安全**：当前无认证机制，仅在可信网络使用
2. **权限控制**：客户端需要 UI 自动化权限
3. **会话隔离**：跨会话操作需要适当的系统权限
4. **敏感信息**：避免在代码中硬编码敏感信息

## 从旧脚本迁移

如果你之前使用单独的测试脚本，请迁移到新的 CLI 工具：

```bash
# 运行迁移向导
python migrate_to_cli.py

# 查看 CLI 帮助
python cybercorp_cli.py --help
```

主要变化：
- 所有 `test_*.py` 脚本功能集成到 `cybercorp_cli.py`
- 通用功能抽象到 `utils/` 工具类
- 统一的错误处理和输出格式
- 支持批量操作和交互模式

## 新功能使用示例

### 鼠标拖动（验证码场景）
```bash
# 执行滑块验证码拖动
python cybercorp_cli.py command wjchk mouse_drag --params '{
    "start_x": 100, "start_y": 200,
    "end_x": 400, "end_y": 200,
    "duration": 2.0,
    "humanize": true
}'
```

### OCR文字识别
```bash
# 识别屏幕区域文字
python cybercorp_cli.py command wjchk ocr_screen --params '{
    "x": 100, "y": 100,
    "width": 500, "height": 300,
    "engine": "windows"
}'

# 识别特定窗口的文字
python cybercorp_cli.py command wjchk ocr_window --params '{
    "hwnd": 123456,
    "engine": "easyocr"
}'
```

### Win32 API操作
```bash
# 查找窗口
python cybercorp_cli.py command wjchk win32_find_window --params '{
    "window_name": "验证码"
}'

# 发送特殊按键
python cybercorp_cli.py command wjchk win32_send_keys --params '{
    "keys": "^a{DELETE}Hello World{ENTER}",
    "delay": 0.05
}'
```

## 贡献指南

1. 使用工具类而非重复代码
2. 新功能通过扩展 CLI 命令实现
3. 插件放在 `plugins/` 目录
4. 调试输出保存到 `var/` 目录
5. 更新文档记录新功能