# CyberCorp 前端界面架构设计

## 1. 概述

CyberCorp 前端界面是虚拟公司三层架构中的用户交互组件，提供员工管理、任务管理、系统监控和配置中心等功能的可视化界面。该组件通过与后端服务器通信，为用户提供直观、友好的操作体验。

## 2. 架构设计

### 2.1 整体架构

```
+-------------------+        +-------------------+
|                   |        |                   |
|  cybercorp_web    |<------>|  cybercorp_server |
|  (前端界面)        |   API   |  (后端服务)       |
|                   |        |                   |
+-------------------+        +---------^---------+
                                       |
                                       | API/WebSocket
                                       |
                              +--------v----------+
                              |                   |
                              |  cybercorp_oper   |
                              |  (操作控制端)      |
                              |                   |
                              +-------------------+
```

### 2.2 分层架构

```
+-------------------------------------------------------+
|                     视图层                            |
|  (页面组件, 布局组件, UI组件)                           |
+-------------------------------------------------------+
|                     状态管理层                         |
|  (状态存储, 状态更新, 状态订阅)                          |
+-------------------------------------------------------+
|                     服务层                            |
|  (API服务, WebSocket服务, 工具服务)                     |
+-------------------------------------------------------+
|                     路由层                            |
|  (路由配置, 路由守卫, 路由跳转)                          |
+-------------------------------------------------------+
```

## 3. 组件设计

### 3.1 视图层

#### 3.1.1 页面组件

- **登录页面**：用户登录界面
- **仪表盘页面**：系统概览界面
- **员工管理页面**：管理虚拟员工
- **任务管理页面**：管理任务
- **系统监控页面**：监控系统状态
- **配置中心页面**：管理系统配置

#### 3.1.2 布局组件

- **主布局**：包含侧边栏、顶部导航和内容区域
- **侧边栏**：显示导航菜单
- **顶部导航**：显示用户信息和全局操作
- **内容区域**：显示页面内容

#### 3.1.3 UI组件

- **表单组件**：输入框、下拉框、单选框、复选框等
- **表格组件**：数据表格
- **图表组件**：折线图、柱状图、饼图等
- **对话框组件**：确认对话框、提示对话框等
- **通知组件**：成功通知、错误通知、警告通知等

### 3.2 状态管理层

#### 3.2.1 状态存储

- **全局状态**：用户信息、系统配置等
- **页面状态**：页面特定的状态
- **组件状态**：组件特定的状态

#### 3.2.2 状态更新

- **同步更新**：直接更新状态
- **异步更新**：通过API请求更新状态
- **事件更新**：通过WebSocket事件更新状态

#### 3.2.3 状态订阅

- **组件订阅**：组件订阅状态变更
- **页面订阅**：页面订阅状态变更
- **全局订阅**：全局订阅状态变更

### 3.3 服务层

#### 3.3.1 API服务

- **员工服务**：员工相关的API服务
  - `getEmployees(): Promise<Employee[]>`：获取所有员工
  - `getEmployee(id: string): Promise<Employee>`：获取特定员工
  - `createEmployee(employee: Employee): Promise<Employee>`：创建员工
  - `updateEmployee(id: string, employee: Employee): Promise<Employee>`：更新员工
  - `deleteEmployee(id: string): Promise<void>`：删除员工

- **任务服务**：任务相关的API服务
  - `getTasks(): Promise<Task[]>`：获取所有任务
  - `getTask(id: string): Promise<Task>`：获取特定任务
  - `createTask(task: Task): Promise<Task>`：创建任务
  - `updateTask(id: string, task: Task): Promise<Task>`：更新任务
  - `deleteTask(id: string): Promise<void>`：删除任务
  - `assignTask(id: string, employeeId: string): Promise<Task>`：分配任务
  - `executeTask(id: string): Promise<Task>`：执行任务
  - `getTaskStatus(id: string): Promise<TaskStatus>`：获取任务状态

- **系统服务**：系统相关的API服务
  - `getSystemStatus(): Promise<SystemStatus>`：获取系统状态
  - `getSystemMetrics(): Promise<SystemMetrics>`：获取系统指标
  - `restartSystem(): Promise<void>`：重启系统
  - `shutdownSystem(): Promise<void>`：关闭系统

- **配置服务**：配置相关的API服务
  - `getConfigs(): Promise<Config[]>`：获取所有配置
  - `getConfig(key: string): Promise<Config>`：获取特定配置
  - `updateConfig(key: string, value: any): Promise<Config>`：更新配置
  - `deleteConfig(key: string): Promise<void>`：删除配置

#### 3.3.2 WebSocket服务

