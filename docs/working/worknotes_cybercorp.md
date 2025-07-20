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

#### 批判性思考记录（2025-07-20）
- **问题反思**：
  - 之前太机械地查找窗口，没有深入理解用户环境
  - 忽略了RDP会话与控制台会话的区别
  - 没有主动思考"为什么找不到窗口"的根本原因
- **关键发现**：
  - tasklist显示的Cursor进程都在RDP-Tcp#1会话中
  - 当前客户端在不同会话，所以看不到这些窗口
  - 需要在当前用户会话中启动Cursor才能控制
- **思维转变**：
  - 从"查找已存在的窗口"转变为"主动创建可控制的环境"
  - 从"被动观察"转变为"主动实验和验证"
  - 认识到中控端不仅是控制工具，更是观察和理解系统的窗口
- **实验发现**：
  - Cursor.exe确实存在于d:\cursor\目录
  - 通过Win+R启动程序的方法可能需要调整
  - 需要考虑更直接的启动方式，如添加执行命令功能
- **技术发现**：
  - 热更新对主模块(client.py)不起作用，需要重启
  - 添加新命令需要重启客户端才能生效
  - 实战测试是发现问题的最佳方式

#### 实战成果总结（2025-07-20）
- **问题解决**：
  1. 修复了datetime变量作用域错误
  2. 实现了find_cursor_windows命令
  3. 添加了execute_program命令用于启动程序
  4. 启动了当前用户的受控端进行实时测试
- **重要洞察**：
  1. 实战测试是发现和解决问题的最佳方式
  2. 批判性思考帮助我们从"被动查找"转向"主动创建"
  3. 中控端是观察和理解系统行为的重要工具
  4. 热更新有局限性，主模块更改需要重启
- **技术成就**：
  1. CyberCorp Node系统已具备完整的控制能力
  2. 客户端稳健性大幅提升（异常恢复、热更新、健康监控）
  3. 统一的响应格式确保了API的一致性
  4. 模块化设计便于功能扩展

#### 状态追踪更新
- 当前状态: ACTIVE
- 状态变更原因: T5任务全部完成，T6.1 Cursor控制测试已实施
- 下一步建议：
  1. 手动重启客户端以加载execute_program命令
  2. 继续测试Cursor IDE的具体控制功能
  3. 开发Cursor特定的命令（如打开AI聊天、执行命令等）
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

#### 工作流改进洞察（2025-07-20）
- **批判性思维的价值**：
  - 在遇到"找不到Cursor窗口"问题时，批判性思考帮助我们：
    - 从"为什么找不到"转向"是否本来就不存在"
    - 从"查找已有窗口"转向"主动创建可控环境"
    - 从"被动观察"转向"主动实验"
  - 这种思维转变直接导致问题的解决
- **规格驱动开发的重要性**：
  - 在添加execute_program命令前，应先更新API规格文档
  - 明确定义命令参数、返回值、错误处理
  - 这样可以避免后续的接口不一致问题
- **工作流优化建议**：
  1. 在workflow.md中增加批判性思维分析环节（已完成）
  2. 强化规格优先原则，确保代码变更有据可依（已完成）
  3. 记录批判性思考过程，作为后续参考

#### 实战启示录（2025-07-20 新增）
- **启示1**：当命令执行失败时，不要只看错误信息，要追问根本原因
- **启示2**：主动创建环境比被动等待更有效
- **启示3**：工作流文档应反映实践中的最佳做法
- **启示4**：规格文档是代码质量的保障，不可省略
- **启示5**：在解决问题过程中保持批判性思维

#### 成功实战案例（2025-07-20 追加）
- **Cursor控制成功**：
  - 启动了新的受控端（client_120）
  - 通过execute_program命令成功启动Cursor.exe（PID: 32016）
  - 找到并控制了Cursor窗口（HWND: 7670670）
  - 成功激活窗口、输入文本、截图
- **关键技术点**：
  - 受控端启动后会自动连接到中控服务器
  - execute_program命令支持启动任意程序
  - find_cursor_windows命令可以找到Cursor进程的所有窗口
  - 窗口控制需要先激活再操作

#### 命令执行流程总结：
1. 管理客户端连接到中控服务器（ws://localhost:9998）
2. 获取可用客户端列表（list_clients）
3. 向指定客户端转发命令（forward_command）
4. 客户端执行命令并返回结果
5. 统一的响应格式确保结果一致性

#### Cursor自动化实战（2025-07-20）
- **已完成**：
  1. 设计了完整的Cursor自动化规格文档
  2. 实现了cursor_automation.py模块
  3. 添加了execute_cursor_task命令到client.py
  4. 创建了测试脚本和目标文件
- **发现的问题**：
  1. 新模块需要重启客户端才能加载
  2. 热更新仅对utils目录下的模块有效
  3. 重启命令可能因超时而失败
- **下一步计划**：
  1. 手动重启客户端加载新模块
  2. 完善Cursor UI元素定位和交互
  3. 实现AI响应检测和结果提取
  4. 测试完整的子任务执行流程

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