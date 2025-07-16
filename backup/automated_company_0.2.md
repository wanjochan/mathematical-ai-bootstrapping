# 在 Agentic 时代：基于 UI-TARS 构建全自动化公司

## 摘要

本文探讨了如何利用 ByteDance 开发的 UI-TARS-1.5（用户界面任务自动化与推理系统）构建一个全自动化的公司或团队。UI-TARS-1.5 是一种原生 GUI 代理模型，能够通过截图输入执行类似人类的键盘和鼠标操作，在 OSWorld 基准测试（一个评估代理在操作系统环境中的任务完成能力的基准）中达到 42.5% 成功率，在 AndroidWorld（一个评估代理在 Android 环境中的任务完成能力的基准）中达到 64.2% 的成功率。

我们提出了一种系统架构，在 Windows 服务器上通过不同用户账户运行 UI-TARS 实例，模拟经理和开发者的角色，并通过 FastAPI 构建的 Web 界面（TeamApp）实现人机交互，支持实时状态监控和 WebSocket 更新。TeamApp 作为消息转发器，简化任务分配与结果反馈流程。本文基于第一性原则设计系统，保持最小化功能，同时为未来扩展（如 BPMN 工作流管理）提供可能性。这一方法展示了 agentic AI 在组织自动化中的潜力。

## 1. 引言

随着人工智能的快速发展，agentic AI 模型为自动化带来了新的可能性。UI-TARS-1.5 是 UI-TARS 系列的最新版本，集成游戏和 GUI 任务改进，具备增强视觉感知、统一动作建模、系统 2 推理、迭代训练、推理时扩展和强化学习等核心能力（秦宇佳等，2025）。这些能力使 UI-TARS-1.5 能够处理复杂的桌面任务，如文件管理、浏览器操作和游戏任务，为构建全自动化公司提供了技术基础。

本文提出了一种基于 UI-TARS-1.5 的全自动化公司架构，其中 AI 代理扮演虚拟员工角色，执行人类经理分配的任务，广泛应用于任务管理、代码开发和跨平台操作。我们通过在 Windows 服务器上运行多个 UI-TARS 实例，并利用 FastAPI 构建的 Web 界面，实现了高效的任务管理和自动化工作流。

## 2. 系统架构

系统由以下三个主要组件构成，遵循 BPMN 的泳道模型（人类、TeamApp、员工），新增实时监控泳道。BPMN 泳道模型通过将系统划分为不同的责任区域，确保任务流程的清晰和高效：

### 2.1 虚拟员工（UI-TARS 代理）

每个虚拟员工由一个 UI-TARS-1.5 实例表示，使用 UI-TARS-1.5-7B 模型，运行在 Windows 服务器上的独立用户账户下。本例中，我们设置了三个用户账户：

- `oper_mgr`：模拟经理角色，运行在端口 10000。
- `oper_dev1`：模拟开发者 1，运行在端口 10001。
- `oper_dev2`：模拟开发者 2，运行在端口 10002。

每个 UI-TARS 实例通过其 API 端点接收任务指令，执行 GUI 操作，并返回结果。其核心能力包括增强视觉感知、统一动作建模、系统 2 推理、迭代训练和游戏性能优化（如 Minecraft 和 Poki 游戏成功率高达 100%）。

### 2.2 TeamApp（Web 界面）

TeamApp 是一个基于 FastAPI 的 Web 应用程序，充当人类经理与 UI-TARS 代理之间的消息转发器，支持 WebSocket 实时更新和状态轮询。经理通过 Web 界面选择目标员工并输入任务（如"打开记事本并写入'Hello, World!'"），TeamApp 将任务转发至相应 UI-TARS 实例并返回结果。基于第一性原则，TeamApp 仅实现最小功能，避免复杂的管理组件。

### 2.3 工作流管理（可选）

对于需要多步骤或多代理协作的复杂任务，可引入 BPMN 引擎（如 Flowable 或 Camunda）管理任务序列。例如，一个工作流可能包括 `oper_dev1` 编写代码、`oper_dev2` 审查代码、以及 `oper_mgr` 批准代码。为保持简单性，初始实现仅包括任务转发功能，推荐集成 Flowable 以支持示例 BPMN 图。

## 3. 系统设置与配置

### 3.1 Windows 服务器设置

