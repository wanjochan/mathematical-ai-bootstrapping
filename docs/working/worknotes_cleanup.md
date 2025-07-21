# Work Notes: CyberCorp Node 清理重构
**Work ID**: cleanup
**Created**: 2025-07-21
**Updated**: 2025-07-21

## 上下文

用户反馈Cursor交互失败太多，要求梳理cybercorp_node目录并清理旧代码。经过分析发现：

1. **目录结构混乱**：
   - 大量测试文件散布在根目录
   - 存在违规命名（*_optimized, *_backup）
   - 临时文件未清理

2. **代码冗余**：
   - 多个版本的vision_model实现
   - 重复的cursor控制器
   - 废弃的脚本仍保留

3. **违反workflow.md规范**：
   - 未遵循src/bin/scripts标准结构
   - 存在禁止的命名方式
   - 文档分散，未集中管理

## 关键发现

### 核心组件识别：
1. **远程控制系统**：基于WebSocket的客户端-服务器架构
2. **视觉分析**：支持多种后端（YOLO, OCR等）
3. **窗口自动化**：Win32 API封装
4. **Cursor IDE集成**：专门的控制器实现

### 问题根源：
- 快速迭代导致的技术债务
- 缺乏统一的代码组织规范
- 测试代码与生产代码混杂

## 决策记录

1. **采用标准目录结构**：严格遵循workflow.md的src/bin/scripts规范
2. **模块化重构**：将分散的功能整合为清晰的模块
3. **保持向后兼容**：确保现有功能在重构后仍可用

## 经验教训

1. **文件命名**：绝不使用状态后缀（fixed, updated等）
2. **版本管理**：用Git而非文件后缀管理版本
3. **测试隔离**：测试代码必须在tests/目录

## 待解决问题

1. 如何处理现有的配置文件？
   - config.ini和server_config.json保留在根目录
2. 日志文件应该放在哪里？
   - logs/目录已存在，保持现有结构
3. 插件系统是否需要保留？
   - plugins/目录保留，提供扩展能力

## 重要发现

1. **import路径问题**：所有文件都需要更新import语句
2. **循环依赖**：remote_control.py中的lazy import表明存在循环依赖
3. **模块化不足**：vision模型有太多变体，需要统一接口

## 已完成的清理

### 目录结构重组：
```
cybercorp_node/
├── src/              # 源代码
│   ├── core/        # 核心功能
│   ├── vision/      # 视觉分析
│   └── automation/  # 自动化工具
├── scripts/         # 脚本
├── tests/           # 测试
└── docs/            # 文档
```

### 删除的文件：
- 所有临时文件（*.png, *.log, 临时json）
- 违规命名文件（*_optimized, *_backup等）
- 冗余的vision模型变体
- 废弃的启动器脚本
- deprecated_scripts和legacy_batch目录

## 下一步行动

1. 更新所有Python文件的import路径
2. 合并vision模型功能到统一接口
3. 统一cursor控制器接口
4. 测试确保功能正常