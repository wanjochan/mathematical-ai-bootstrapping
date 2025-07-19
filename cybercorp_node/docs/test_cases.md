# CyberCorp Node 测试用例文档

## 1. 基础功能测试

### 1.1 服务器状态测试
```bash
# 测试服务器连接
python cybercorp_test_suite.py status

# 详细状态信息
python cybercorp_test_suite.py status -v
```

### 1.2 客户端列表测试
```bash
# 列出所有客户端
python cybercorp_test_suite.py list

# 按能力分组
python cybercorp_test_suite.py list --group-by capability
```

### 1.3 系统信息测试
```bash
# 获取目标客户端系统信息
python cybercorp_test_suite.py info -t wjchk

# 保存结果
python cybercorp_test_suite.py info -t wjchk --save
```

## 2. 控制功能测试

### 2.1 基础控制测试
```bash
# 测试所有基础命令
python cybercorp_test_suite.py control -t wjchk

# 测试特定命令
python cybercorp_test_suite.py control -t wjchk -c get_screen_size

# 带参数的命令
python cybercorp_test_suite.py control -t wjchk -c send_keys --params '{"keys": "Hello World"}'
```

### 2.2 窗口操作测试
```bash
# 获取所有窗口
python cybercorp_test_suite.py windows -t wjchk

# 限制输出
python cybercorp_test_suite.py windows -t wjchk --limit
```

### 2.3 进程管理测试
```bash
# 获取进程列表
python cybercorp_test_suite.py processes -t wjchk

# 完整进程列表
python cybercorp_test_suite.py processes -t wjchk --full
```

## 3. VSCode 集成测试

### 3.1 VSCode 内容测试
```bash
# 获取VSCode结构
python cybercorp_test_suite.py vscode -t wjchk

# 包含完整内容
python cybercorp_test_suite.py vscode -t wjchk --full
```

### 3.2 Roo Code 测试
```bash
# 检查Roo Code状态
python cybercorp_test_suite.py roo -t wjchk

# 发送消息到Roo Code
python cybercorp_test_suite.py roo -t wjchk --message "分析当前代码结构"
```

## 4. 高级功能测试

### 4.1 鼠标拖动测试
```bash
# 默认拖动测试
python cybercorp_test_suite.py drag -t wjchk

# 自定义拖动参数
python cybercorp_test_suite.py drag -t wjchk \
    --start-x 100 --start-y 200 \
    --end-x 500 --end-y 200 \
    --duration 2.0 --humanize

# 右键拖动
python cybercorp_test_suite.py drag -t wjchk --button right
```

### 4.2 OCR 测试
```bash
# 屏幕OCR测试
python cybercorp_test_suite.py ocr -t wjchk --screen

# 指定区域OCR
python cybercorp_test_suite.py ocr -t wjchk --screen \
    -x 100 -y 100 --width 600 --height 400

# 窗口OCR测试
python cybercorp_test_suite.py ocr -t wjchk --window "记事本"

# 指定OCR引擎
python cybercorp_test_suite.py ocr -t wjchk --screen --engine easyocr
```

### 4.3 Win32 API 测试
```bash
# 查找窗口
python cybercorp_test_suite.py win32 -t wjchk --find-window "Visual Studio Code"

# 发送按键
python cybercorp_test_suite.py win32 -t wjchk --send-keys "^a{DELETE}Hello{ENTER}"
```

### 4.4 视觉模型测试
```bash
# 本地视觉模型测试
python cybercorp_test_suite.py vision

# 性能基准测试
python cybercorp_test_suite.py vision --iterations 50
```

## 5. 性能和压力测试

### 5.1 并行执行测试
```bash
# 并行执行多个测试
python cybercorp_test_suite.py parallel -t wjchk

# 自定义并行测试
python cybercorp_test_suite.py status list windows processes --parallel -t wjchk
```

### 5.2 压力测试
```bash
# 默认压力测试
python cybercorp_test_suite.py stress -t wjchk

# 自定义压力测试
python cybercorp_test_suite.py stress -t wjchk \
    --iterations 100 \
    --command get_screen_size

# 高强度测试
python cybercorp_test_suite.py stress -t wjchk \
    --iterations 1000 \
    --command vscode_get_content
```

## 6. 组合测试场景

### 6.1 完整功能测试
```bash
# 运行所有基础测试
python cybercorp_test_suite.py status list info control windows processes -t wjchk --save
```

### 6.2 RPA 功能测试
```bash
# 测试所有RPA相关功能
python cybercorp_test_suite.py vscode roo ocr drag win32 -t wjchk --parallel
```

### 6.3 验证码处理模拟
```bash
# 1. 截图识别
python cybercorp_test_suite.py ocr -t wjchk --screen --save

# 2. 执行拖动
python cybercorp_test_suite.py drag -t wjchk \
    --start-x 100 --start-y 300 \
    --end-x 400 --end-y 300 \
    --humanize --duration 3.0
```

## 7. 调试和故障排除

### 7.1 详细日志模式
```bash
# 启用详细日志
python cybercorp_test_suite.py status -t wjchk -v

# 保存测试结果
python cybercorp_test_suite.py ocr drag -t wjchk --save -v
```

### 7.2 超时设置
```bash
# 自定义超时
python cybercorp_test_suite.py control -t wjchk --timeout 30.0

# 长时间操作
python cybercorp_test_suite.py ocr -t wjchk --screen --timeout 60.0
```

## 8. 批量测试执行

### 8.1 使用批量命令文件

创建 `test_batch.json`:
```json
[
  {
    "command": "get_system_info",
    "description": "系统信息"
  },
  {
    "command": "ocr_screen",
    "params": {
      "x": 0, "y": 0,
      "width": 1920, "height": 1080
    },
    "description": "全屏OCR"
  },
  {
    "command": "mouse_drag",
    "params": {
      "start_x": 100, "start_y": 200,
      "end_x": 500, "end_y": 200,
      "duration": 2.0,
      "humanize": true
    },
    "description": "拖动测试"
  }
]
```

执行：
```bash
python cybercorp_cli.py batch wjchk test_batch.json
```

### 8.2 并行批量测试

使用 Python 脚本：
```python
from utils.parallel_executor import ParallelExecutor, TaskBuilder

# 创建任务
builder = TaskBuilder()
builder.add_parallel([
    ("OCR测试", run_ocr_test, ()),
    ("拖动测试", run_drag_test, ()),
    ("Win32测试", run_win32_test, ())
])

# 执行
executor = ParallelExecutor(max_workers=3)
executor.add_tasks(builder.build())
results = await executor.execute_all()
```

## 9. 持续集成测试

### 9.1 基础健康检查
```bash
# 每日健康检查
python cybercorp_test_suite.py status list -v
```

### 9.2 功能回归测试
```bash
# 核心功能测试
python cybercorp_test_suite.py control vscode ocr drag -t wjchk --save
```

### 9.3 性能基准测试
```bash
# 性能基准
python cybercorp_test_suite.py stress parallel vision --save
```

## 10. 测试结果分析

测试结果保存在 `var/` 目录：
- `test_results_*.json` - 测试结果
- `ocr_*.json` - OCR识别结果
- `roo_*.json` - Roo Code状态
- `test_suite_*.log` - 详细日志

分析工具：
```python
from utils.data_persistence import DataPersistence

# 加载最新结果
persistence = DataPersistence()
latest_result = persistence.load_latest("test_results")

# 比较两次测试
comparison = persistence.compare_files("result1.json", "result2.json")
```