# Work Plan: CyberCorp Node 代码库清理重构
**Work ID**: cleanup
**Status**: ACTIVE
**Created**: 2025-07-21
**Updated**: 2025-07-21

## 目标
根据workflow.md规范，清理cybercorp_node目录，移除冗余代码，建立清晰的项目结构。

## 任务分解

### T1: 分析现有结构 [100%]
- [x] 阅读workflow.md了解项目规范
- [x] 查看cybercorp_node目录结构
- [x] 识别需要清理的文件

### T2: 制定清理方案 [100%]
- [x] 识别核心功能模块
- [x] 确定保留/删除文件列表
- [x] 规划新的目录结构

### T3: 执行清理 [75%]
- [x] 备份重要文件（通过Git）
- [x] 删除冗余文件
- [x] 重组目录结构
- [ ] 更新文件引用

### T4: 优化核心代码 [0%]
- [ ] 简化remote_control.py
- [ ] 优化vision_integration.py
- [ ] 清理cursor控制器代码

## 问题分析

### 主要问题：
1. **文件混乱**：大量test_*.py散布在根目录
2. **版本后缀**：存在_optimized, _backup等违规命名
3. **冗余代码**：多个cursor控制器版本
4. **临时文件**：截图、日志等不应提交的文件
5. **目录结构**：不符合workflow.md的标准结构

### 核心功能识别：
1. **远程控制系统**：server.py, client.py, utils/remote_control.py
2. **视觉分析**：utils/vision_*.py
3. **Cursor自动化**：utils/cursor_*.py
4. **窗口管理**：utils/window_cache.py, win32_backend.py

## 清理方案

### 保留文件（核心功能）：
```
cybercorp_node/
├── src/                    # 源代码
│   ├── core/              # 核心功能
│   │   ├── server.py      # WebSocket服务器
│   │   ├── client.py      # 客户端
│   │   └── remote_control.py  # 远程控制
│   ├── vision/            # 视觉分析
│   │   ├── analyzer.py    # 主分析器
│   │   └── backends/      # 不同后端实现
│   └── automation/        # 自动化工具
│       ├── cursor.py      # Cursor IDE控制
│       └── windows.py     # 窗口管理
├── scripts/               # 脚本
│   ├── start_server.bat
│   └── start_client.bat
├── tests/                 # 测试
└── docs/                  # 文档
```

### 删除文件：
1. 所有test_*.py从根目录移到tests/
2. 删除所有截图文件（*.png）
3. 删除deprecated_scripts_*目录
4. 删除所有*_optimized, *_backup等违规命名文件
5. 删除临时json文件

### 代码优化重点：
1. 合并多个vision_model_*.py为一个模块化系统
2. 统一cursor控制器接口
3. 简化remote_control.py，移除冗余功能
4. 建立清晰的模块边界

## 执行步骤

1. 创建新的目录结构
2. 移动核心文件到正确位置
3. 更新所有import路径
4. 删除冗余文件
5. 测试确保功能正常
6. 提交更改

## 进度追踪
- 总进度: 68.75%
- 当前任务: T3 - 执行清理
- 下一步: 更新所有文件的import路径

## 已完成的清理工作

1. **创建标准目录结构**：
   - src/core/ - 核心功能
   - src/vision/ - 视觉分析
   - src/automation/ - 自动化工具
   - scripts/ - 脚本文件
   - tests/ - 测试文件

2. **文件迁移**：
   - 核心服务文件移到src/core/
   - 视觉相关文件移到src/vision/
   - 自动化文件移到src/automation/
   - 测试文件移到tests/
   - 脚本文件移到scripts/

3. **清理工作**：
   - 删除了所有临时文件（*.png, *.log, *.json）
   - 删除了违规命名文件（*_optimized, *_backup等）
   - 删除了冗余启动器文件
   - 删除了废弃目录