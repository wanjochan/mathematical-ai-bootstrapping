

# 在 Agentic 时代：基于 UI-TARS 构建全自动化公司

## 摘要
本文探讨了如何利用 ByteDance 开发的 UI-TARS（用户界面任务自动化与推理系统）构建一个全自动化的公司或团队。UI-TARS 是一种原生 GUI 代理模型，能够通过截图输入执行类似人类的键盘和鼠标操作。我们提出了一种系统架构，在 Windows 服务器上通过不同用户账户运行 UI-TARS 实例，模拟经理和开发者的角色，并通过 FastAPI 构建的 Web 界面（TeamApp）实现人机交互。TeamApp 作为消息转发器，简化任务分配与结果反馈流程。本文基于第一性原则设计系统，保持最小化功能，同时为未来扩展（如 BPMN 工作流管理）提供可能性。这一方法展示了 agentic AI 在组织自动化中的潜力。

## 1. 引言
随着人工智能的快速发展，agentic AI 模型为自动化带来了新的可能性。UI-TARS 是一种先进的 GUI 代理模型，能够以人类的方式与图形用户界面（GUI）交互，执行如浏览器导航、文件管理和办公软件操作等任务（秦宇佳等，2025）。本文提出了一种基于 UI-TARS 的全自动化公司架构，其中 AI 代理扮演虚拟员工角色，执行由人类经理分配的任务。我们通过在 Windows 服务器上运行多个 UI-TARS 实例，并使用 FastAPI 构建的 Web 界面，实现了高效的任务管理和自动化工作流。

## 2. 系统架构
系统由以下三个主要组件构成，遵循 BPMN 的泳道模型（人类、TeamApp、员工）：

### 2.1 虚拟员工（UI-TARS 代理）
每个虚拟员工由一个 UI-TARS 实例表示，运行在 Windows 服务器上的独立用户账户下。本例中，我们设置了三个用户账户：
- `oper_mgr`：模拟经理角色，运行在端口 10000。
- `oper_dev1`：模拟开发者 1，运行在端口 10001。
- `oper_dev2`：模拟开发者 2，运行在端口 10002。

每个 UI-TARS 实例通过其 API 端点接收任务指令，执行 GUI 操作，并返回结果。UI-TARS 的核心能力包括增强感知、统一动作建模、系统 2 推理和迭代训练（秦宇佳等，2025），使其能够处理复杂的桌面任务。

### 2.2 TeamApp（Web 界面）
TeamApp 是一个基于 FastAPI 的 Web 应用程序，充当人类经理与 UI-TARS 代理之间的消息转发器。经理通过 Web 界面选择目标员工并输入任务（如“打开记事本并写入‘Hello, World!’”），TeamApp 将任务转发到相应的 UI-TARS 实例并返回结果。基于第一性原则，TeamApp 仅实现最小功能，避免复杂的管理组件。

### 2.3 工作流管理（可选）
对于需要多步骤或多代理协作的复杂任务，可引入 BPMN 引擎（如 Flowable 或 Camunda）来管理任务序列。例如，一个工作流可能包括 `oper_dev1` 编写代码、`oper_dev2` 审查代码、以及 `oper_mgr` 批准代码。为保持简单性，初始实现仅包括任务转发功能。

## 3. 系统设置与配置
### 3.1 Windows 服务器设置
在 Windows 服务器上创建三个用户账户：`oper_mgr`、`oper_dev1` 和 `oper_dev2`。使用 `runas` 命令为每个账户启动 UI-TARS 服务，分配不同端口：

```bash
runas /user:oper_mgr "agent-tars serve --port 10000"
runas /user:oper_dev1 "agent-tars serve --port 10001"
runas /user:oper_dev2 "agent-tars serve --port 10002"
```

这些命令启动无头 UI-TARS 服务器，监听指定的端口。每个实例通过其 API 端点（如 `/v1/chat/completions`）接收任务指令。

### 3.2 Linux 服务器耦合（可选）
对于需要 Linux 环境的特定任务，可在单独的 Linux 服务器上运行数据处理或程序执行任务，并通过 API 或共享存储与 Windows 服务器耦合。这种设计确保了系统的灵活性和跨平台兼容性。

## 4. TeamApp 设计与实现
TeamApp 使用 FastAPI 构建，提供一个简单的 Web 界面，允许经理选择员工并输入任务。以下是 TeamApp 的核心实现代码：

