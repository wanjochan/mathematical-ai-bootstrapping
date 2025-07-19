# CyberCorp Node 技术改进方案

## 1. Windows系统API集成方案

### 1.1 为什么需要Win32 API

虽然UI Automation (UIA) 提供了强大的UI元素访问能力，但在某些场景下存在限制：
- 某些应用程序不支持UIA
- 需要更底层的系统控制（如全局热键、系统钩子）
- 性能要求高的场景（UIA可能较慢）
- 需要访问窗口消息、进程内存等底层功能

### 1.2 Win32 API 集成功能清单

#### 窗口管理
- `FindWindow` / `FindWindowEx` - 查找窗口
- `GetWindowText` / `SetWindowText` - 获取/设置窗口标题
- `ShowWindow` - 控制窗口显示状态
- `SetForegroundWindow` - 激活窗口
- `GetWindowRect` - 获取窗口位置和大小
- `MoveWindow` - 移动和调整窗口大小

#### 进程和线程
- `OpenProcess` - 打开进程句柄
- `ReadProcessMemory` - 读取进程内存
- `GetModuleHandle` - 获取模块句柄
- `GetProcAddress` - 获取函数地址

#### 输入模拟
- `SendInput` - 发送键盘和鼠标输入
- `mouse_event` - 鼠标事件（包括拖动）
- `keybd_event` - 键盘事件
- `SetCursorPos` / `GetCursorPos` - 设置/获取鼠标位置

#### 屏幕捕获
- `GetDC` / `BitBlt` - 屏幕截图
- `PrintWindow` - 窗口截图（即使被遮挡）

#### 系统钩子
- `SetWindowsHookEx` - 设置系统钩子
- `CallNextHookEx` - 调用下一个钩子
- `UnhookWindowsHookEx` - 卸载钩子

## 2. OCR解决方案研究

### 2.1 候选方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **Tesseract** | - 开源免费<br>- 支持多语言<br>- 成熟稳定 | - 速度较慢<br>- 需要预处理<br>- 准确率一般 | 通用文本识别 |
| **PaddleOCR** | - 中文识别优秀<br>- 速度快<br>- 轻量级 | - 部署复杂<br>- 依赖较多 | 中文为主的场景 |
| **EasyOCR** | - 易于使用<br>- 支持80+语言<br>- GPU加速 | - 模型较大<br>- 首次加载慢 | 多语言场景 |
| **Windows OCR API** | - 系统原生<br>- 无需额外依赖<br>- 性能好 | - 仅Windows 10+<br>- 功能有限 | Windows原生应用 |
| **TrOCR (Transformer)** | - 准确率高<br>- 处理复杂场景好 | - 资源消耗大<br>- 需要GPU | 高精度要求 |

### 2.2 推荐方案

**主方案**：Windows OCR API（快速、轻量）
- 用于常规UI文本识别
- 零依赖，易于部署

**备选方案**：EasyOCR（功能全面）
- 用于复杂场景和多语言支持
- 可选GPU加速

**探索方案**：轻量级专用模型
- 研究 MobileNet + CRNN 组合
- 针对UI界面优化

## 3. 鼠标拖动功能设计

### 3.1 应用场景
- 滑块验证码
- 拖放操作（文件、UI元素）
- 绘图和手势
- 窗口调整

### 3.2 实现方案

```python
# 基础拖动API设计
class MouseDragAPI:
    def drag(self, start_x, start_y, end_x, end_y, duration=1.0):
        """基础拖动"""
        
    def drag_with_curve(self, start, end, control_points, duration=1.0):
        """贝塞尔曲线拖动（模拟人类）"""
        
    def drag_element(self, element, offset_x, offset_y):
        """拖动UI元素"""
        
    def drag_and_drop(self, source_element, target_element):
        """拖放操作"""
```

### 3.3 人性化模拟
- 添加随机抖动
- 变速运动（先快后慢）
- 贝塞尔曲线路径
- 随机停顿

## 4. 视觉模型架构设计

### 4.1 参考项目
- **UI-TARS**: 基于Transformer的UI理解模型
- **OmniParser**: 多模态UI解析器

### 4.2 目标架构

```
输入层（截图）
    ↓
特征提取（CNN/ViT）
    ↓
区域检测（YOLO/Faster-RCNN）
    ↓
元素分类（ResNet）
    ↓
文本识别（OCR）
    ↓
结构化输出（JSON）
```

### 4.3 性能目标
- 帧率：15-30 FPS
- 延迟：< 100ms
- 准确率：> 95%
- 内存占用：< 500MB

## 5. 统一接口设计

### 5.1 分层架构

```
应用层（高级API）
    ├── find_element(策略选择)
    ├── interact_with_element(动作执行)
    └── extract_content(内容提取)
    
策略层（智能选择）
    ├── UIA策略
    ├── Win32策略
    ├── OCR策略
    └── 视觉模型策略
    
执行层（具体实现）
    ├── UIA Backend
    ├── Win32 Backend
    ├── OCR Backend
    └── Vision Backend
```

### 5.2 策略选择逻辑

1. **优先级顺序**：
   - UIA（如果支持）
   - Win32 API（窗口级操作）
   - OCR（文本识别）
   - 视觉模型（复杂场景）

2. **组合使用**：
   - UIA + Win32：提高成功率
   - Win32 + OCR：处理非标准控件
   - 所有方法：容错和验证

## 6. 实施计划

### Phase 1：基础集成（1-2周）
- [ ] Win32 API基础封装
- [ ] 简单OCR集成（Windows OCR API）
- [ ] 鼠标拖动基础功能

### Phase 2：功能完善（2-3周）
- [ ] 高级Win32功能
- [ ] EasyOCR集成
- [ ] 人性化鼠标模拟

### Phase 3：视觉模型（4-6周）
- [ ] 模型选型和训练
- [ ] 实时推理优化
- [ ] 统一接口实现

### Phase 4：优化和测试（2周）
- [ ] 性能优化
- [ ] 稳定性测试
- [ ] 文档完善

## 7. 技术挑战和解决方案

### 7.1 性能优化
- **问题**：多种方法组合可能导致延迟
- **方案**：
  - 异步执行
  - 缓存机制
  - 智能预测

### 7.2 兼容性
- **问题**：不同Windows版本API差异
- **方案**：
  - 运行时检测
  - 降级策略
  - polyfill实现

### 7.3 安全性
- **问题**：底层API可能被杀软拦截
- **方案**：
  - 数字签名
  - 白名单申请
  - 用户授权机制