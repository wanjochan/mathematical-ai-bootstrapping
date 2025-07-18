# 桌面窗口管理器

一个用于分析和管理Windows桌面窗口的应用程序。

## 功能特性

- **窗口列表显示**: 左侧面板显示当前用户会话中的所有窗口
- **窗口结构分析**: 右侧面板显示选定窗口的详细结构化数据
- **UI元素识别**: 自动识别窗口中的按钮、文本框、列表等UI元素
- **可视化标注**: 生成带有元素标签的窗口截图
- **实时信息**: 显示窗口位置、大小、状态等详细信息

## 系统要求

- Windows 操作系统
- Python 3.7 或更高版本
- 管理员权限（用于访问某些系统窗口）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行应用程序：
   ```bash
   python main.py
   ```

2. 在左侧窗口列表中选择要分析的窗口

3. 右侧将显示该窗口的基本信息

4. 点击"分析窗口结构"按钮获取详细的结构化数据

5. 查看生成的截图文件（保存在 `screenshots` 目录中）

## 文件结构

```
cybercorp-desktop/
├── main.py              # 主程序入口
├── window_manager.py    # 窗口管理模块
├── window_analyzer.py   # 窗口分析模块
├── requirements.txt     # 依赖包列表
├── README.md           # 说明文档
└── screenshots/        # 截图保存目录
```

## 主要功能模块

### WindowManager
- 枚举所有窗口
- 获取窗口基本信息
- 查找特定窗口
- 获取子窗口列表

### WindowAnalyzer
- 分析窗口UI结构
- 识别UI元素类型
- 截取窗口图像
- 生成标注图像

## 支持的UI元素类型

- Button（按钮）
- TextBox（文本框）
- Label（标签）
- ListBox（列表框）
- ComboBox（下拉框）
- CheckBox（复选框）
- RadioButton（单选按钮）
- Menu（菜单）
- ToolBar（工具栏）
- ScrollBar（滚动条）
- 等等...

## 注意事项

1. 某些系统保护的窗口可能无法分析
2. 需要管理员权限才能访问某些应用程序的窗口
3. 截图文件会保存在本地，请定期清理
4. 分析复杂窗口可能需要一些时间

## 故障排除

如果遇到问题：

1. 确保已安装所有依赖包
2. 以管理员身份运行程序
3. 检查目标窗口是否可见且未被遮挡
4. 查看控制台输出的错误信息

## 🔥 热重载功能

**新增热重载版本**，支持实时更新界面组件，无需重启程序！

### 启动热重载版本
```bash
python main_hot_reload.py
# 或双击
run_hot_reload.bat
```

### 热重载特性
- **文件监控**: 自动监控 `ui_components.py` 文件变化
- **API接口**: 提供HTTP API手动触发重载
- **状态保持**: 重载时保持窗口选择状态和分析内容
- **组件化**: 支持单独重载工具栏、列表面板、分析面板

### 使用方法

1. **自动重载**: 修改 `ui_components.py` 保存后自动触发
2. **手动重载**: 点击界面上的"⚡ 热重载"按钮
3. **API重载**: 
   ```bash
   # 查看状态
   curl http://localhost:8888/status
   
   # 重载所有组件
   curl -X POST http://localhost:8888/reload -H "Content-Type: application/json" -d '{"component":"all"}'
   
   # 重载特定组件
   curl -X POST http://localhost:8888/reload -H "Content-Type: application/json" -d '{"component":"toolbar"}'
   ```

4. **测试工具**: 
   ```bash
   python test_hot_reload.py
   ```

### 文件结构（热重载版）

```
cybercorp-desktop/
├── main.py                    # 原版主程序
├── main_hot_reload.py         # 🔥 热重载版主程序
├── ui_components.py           # 🔥 可重载的UI组件
├── hot_reload.py              # 🔥 热重载核心模块
├── test_hot_reload.py         # 🔥 热重载测试工具
├── run_hot_reload.bat         # 🔥 热重载版启动脚本
├── window_manager.py          # 窗口管理模块
├── window_analyzer.py         # 窗口分析模块
├── logger.py                  # 日志模块
├── requirements.txt           # 依赖包列表
└── logs/                      # 日志文件目录
```

### 开发工作流

1. 启动热重载版程序: `python main_hot_reload.py`
2. 修改 `ui_components.py` 中的组件代码
3. 保存文件，程序自动重载更新的组件
4. 实时看到界面变化，无需重启程序

### API接口说明

- `GET /status` - 查看重载器状态
- `POST /reload` - 触发组件重载
  - `{"component": "all"}` - 重载所有组件
  - `{"component": "toolbar"}` - 重载工具栏
  - `{"component": "window_list_panel"}` - 重载窗口列表面板  
  - `{"component": "analysis_panel"}` - 重载分析面板

## 扩展功能

未来可能添加的功能：
- OCR文本识别
- 自动化操作录制
- 窗口操作回放
- 更智能的元素识别
- 热重载支持更多文件类型
- 配置文件驱动的界面布局 