```python
from fastapi import FastAPI
import requests

app = FastAPI()

@app.post("/send_task")
def send_task(task: str, employee: str):
    # 映射员工到对应的 UI-TARS 端口
    base_url = "http://localhost"
    ports = {
        "oper_mgr": 10000,
        "oper_dev1": 10001,
        "oper_dev2": 10002
    }
    
    if employee not in ports:
        return {"error": "无效的员工"}
    
    url = f"{base_url}:{ports[employee]}/v1/chat/completions"
    
    # 发送任务到 UI-TARS 代理
    response = requests.post(url, json={"messages": [{"role": "user", "content": task}]})
    return response.json()
```

### 4.1 功能特性
- **任务分配**：经理通过 Web 界面输入任务并选择目标员工，TeamApp 将任务转发到对应的 UI-TARS 实例。
- **结果反馈**：UI-TARS 代理执行任务后返回结果，TeamApp 将其显示在 Web 界面上。
- **可扩展性**：通过添加新的用户账户和 UI-TARS 实例，可轻松扩展系统以支持更多虚拟员工。

### 4.2 BPMN 工作流设计
虽然初始实现保持简单，但可以通过 BPMN 引擎实现复杂工作流。例如，一个代码开发工作流可能包括以下步骤：
1. `oper_dev1` 编写代码。
2. `oper_dev2` 审查代码。
3. `oper_mgr` 批准代码。

BPMN 模型可以定义为三个泳道（人类、TeamApp、员工），每个泳道包含特定的任务节点。TeamApp 将任务指令按顺序发送到相应的 UI-TARS 实例，确保工作流的无缝执行。

## 5. 技术栈与工具
以下是系统实现中使用的核心技术栈：

| 组件         | 技术/工具       | 描述                                                                 |
|--------------|-----------------|----------------------------------------------------------------------|
| 虚拟员工     | UI-TARS         | 原生 GUI 代理模型，处理桌面任务（如文件管理、浏览器操作）             |
| Web 界面     | FastAPI         | 轻量级 Web 框架，用于构建 TeamApp，提供任务分配和结果反馈             |
| 工作流管理   | BPMN 引擎       | 可选组件，用于管理复杂任务序列（如 Flowable 或 Camunda）              |
| 服务器       | Windows Server  | 运行 UI-TARS 实例的操作系统，支持 GUI 操作                           |
| 辅助服务器    | Linux Server    | 可选，用于处理特定 Linux 环境任务，与 Windows 服务器通过 API 耦合     |

## 6. 讨论
### 6.1 优势
- **高效自动化**：UI-TARS 的 GUI 交互能力使系统能够处理复杂的桌面任务，减少人工干预。
- **可扩展性**：通过添加新的 UI-TARS 实例和用户账户，系统可轻松扩展。
- **简单性**：TeamApp 的消息转发设计遵循第一性原则，保持系统轻量且易于维护。

### 6.2 挑战
- **安全性**：UI-TARS 的强大 GUI 操作能力可能被滥用（如绕过 CAPTCHA），需要严格的安全评估（秦宇佳等，2025）。
- **可靠性**：UI-TARS 可能在不熟悉的 GUI 环境中产生错误推断或次优操作，需要持续优化。
- **计算资源**：运行多个 UI-TARS 实例需要大量计算资源，尤其是在大规模任务中。

## 7. 结论
通过利用 UI-TARS 的 GUI 交互能力，我们展示了一种构建全自动化公司或团队的可行方法。系统通过在 Windows 服务器上运行多个 UI-TARS 实例，并使用 FastAPI 构建的 TeamApp 进行任务管理，实现了高效的自动化工作流。虽然当前设计简单，但通过整合 BPMN 引擎可进一步支持复杂任务场景。未来的工作应关注安全性、可靠性和跨平台集成，以充分发挥 agentic AI 的潜力。

## 参考文献
- [1] 秦宇佳等，"UI-TARS: Pioneering Automated GUI Interaction with Native Agents," arXiv preprint arXiv:2501.12326, 2025. [https://arxiv.org/abs/2501.12326](https://arxiv.org/abs/2501.12326)
- [2] ByteDance, "UI-TARS Desktop," GitHub, 2025. [https://github.com/bytedance/UI-TARS-desktop](https://github.com/bytedance/UI-TARS-desktop)
- [3] Agent TARS, "CLI Documentation," 2025. [https://agent-tars.com/guide/basic/cli.html](https://agent-tars.com/guide/basic/cli.html)

