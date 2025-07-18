# CyberCorp 前端界面 (cybercorp_web)

## 概述

CyberCorp 前端界面是虚拟公司三层架构中的前端组件，提供用户友好的Web界面，用于管理虚拟员工、任务和系统资源。该组件通过API与后端服务器通信，展示数据并允许用户进行操作。

## 主要功能

- **员工管理**：查看和控制虚拟员工状态，包括创建、配置和监控员工
- **任务管理**：创建、分配和监控任务，包括任务队列和执行状态
- **系统监控**：查看系统资源和性能指标，包括CPU、内存和网络使用情况
- **配置中心**：管理系统配置和参数，包括模型设置和系统选项

## 技术栈

- **框架**：React 或 Vue.js
- **UI组件**：Material-UI 或 Ant Design
- **状态管理**：Redux 或 Vuex
- **API客户端**：Axios 或 Fetch API
- **构建工具**：Webpack 或 Vite

## 目录结构

```
cybercorp_web/
├── public/              # 静态资源
├── src/                 # 源代码
│   ├── components/      # 组件
│   │   ├── common/      # 通用组件
│   │   ├── employee/    # 员工相关组件
│   │   ├── task/        # 任务相关组件
│   │   └── system/      # 系统相关组件
│   ├── pages/           # 页面
│   ├── services/        # API服务
│   ├── store/           # 状态管理
│   ├── utils/           # 工具函数
│   ├── App.js           # 应用入口
│   └── index.js         # 主入口
├── tests/               # 测试
├── package.json         # 依赖管理
└── README.md           # 说明文档
```

## 安装与运行

### 安装依赖

```bash
npm install
```

### 开发模式运行

```bash
npm run dev
```

### 构建生产版本

```bash
npm run build
```

## 与其他组件的关系

- **cybercorp_server**：通过API与后端服务器通信，获取数据并发送操作请求
- **cybercorp_oper**：不直接通信，通过后端服务器间接交互

## 开发指南

### 开发环境设置

1. 克隆仓库
2. 安装依赖：`npm install`
3. 启动开发服务器：`npm run dev`

### 代码规范

- 遵循ESLint配置
- 使用TypeScript进行类型检查
- 编写单元测试
- 文档使用Markdown格式

### 贡献流程

1. 创建功能分支
2. 提交代码
3. 运行测试
4. 提交Pull Request

## 许可证

[MIT License](LICENSE)