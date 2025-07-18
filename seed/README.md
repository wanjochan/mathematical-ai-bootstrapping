# CyberCorp 种子项目

一个轻量级的虚拟同事系统，用于模拟和管理AI员工。

## 功能

- 添加和管理虚拟同事
- 创建和分配任务
- 跟踪任务进度
- 简单的命令行界面

## 快速开始

1. 克隆仓库
2. 运行以下命令：

```bash
# 添加新同事
python main.py add --name "张三" --role "开发者" --skills "编程" "测试"

# 创建新任务
python main.py task --title "实现登录功能" --desc "实现用户登录界面和认证逻辑" --priority high

# 查看系统状态
python main.py status
```

## 项目结构

```
seed/
├── core/
│   └── colleague.py    # 虚拟同事核心实现
├── main.py            # 主程序入口
└── README.md          # 项目文档
```

## 开发

目前项目处于早期开发阶段，欢迎贡献代码和想法。
