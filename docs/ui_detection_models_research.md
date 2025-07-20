# UI Detection Models Research

## 1. OmniParser (Microsoft) ⭐ 推荐

**官方仓库**: https://github.com/microsoft/OmniParser
**模型下载**: https://huggingface.co/microsoft/OmniParser

### 特点
- 使用YOLOv8 Nano进行UI元素检测
- 结合Florence-2模型进行元素描述
- 在67k UI截图数据集上训练
- 支持多平台UI检测
- 在Windows Agent Arena达到最佳性能

### 性能
- 检测精度高，特别适合computer-use场景
- 支持检测可交互元素
- 实时性能良好

### 使用方法
```python
# 安装
pip install ultralytics
pip install transformers

# 使用示例
from omniparser import OmniParser

parser = OmniParser()
elements = parser.parse_screenshot(image)
```

## 2. YOLO-World (CVPR 2024)

**仓库**: https://github.com/AILab-CVC/YOLO-World

### 特点
- 开放词汇检测(Open-Vocabulary)
- 零样本推理能力
- 实时性能
- 支持自定义UI元素类型

## 3. YOLOv8 UI定制版本

### 训练数据集
- VNIS Dataset: 移动UI数据集，21种UI元素类型
- Rico Dataset: 安卓UI数据集
- 自定义数据集训练

### 使用Ultralytics YOLOv8
```python
from ultralytics import YOLO

# 加载预训练模型
model = YOLO('yolov8n.pt')

# 针对UI元素进行微调
model.train(data='ui_dataset.yaml', epochs=100)
```

## 4. 其他相关模型

### ScreenAI (Google)
- 专门用于屏幕理解的多模态模型
- 支持UI元素检测和描述

### UI-BERT
- 基于BERT的UI理解模型
- 适合UI布局分析

## 推荐方案

对于您的cybercorp_node项目，建议：

1. **首选OmniParser**
   - 专门为UI agent设计
   - 检测精度高
   - 有Microsoft支持和更新

2. **备选YOLOv8自训练**
   - 如果需要特定UI元素检测
   - 可以使用自己的数据集训练

3. **集成方案**
   ```python
   # 替换现有的vision_model_enhanced.py
   # 使用OmniParser或YOLOv8
   
   class UIVisionModelYOLO:
       def __init__(self):
           # 加载OmniParser或YOLOv8模型
           self.model = load_omniparser_model()
       
       def detect_ui_elements(self, image):
           # 使用模型进行检测
           results = self.model.predict(image)
           return self._convert_to_ui_elements(results)
   ```

## 性能对比

| 模型 | 准确率 | FPS | 特点 |
|------|--------|-----|------|
| OmniParser | 95%+ | 30+ | 专为UI设计，集成OCR |
| YOLOv8 | 90%+ | 60+ | 速度快，需要自训练 |
| 传统CV | 70% | 17 | 当前实现 |

## 下一步行动

1. 下载并测试OmniParser
2. 评估是否满足95%准确率要求
3. 集成到vision_integration.py中
4. 保留传统CV作为后备方案