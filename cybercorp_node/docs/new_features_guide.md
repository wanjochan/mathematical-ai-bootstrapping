# CyberCorp Node 新功能使用指南

## 快速开始

本指南介绍如何使用CyberCorp Node的新增高级功能，包括鼠标拖动、OCR识别和Win32 API控制。

## 前提条件

1. 确保服务器运行在端口9998
2. 目标客户端已连接（如用户wjchk）
3. 安装必要的依赖：

```bash
# OCR相关
pip install easyocr
pip install pytesseract
pip install paddlepaddle paddleocr

# Win32 API
pip install pywin32

# 视觉模型（可选）
pip install opencv-python
pip install ultralytics  # 如果使用YOLO
```

## 功能详解

### 1. 鼠标拖动功能

适用于验证码拖动、拖放操作等场景。

#### 基础拖动
```python
# 直线拖动
python cybercorp_cli.py command wjchk mouse_drag --params '{
    "start_x": 100,
    "start_y": 200,
    "end_x": 500,
    "end_y": 200,
    "duration": 1.0
}'
```

#### 人性化拖动
```python
# 模拟真实用户的曲线拖动
python cybercorp_cli.py command wjchk mouse_drag --params '{
    "start_x": 100,
    "start_y": 200,
    "end_x": 500,
    "end_y": 200,
    "duration": 2.0,
    "humanize": true
}'
```

#### 右键拖动
```python
# 使用右键进行拖动
python cybercorp_cli.py command wjchk mouse_drag --params '{
    "start_x": 100,
    "start_y": 200,
    "end_x": 300,
    "end_y": 400,
    "button": "right"
}'
```

### 2. OCR文字识别

支持多种OCR引擎，自动选择最优方案。

#### 屏幕区域OCR
```python
# 识别屏幕指定区域
python cybercorp_cli.py command wjchk ocr_screen --params '{
    "x": 100,
    "y": 100,
    "width": 500,
    "height": 200
}'

# 指定OCR引擎
python cybercorp_cli.py command wjchk ocr_screen --params '{
    "x": 100,
    "y": 100,
    "width": 500,
    "height": 200,
    "engine": "easyocr"
}'
```

#### 窗口OCR
```python
# 先查找窗口
python cybercorp_cli.py command wjchk win32_find_window --params '{
    "window_name": "验证码"
}'

# 使用返回的hwnd进行OCR
python cybercorp_cli.py command wjchk ocr_window --params '{
    "hwnd": 123456,
    "engine": "windows"
}'
```

#### 可用的OCR引擎
- `windows` - Windows OCR API（最快，仅Windows 10+）
- `easyocr` - 支持80+语言，精度高
- `tesseract` - 经典开源方案
- `paddleocr` - 中文识别最佳

### 3. Win32 API操作

提供更底层的Windows控制能力。

#### 查找窗口
```python
# 按窗口标题查找
python cybercorp_cli.py command wjchk win32_find_window --params '{
    "window_name": "记事本"
}'

# 按类名查找
python cybercorp_cli.py command wjchk win32_find_window --params '{
    "class_name": "Notepad"
}'
```

#### 高级键盘输入
```python
# 发送组合键和特殊键
python cybercorp_cli.py command wjchk win32_send_keys --params '{
    "keys": "^a{DELETE}Hello World{ENTER}",
    "delay": 0.05
}'

# 特殊键说明：
# ^  = Ctrl
# +  = Shift
# %  = Alt
# {ENTER} = 回车键
# {TAB} = Tab键
# {ESC} = Esc键
# {F1}-{F12} = 功能键
```

## 实战示例

### 示例1：处理滑块验证码

