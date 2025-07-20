# 工作笔记 vision

本文档包含工作流 vision 的上下文、经验和工作会话笔记，以保持AI会话之间的连续性。

## 工作流信息
- 工作ID: vision
- 创建时间: 2025-07-20
- 关联计划: [工作计划文档](workplan_vision.md)
- 特别注意：不要做历史纪录，只更新最后结果！

## 会话

### 会话：2025-07-20

#### 上下文
- 基于cybercorp实战经验，识别出窗口结构化解析是性能瓶颈
- 用户明确需求：开发独立的工具组件，便于后续集成
- 从大型视觉缓存系统简化为专注的解析工具

#### 设计理念
- **单一职责**：只做窗口内容到结构化数据的转换
- **模块化设计**：作为独立组件，易于集成到现有系统
- **渐进式开发**：先实现核心功能，再逐步优化

#### 技术选型思考

1. **截图方案对比**
   ```python
   # 方案A: Win32 API (当前使用)
   - 优点：稳定、兼容性好
   - 缺点：速度较慢
   
   # 方案B: Desktop Duplication API
   - 优点：速度快、低延迟
   - 缺点：需要Windows 8+
   
   # 方案C: BitBlt优化
   - 优点：平衡性能和兼容性
   - 缺点：某些应用可能黑屏
   ```

2. **识别方案选择**
   - **轻量级优先**：MobileNet/EfficientNet系列
   - **专用模型**：针对UI元素训练的专门模型
   - **混合策略**：传统CV + 深度学习结合

3. **输出格式设计**
   ```json
   {
     "metadata": {
       "timestamp": "2025-07-20T10:00:00",
       "window_handle": 12345,
       "processing_time_ms": 850
     },
     "structure": {
       "type": "window",
       "title": "应用标题",
       "bounds": [0, 0, 1920, 1080],
       "children": [
         {
           "type": "toolbar",
           "bounds": [0, 0, 1920, 40],
           "children": [...]
         },
         {
           "type": "content_area",
           "bounds": [0, 40, 1920, 1040],
           "children": [...]
         }
       ]
     },
     "elements": [
       {
         "id": "elem_001",
         "type": "button",
         "text": "保存",
         "bounds": [100, 50, 80, 30],
         "confidence": 0.98,
         "properties": {
           "clickable": true,
           "enabled": true
         }
       }
     ]
   }
   ```

#### 实现策略

1. **第一阶段：基础框架**
   - 实现基本的截图功能
   - 简单的边缘检测和区域划分
   - 基础的JSON输出

2. **第二阶段：智能识别**
   - 集成OCR功能
   - UI元素分类
   - 层次结构推断

3. **第三阶段：性能优化**
   - 增量更新支持
   - 缓存机制
   - GPU加速（可选）

#### 关键挑战

1. **准确性挑战**
   - 不同UI框架的视觉差异
   - 自定义控件的识别
   - 动态内容的处理

2. **性能挑战**
   - 大窗口的处理速度
   - 实时更新需求
   - 内存占用控制

3. **兼容性挑战**
   - 不同Windows版本
   - 高DPI支持
   - 多显示器场景

#### 创新思路

1. **智能采样**
   - 根据窗口类型自适应采样率
   - 关注区域优先处理
   - 变化检测触发更新

2. **模板学习**
   - 自动学习常见应用的UI模式
   - 建立应用特定的识别模板
   - 提高特定场景的准确率

3. **轻量级标注**
   - 使用简单的标注快速训练
   - 用户反馈改进识别
   - 持续优化模型

#### 状态追踪更新
- 当前状态: PLANNING
- 状态变更原因: 开始规划窗口内容结构化解析工具
- 下一步计划: 
  1. 完成技术原型验证
  2. 确定最终技术方案
  3. 开始MVP开发

## 知识库

### 相关技术资源
- Windows Graphics Capture API (Windows 10+)
- UI Automation vs 视觉识别对比
- 轻量级目标检测模型汇总

### 性能基准
- 纯UIA提取: 10-30秒
- 目标性能: <1秒
- 实时场景: <100ms

### 竞品分析
- Power Automate Desktop: 使用UIA + 图像识别
- Selenium: DOM解析为主
- Appium: 原生API + 图像识别

## 参考资料

- [Windows.Graphics.Capture namespace](https://docs.microsoft.com/en-us/uwp/api/windows.graphics.capture)
- [MobileNet论文](https://arxiv.org/abs/1704.04861)
- [UI元素检测数据集](https://github.com/google-research-datasets/uibert)

## 改进建议

### 基于本次执行的建议
- 建议1：先实现Windows平台，后续考虑跨平台
- 建议2：优先支持主流应用（浏览器、IDE、Office）
- 建议3：提供简单的可视化调试工具

### 模板改进建议
- 将子任务切分得更细，便于并行开发
- 增加更多技术决策点的记录
- 添加代码示例和伪代码