在 Windows 服务器上创建三个用户账户：`oper_mgr`、`oper_dev1` 和 `oper_dev2`。使用 `runas` 命令为每个账户启动 UI-TARS 服务，分配不同端口：

```bash
runas /user:oper_mgr "agent-tars serve --port 10000 --model.provider volcengine"
runas /user:oper_dev1 "agent-tars serve --port 10001 --model.provider volcengine"
runas /user:oper_dev2 "agent-tars serve --port 10002 --model.provider volcengine"
```

这些命令启动无头 UI-TARS 服务器，监听指定端口。每个实例通过其 API 端点（如 `/v1/chat/completions`）接收任务指令。为支持 Midscene.js 浏览器自动化，需安装 Node.js 依赖，步骤如下：

1. 下载 Node.js 安装包。
2. 运行安装包并按照提示完成安装。
3. 安装 Midscene.js 依赖：`npm install midscene`。

### 3.2 Linux 服务器耦合（可选）

对于需要 Linux 环境的特定任务，可在单独的 Linux 服务器上运行数据处理或程序执行任务，并通过 API 或共享存储与 Windows 服务器耦合。示例 API 耦合代码包括远程操作功能，从 UI-TARS-desktop v0.2.0 更新。

## 4. TeamApp 设计与实现

TeamApp 使用 FastAPI 构建，提供一个简单的 Web 界面，允许经理选择员工并输入任务。以下是核心实现代码，包括 WebSocket 和状态管理：

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import requests
import asyncio

app = FastAPI()

employees = {
    "oper_mgr": {"port": 10000, "status": "idle"},
    "oper_dev1": {"port": 10001, "status": "idle"},
    "oper_dev2": {"port": 10002, "status": "idle"}
}

connections = []

