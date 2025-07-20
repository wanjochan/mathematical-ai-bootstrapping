# 工作计划 cybercorp_claudecode

本文档包含工作流 cybercorp_claudecode 的动态任务规划和分解。

## 工作流信息
- 工作ID: cybercorp_claudecode
- 创建时间: 2025-01-20
- 状态: ACTIVE (进行中)
- 描述: 构建AI专家系统与Claude命令集成，支持跨平台跨机器的专家协作
- 总体进度: 0%
- 特别注意：不要做历史纪录，只更新最后结果！

## 任务树

- T1 [0%] 第一阶段：cybercorp_node重构和Linux支持
  - T1.1 [0%] 创建平台抽象层
    - T1.1.1 [0%] 创建backends/base.py抽象基类
    - T1.1.2 [0%] 创建utils/platform_utils.py工厂类
    - T1.1.3 [0%] 重构requirements为分层结构
  - T1.2 [0%] 迁移Windows代码
    - T1.2.1 [0%] 拆分win32_backend到backends/windows/
    - T1.2.2 [0%] 提取client.py中Windows代码到client_windows.py
    - T1.2.3 [0%] 验证Windows功能正常
  - T1.3 [0%] 实现Linux后端
    - T1.3.1 [0%] 实现backends/linux/window_manager.py
    - T1.3.2 [0%] 实现backends/linux/input_controller.py
    - T1.3.3 [0%] 创建client_linux.py
  - T1.4 [0%] 统一客户端入口
    - T1.4.1 [0%] 重构client.py为平台感知入口
    - T1.4.2 [0%] 创建跨平台测试用例
    - T1.4.3 [0%] 更新文档和部署脚本

- T2 [0%] 第二阶段：本地AI专家系统集成
  - T2.1 [0%] 设计专家系统架构 [PARALLEL]
    - T2.1.1 [0%] 定义Agent与Claude命令映射接口
    - T2.1.2 [0%] 设计session管理机制
    - T2.1.3 [0%] 设计专家间通信协议
  - T2.2 [0%] 实现专家进程管理 [PARALLEL]
    - T2.2.1 [0%] 创建LocalExpertManager类
    - T2.2.2 [0%] 实现claude/gemini进程spawn和管理
    - T2.2.3 [0%] 实现进程间通信机制
  - T2.3 [0%] 集成到cybercorp_node
    - T2.3.1 [0%] 添加AI_EXPERT命令类型
    - T2.3.2 [0%] 实现专家执行插件
    - T2.3.3 [0%] 测试本地专家协作

- T3 [0%] 第三阶段：跨机器AI专家协作
  - T3.1 [0%] 扩展通信协议
    - T3.1.1 [0%] 设计专家任务分发协议
    - T3.1.2 [0%] 实现结果聚合机制
    - T3.1.3 [0%] 添加专家健康检查
  - T3.2 [0%] 统一专家接口
    - T3.2.1 [0%] 定义ExpertInterface基类
    - T3.2.2 [0%] 实现ClaudeExpert
    - T3.2.3 [0%] 实现GeminiExpert（可选）
  - T3.3 [0%] 系统集成测试
    - T3.3.1 [0%] 测试Linux/Windows混合部署
    - T3.3.2 [0%] 测试多专家并行执行
    - T3.3.3 [0%] 性能优化和压力测试

## 任务详情

### T1: 第一阶段：cybercorp_node重构和Linux支持
- 优先级: 高
- 依赖: 无
- 预计时间: 4-5天
- 描述: 重构cybercorp_node为跨平台架构，实现Linux客户端支持

### T1.1: 设计专家系统架构
- 优先级: 高
- 依赖: 无
- 描述: 设计清晰的架构，确保系统可扩展性
- 关键设计点:
  - Agent模型扩展：添加command、env、location等字段
  - Session与进程的映射关系
  - 专家生命周期管理

### T1.2: 实现本地进程管理器
- 优先级: 高
- 依赖: T1.1
- 描述: 核心组件，负责spawn和管理claude进程
- 技术要点:
  - 使用subprocess.Popen管理进程
  - 实现进程监控和重启机制
  - 处理stdin/stdout进行通信

### T2: 第二阶段：cybercorp_node Linux支持评估
- 优先级: 中
- 依赖: T1完成
- 预计时间: 3-4天（如果完整实现）
- 描述: 评估将cybercorp_node扩展到Linux的可行性和工作量

### T2.1: 创建平台抽象层
- 优先级: 高
- 依赖: 无
- 描述: 为跨平台支持打基础
- 设计模式: 抽象工厂模式
- 接口设计:
  ```python
  class PlatformBackend:
      def find_window()
      def send_keys()
      def take_screenshot()
  ```

### T2.2: Linux后端实现评估
- 优先级: 中
- 依赖: T2.1
- 描述: 评估Linux实现的技术方案
- 评估内容:
  - X11 vs Wayland兼容性
  - 不同Linux发行版差异
  - 依赖库的可用性

### T2.3: 最小化Linux支持方案
- 优先级: 高
- 依赖: T2.2
- 描述: 设计不依赖GUI的轻量级方案
- 方案要点:
  - 基于SSH执行远程命令
  - 使用Socket进行数据传输
  - 避免窗口管理复杂性

### T3: 第三阶段：跨机器AI专家协作
- 优先级: 高
- 依赖: T1, T2.3
- 预计时间: 2天
- 描述: 实现跨机器的AI专家调度和协作

## 并行任务管理

### 并行任务组定义
1. **T2.1 和 T2.2 [PARALLEL]**
   - 并行原因: 抽象层设计和Linux评估可同时进行
   - 同步点: T2.3需要两者结果
   - 预期时间节省: 40%

### 风险评估
1. **Linux GUI自动化复杂性**: 高风险
   - 缓解措施: 优先考虑无GUI方案
2. **跨平台兼容性**: 中风险
   - 缓解措施: 充分的抽象层设计
3. **网络通信稳定性**: 低风险
   - 缓解措施: 实现重连机制

## 动态规划笔记

- 考虑到cybercorp_node的Windows依赖性，建议先实现最小化的Linux支持
- 优先实现基于命令行的专家通信，避免GUI复杂性
- 可以考虑使用Docker容器来隔离不同专家环境
- 第一阶段的本地专家系统可以快速验证概念
- 建议创建一个独立的 ai_expert_proxy 服务，降低耦合度

## 工作量评估

### cybercorp_node Linux完整支持
- 创建抽象层: 2-3天
- 实现Linux后端: 5-7天
- 测试和调试: 3-4天
- **总计: 10-14天**

### 推荐的轻量级方案
- 本地专家管理: 2天
- 基于Socket的远程执行: 1天
- 集成测试: 1天
- **总计: 4天**

建议采用轻量级方案，避免GUI自动化的复杂性，专注于AI专家的协作通信。