```python
# 1. 截图并识别验证码位置
ocr_result = await forward_command(client_id, 'ocr_screen', {
    'x': 0, 'y': 0, 'width': 800, 'height': 600
})

# 2. 找到滑块和目标位置
slider_pos = find_element_with_text(ocr_result, "拖动滑块")
target_pos = find_element_with_text(ocr_result, "验证")

# 3. 执行拖动
await forward_command(client_id, 'mouse_drag', {
    'start_x': slider_pos['x'],
    'start_y': slider_pos['y'],
    'end_x': target_pos['x'],
    'end_y': target_pos['y'],
    'duration': 2.0,
    'humanize': True
})
```

### 示例2：自动化表单填写

```python
# 1. 查找表单窗口
window_result = await forward_command(client_id, 'win32_find_window', {
    'window_name': '登录'
})

# 2. OCR识别表单字段
ocr_result = await forward_command(client_id, 'ocr_window', {
    'hwnd': window_result['hwnd']
})

# 3. 定位输入框并填写
for field in ocr_result['detections']:
    if '用户名' in field['text']:
        # 点击输入框
        await forward_command(client_id, 'send_mouse_click', {
            'x': field['bbox'][0] + 100,
            'y': field['bbox'][1]
        })
        # 输入内容
        await forward_command(client_id, 'win32_send_keys', {
            'keys': 'myusername'
        })
```

### 示例3：批量操作

创建批量命令文件 `batch_ocr_drag.json`:

```json
[
  {
    "command": "ocr_screen",
    "params": {
      "x": 0,
      "y": 0,
      "width": 1920,
      "height": 1080
    },
    "description": "全屏OCR识别"
  },
  {
    "command": "mouse_drag",
    "params": {
      "start_x": 100,
      "start_y": 500,
      "end_x": 700,
      "end_y": 500,
      "duration": 3.0,
      "humanize": true
    },
    "description": "执行验证码拖动"
  },
  {
    "command": "win32_send_keys",
    "params": {
      "keys": "{ENTER}"
    },
    "description": "确认提交"
  }
]
```

执行批量操作：
```bash
python cybercorp_cli.py batch wjchk batch_ocr_drag.json
```

## 性能优化建议

1. **OCR优化**
   - 使用Windows OCR API获得最快速度
   - 限定识别区域以提高性能
   - 缓存识别结果避免重复

2. **鼠标拖动优化**
   - 短距离使用直线拖动
   - 长距离启用人性化曲线
   - 调整duration参数控制速度

3. **Win32 API优化**
   - 缓存窗口句柄避免重复查找
   - 批量发送按键减少调用次数
   - 使用后台操作避免窗口切换

## 故障排除

### OCR无法识别
- 检查图像质量和对比度
- 尝试不同的OCR引擎
- 调整识别区域大小

### 鼠标拖动失败
- 确保坐标在屏幕范围内
- 增加拖动duration时间
- 检查目标应用是否支持拖放

### Win32 API错误
- 确认目标窗口存在
- 检查权限（需要管理员权限）
- 验证窗口句柄有效性

## 最佳实践

1. **组合使用多种方法**
   ```python
   # 先尝试UIA，失败则用Win32 API，最后用OCR
   try:
       # UIA方法
       result = background_click(element_name)
   except:
       try:
           # Win32 API方法
           hwnd = find_window(window_name)
           send_mouse_click(x, y)
       except:
           # OCR + 鼠标方法
           text_pos = ocr_find_text("按钮")
           mouse_click(text_pos.x, text_pos.y)
   ```

2. **错误处理和重试**
   ```python
   # 使用重试机制
   for attempt in range(3):
       result = mouse_drag(...)
       if verify_drag_success():
           break
       time.sleep(1)
   ```

3. **日志和调试**
   - 保存OCR结果用于分析
   - 记录鼠标轨迹用于优化
   - 截图保存操作前后状态

## 总结

新增的高级功能极大地扩展了CyberCorp Node的能力：

- **鼠标拖动**：解决验证码等复杂交互
- **OCR识别**：让系统能"看懂"界面
- **Win32 API**：提供底层控制能力

这些功能的组合使用，可以应对各种复杂的自动化场景，特别是在处理非标准UI控件时表现出色。