@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
        <body>
            <h1>Team App</h1>
            <select id="employee">
                <option value="oper_mgr">Manager</option>
                <option value="oper_dev1">Dev1</option>
                <option value="oper_dev2">Dev2</option>
            </select>
            <input id="task" placeholder="Enter task">
            <button onclick="sendTask()">Send</button>
            <div id="result"></div>
            <div id="status"></div>
            <script>
                const ws = new WebSocket("ws://localhost:8000/ws");
                ws.onmessage = (event) => { 
                    document.getElementById("status").innerText = event.data; 
                };
                function sendTask() {
                    fetch('/send_task', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            task: document.getElementById("task").value, 
                            employee: document.getElementById("employee").value
                        })
                    }).then(res => res.json()).then(data => { 
                        document.getElementById("result").innerText = JSON.stringify(data); 
                    });
                }
            </script>
        </body>
    </html>
    """)

@app.post("/send_task")
async def send_task(task: str, employee: str):
    if employee not in employees:
        return {"error": "Invalid employee"}
    
    employees[employee]["status"] = "busy"
    broadcast_status()
    
    url = f"http://localhost:{employees[employee]['port']}/v1/chat/completions"
    response = requests.post(url, json={"messages": [{"role": "user", "content": task}]})
    
    employees[employee]["status"] = "idle"
    broadcast_status()
    
    return response.json()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        connections.remove(websocket)

def broadcast_status():
    status = {emp: data["status"] for emp, data in employees.items()}
    for conn in connections:
        conn.send_text(str(status))

async def monitor_status():
    while True:
        await asyncio.sleep(5)
        broadcast_status()

@app.on_event("startup")
async def startup():
    asyncio.create_task(monitor_status())
```

### 4.1 功能特性

- **任务分配**：经理通过 Web 界面输入任务并选择目标员工，TeamApp 将任务转发至对应 UI-TARS 实例。
- **结果反馈**：UI-TARS 代理执行任务后返回结果，TeamApp 将其显示在 Web 界面上。
- **状态观察**：通过 WebSocket 查看所有员工工作状态（idle/busy）。
- **可扩展性**：通过添加新的用户账户和 UI-TARS 实例，可轻松扩展系统，支持动态员工添加和 SDK 集成。

### 4.2 BPMN 工作流设计

初始实现保持简单，但可通过 BPMN 引擎实现复杂工作流。例如，一个代码开发工作流包括：

1. `oper_dev1` 编写代码。
2. `oper_dev2` 审查代码。
3. `oper_mgr` 批准代码。

BPMN 模型定义为三个泳道（人类、TeamApp、员工），每个泳道包含特定任务节点。TeamApp 按顺序发送任务指令至相应 UI-TARS 实例，确保工作流无缝执行。示例 BPMN XML 可从 Flowable 文档获取。

## 5. 技术栈与工具

以下是系统实现的核心技术栈：

| 组件         | 技术/工具       | 用途                                                                 |
|--------------|-----------------|----------------------------------------------------------------------|
| 虚拟员工     | UI-TARS-1.5     | 处理桌面任务（如文件管理、浏览器操作）和游戏任务（如 Minecraft）     |
| Web 界面     | FastAPI         | 构建 TeamApp，提供任务分配、结果反馈和 WebSocket 实时更新             |
| 工作流管理   | BPMN 引擎       | 管理复杂任务序列（如 Flowable 或 Camunda，可选集成）                |
| 服务器       | Windows Server  | 运行 UI-TARS 实例，支持 GUI 操作                                     |
| 辅助服务器   | Linux Server    | 处理特定 Linux 环境任务，通过 API 与 Windows 服务器耦合（可选）      |
| 附加工具     | Agent TARS CLI  | 部署和推理 UI-TARS                                                   |
| 附加工具     | UI-TARS SDK     | 集成和坐标处理                                                       |

## 6. 讨论

### 6.1 优势

- **高效自动化**：UI-TARS-1.5 的 GUI 交互能力使系统能处理复杂桌面任务，减少人工干预，在 OSWorld 中优于 OpenAI CUA (36.4%) 和 Claude 3.7 (28%)。
- **可扩展性**：通过添加 UI-TARS 实例和用户账户，系统可轻松扩展。
- **简单性**：TeamApp 的消息转发设计遵循第一性原则，保持系统轻量且易维护。

### 6.2 挑战

- **安全性**：UI-TARS 的强大 GUI 操作能力可能被滥用（如绕过 CAPTCHA），需严格安全评估和沙箱环境（秦宇佳等，2025）。应对措施包括实施访问控制、使用沙箱隔离和定期安全审计。
- **可靠性**：UI-TARS 在不熟悉的 GUI 环境中可能出错，需通过多样化训练数据和自适应学习持续优化。
- **计算资源**：运行多个 UI-TARS 实例需大量资源，可通过分布式计算和模型优化解决。

## 7. 结论

通过利用 UI-TARS-1.5 的 GUI 交互能力，我们展示了一种构建全自动化公司或团队的可行方法。系统在 Windows 服务器上运行多个 UI-TARS 实例，并通过 FastAPI 构建的 TeamApp 实现任务管理，达成高效自动化工作流。当前设计简单，但可通过整合 BPMN 引擎支持复杂任务场景。

未来工作将聚焦安全性、可靠性和跨平台集成，具体包括开发安全框架、实施可靠性测试和探索跨平台运行，以充分发挥 agentic AI 的潜力。

## 参考文献

- [1] 秦宇佳等，"UI-TARS: Pioneering Automated GUI Interaction with Native Agents," arXiv preprint arXiv:2501.12326, 2025. [https://arxiv.org/abs/2501.12326](https://arxiv.org/abs/2501.12326)
- [2] ByteDance, "UI-TARS Desktop," GitHub, 2025. [https://github.com/bytedance/UI-TARS-desktop](https://github.com/bytedance/UI-TARS-desktop)
- [3] Agent TARS, "CLI Documentation," 2025. [https://agent-tars.com/guide/basic/cli.html](https://agent-tars.com/guide/basic/cli.html)
- [4] ByteDance, "UI-TARS," GitHub, 2025. [https://github.com/bytedance/UI-TARS](https://github.com/bytedance/UI-TARS)
- [5] ByteDance, "ByteDance Seed Agent Model UI-TARS-1.5 Open Source," Blog, 2025. [https://seed.bytedance.com/en/blog/bytedance-seed-agent-model-ui-tars-1-5-open-source-achieving-sota-performance-in-various-benchmarks](https://seed.bytedance.com/en/blog/bytedance-seed-agent-model-ui-tars-1-5-open-source-achieving-sota-performance-in-various-benchmarks)
- [6] ByteDance, "UI-TARS GitHub Repository," 2025. [https://github.com/bytedance/UI-TARS](https://github.com/bytedance/UI-TARS)

