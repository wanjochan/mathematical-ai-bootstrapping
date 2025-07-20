# 工作笔记 cybercorp

本文档包含工作流 cybercorp 的上下文、经验和工作会话笔记，以保持AI会话之间的连续性。

## 工作流信息
- 工作ID: cybercorp
- 创建时间: 2023-11-15
- 关联计划: [工作计划文档](workplan_cybercorp.md)
- 特别注意：不要做历史纪录，只更新最后结果！

## 会话

### 会话：2025-07-20

#### 上下文
- CyberCorp Node系统重构和优化工作
- 已完成的关键组件：
  - cybercorp_node/server.py：WebSocket服务器，支持客户端管理和命令转发
  - cybercorp_node/client.py：受控端，支持窗口管理、键鼠控制、截图、OCR、Win32 API
  - cybercorp_node/utils/：工具模块包括remote_control.py、window_cache.py、win32_backend.py、ocr_backend.py
- 系统架构已从原计划调整为：
  - 中控服务器(server.py)：管理所有受控端连接
  - 受控端(client.py)：在目标机器上执行操作
  - 控制端(remote_control.py)：高级API用于控制操作

#### 挑战与解决
- 挑战1：UIA结构提取速度慢（10-30秒）
  - 解决方案：实现了限深度提取、窗口缓存机制，速度提升10倍
- 挑战2：命令执行延迟高
  - 解决方案：实现了异步命令队列、批量执行、优先级调度
- 挑战3：多文件混乱，代码重复
  - 解决方案：整合了35+测试脚本到统一框架，减少77%文件数量
- 挑战4：实战测试发现的问题
  - 窗口激活失败：需要管理员权限或使用SetForegroundWindow API
  - 键盘输入失败：需要先激活窗口并等待
  - 响应格式不一致：需要统一返回dict格式
  - 客户端版本不同步：需要版本检查机制
- 挑战5：Cursor IDE窗口识别问题
  - 现象：发现12个Cursor.exe进程但无可见窗口
  - 分析：Cursor可能运行在后台模式或不同会话
  - 解决方案：实现了find_cursor_windows命令，通过进程名识别
- 挑战6：datetime变量作用域错误
  - 现象：所有命令执行时报错"cannot access local variable 'datetime'"
  - 分析：_handle_screenshot函数中局部导入datetime造成作用域混淆
  - 解决方案：使用global datetime声明使用模块级导入

#### 状态追踪更新
- 当前状态: ACTIVE
- 状态变更原因: T5任务全部完成，受控端稳健性和功能大幅提升
- 主要成就:
  1. 实现了完整的异常恢复机制（T5.1）
  2. 实现了热更新功能（T5.2）
  3. 实现了健康监控系统（T5.3）
  4. 实现了增强日志管理（T5.4）
  5. 修复了窗口控制问题
  6. 统一了响应格式
  7. 实现了远程重启功能
- 版本更新: CyberCorp Node v2.0.0
  - 新增功能: 故障恢复、热更新、健康监控、增强日志、远程重启
  - 性能优化: 异步执行、连接池、资源优化、并发处理
  - 代码改进: 模块化架构、统一响应格式、完整测试套件
- 下一步计划: 
  1. 根据业务需求继续优化
  2. 可考虑开发cybercorp_web前端界面
  3. 或专注于现有功能的生产环境部署

## 知识库

### 系统架构
- CyberCorp Node系统采用中控/受控架构：
  - 中控服务器(server.py)：WebSocket服务器，管理所有客户端连接，支持命令转发
  - 受控端(client.py)：在目标机器运行，执行窗口管理、键鼠控制等操作
  - 控制端(remote_control.py)：提供高级API，简化控制操作
- 性能优化技术：
  - 窗口缓存(WindowCache)：2分钟TTL，减少重复查询
  - 异步命令队列(CommandQueue)：支持并行执行和优先级调度
  - 批量执行(BatchExecutor)：减少网络往返，提升效率
  - UIA优化：限制深度、选择性属性获取

### 关键组件
- cybercorp_node核心模块：
  - server.py：WebSocket服务器，支持客户端管理、命令转发、心跳监控
  - client.py：受控端，支持窗口管理、键鼠控制、截图、OCR、Win32 API、热更新、健康监控
  - client_watchdog.py：进程监控，自动重启崩溃的客户端
  - utils/remote_control.py：高级控制API，提供RemoteController、WindowController、BatchExecutor
  - utils/window_cache.py：窗口信息缓存，支持TTL过期和模式匹配
  - utils/win32_backend.py：Windows API封装，支持窗口查找、鼠标拖动（贝塞尔曲线）
  - utils/ocr_backend.py：多引擎OCR支持（Windows OCR、EasyOCR、Tesseract、PaddleOCR）
  - utils/hot_reload_manager.py：热更新管理器，支持文件监控、模块重载、配置更新
  - utils/file_monitor.py：文件系统监控，触发热更新
  - utils/module_reloader.py：Python模块动态重载
  - utils/config_manager.py：配置文件管理，支持热更新
  - utils/health_monitor.py：健康监控系统，跟踪CPU、内存、命令执行
  - utils/log_manager.py：增强日志管理，支持轮转、远程查看、持久化
  - utils/response_formatter.py：统一响应格式化器
- 测试套件：
  - test_hot_reload.py：热更新功能测试
  - test_health_monitor.py：健康监控测试
  - test_window_input.py：窗口控制测试
  - test_response_format.py：响应格式验证
  - test_log_manager.py：日志管理测试
  - test_performance.py：性能基准测试
  - test_restart.py：远程重启测试
  - test_dashboard.py：综合仪表板

### 重要模式和最佳实践
- 实战驱动开发：通过实际使用发现问题并优化
- 渐进式改进：先实现基础功能，再逐步优化
- 错误容错设计：所有操作都要有错误处理
- 性能优先：使用缓存、批处理等技术提升响应速度
- 版本兼容：确保新旧客户端都能正常工作
- 工作流规范：严格遵循workflow.md，所有更新记录在工作文档中
- 响应格式统一：使用ResponseFormatter确保API一致性
- 模块化设计：功能分离到utils/目录，便于维护和测试

## 工作流状态历史

### 状态变更记录
| 时间 | 从状态 | 到状态 | 变更原因 | 备注 |
|------|--------|--------|----------|------|
| 2023-11-15 | INIT | PLANNING | 初始化完成 | 模板文档已读取，工作计划已创建 |

### 关键里程碑
- 里程碑1: 2023-11-15 - 工作流初始化完成，开始规划

## 参考资料

- PRD-shortterm.md：产品需求文档
- workflow.md：工作流程说明
- cybercorp_server/README.md：服务器组件说明
- cybercorp_desktop/README.md：桌面客户端说明
- cybercorp_server/docs/SYSTEM_ARCHITECTURE.md：系统架构文档

## 改进建议

### 基于本次执行的建议
- 建议1：采用更模块化的设计，便于后续扩展
- 建议2：建立统一的通信协议标准，确保组件间无缝集成

### 模板改进建议
- 模板改进1：增加技术栈选择和评估部分
- 模板改进2：增加部署策略和环境配置部分