- **连接管理**：管理WebSocket连接
- **事件订阅**：订阅WebSocket事件
- **事件处理**：处理WebSocket事件

#### 3.3.3 工具服务

- **认证服务**：处理用户认证
- **存储服务**：处理本地存储
- **日志服务**：处理日志记录

### 3.4 路由层

#### 3.4.1 路由配置

- **路由定义**：定义路由路径和组件
- **路由嵌套**：支持路由嵌套
- **路由参数**：支持路由参数

#### 3.4.2 路由守卫

- **全局守卫**：全局路由守卫
- **路由守卫**：特定路由守卫
- **组件守卫**：组件内守卫

#### 3.4.3 路由跳转

- **编程式导航**：通过代码跳转路由
- **声明式导航**：通过链接跳转路由

## 4. 数据模型

### 4.1 员工模型

```typescript
interface Employee {
  id: string;
  name: string;
  type: string;
  status: string;
  config: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}
```

### 4.2 任务模型

```typescript
interface Task {
  id: string;
  name: string;
  description: string;
  status: string;
  priority: number;
  assignedTo: string;
  createdAt: string;
  updatedAt: string;
  startedAt?: string;
  completedAt?: string;
}
```

### 4.3 系统模型

```typescript
interface SystemStatus {
  id: string;
  name: string;
  status: string;
  version: string;
  startedAt: string;
  uptime: number;
}

interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: number;
}
```

### 4.4 配置模型

```typescript
interface Config {
  key: string;
  value: any;
  description: string;
  createdAt: string;
  updatedAt: string;
}
```

## 5. 页面设计

### 5.1 登录页面

- **登录表单**：用户名和密码输入
- **登录按钮**：提交登录请求
- **记住我**：记住登录状态
- **忘记密码**：重置密码链接

### 5.2 仪表盘页面

- **系统概览**：显示系统状态和关键指标
- **员工概览**：显示员工数量和状态分布
- **任务概览**：显示任务数量和状态分布
- **最近活动**：显示最近的系统活动

### 5.3 员工管理页面

- **员工列表**：显示所有员工
- **员工详情**：显示员工详细信息
- **员工创建**：创建新员工
- **员工编辑**：编辑员工信息
- **员工删除**：删除员工

### 5.4 任务管理页面

- **任务列表**：显示所有任务
- **任务详情**：显示任务详细信息
- **任务创建**：创建新任务
- **任务编辑**：编辑任务信息
- **任务删除**：删除任务
- **任务分配**：分配任务给员工
- **任务执行**：执行任务

### 5.5 系统监控页面

- **系统状态**：显示系统状态
- **系统指标**：显示系统指标
- **系统日志**：显示系统日志
- **系统操作**：提供系统操作按钮

### 5.6 配置中心页面

- **配置列表**：显示所有配置
- **配置详情**：显示配置详细信息
- **配置编辑**：编辑配置信息
- **配置删除**：删除配置

## 6. 通信协议

### 6.1 API通信

- **请求格式**：HTTP请求
- **响应格式**：JSON格式
- **认证方式**：JWT令牌认证
- **错误处理**：HTTP状态码和错误消息

### 6.2 WebSocket通信

- **连接建立**：WebSocket握手
- **消息格式**：JSON格式
- **认证方式**：JWT令牌认证
- **心跳机制**：定期发送心跳消息

## 7. 安全设计

### 7.1 认证与授权

- **用户认证**：使用JWT令牌认证
- **用户授权**：基于角色的访问控制
- **令牌管理**：令牌的生成、验证和刷新

### 7.2 数据安全

- **数据加密**：敏感数据的加密
- **数据验证**：输入数据的验证
- **XSS防护**：防止跨站脚本攻击
- **CSRF防护**：防止跨站请求伪造

## 8. 部署设计

### 8.1 构建部署

- **开发构建**：用于开发环境
- **生产构建**：用于生产环境
- **静态部署**：部署到静态服务器

### 8.2 环境配置

- **开发环境**：用于开发和测试
- **生产环境**：用于生产部署

## 9. 与其他组件的关系

### 9.1 与cybercorp_server的关系

- **发送请求**：向服务器发送请求
- **接收响应**：接收服务器的响应
- **接收事件**：接收服务器的事件

### 9.2 与cybercorp_oper的关系

- **间接关系**：通过服务器间接交互

## 10. 未来扩展

### 10.1 功能扩展

- **支持更多员工类型**：支持更多类型的虚拟员工
- **支持更多任务类型**：支持更多类型的任务
- **支持更多系统功能**：支持更多系统功能

### 10.2 技术扩展

- **支持移动端**：支持移动端访问
- **支持离线模式**：支持离线使用
- **支持PWA**：支持渐进式Web应用