#!/usr/bin/env python3
"""CyberCorp Desktop Client - 图形界面客户端"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import requests
import websocket
from datetime import datetime
import logging
import os
import sys
import psutil

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SingleInstanceChecker:
    """单实例检查器"""
    
    @staticmethod
    def is_already_running():
        """检查是否已有实例在运行"""
        current_pid = os.getpid()
        current_name = os.path.basename(sys.argv[0])
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] == current_pid:
                    continue
                    
                if proc.info['name'] == current_name or any(current_name in cmd for cmd in (proc.info['cmdline'] or [])):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

class HotReloadManager:
    """热重载管理器"""
    
    def __init__(self, client_instance):
        self.client = client_instance
        self.last_modified = {}
        self.watching = False
        self.reload_thread = None
        
    def start_watching(self):
        """开始监控文件变化"""
        if self.watching:
            return
            
        self.watching = True
        self.reload_thread = threading.Thread(target=self._watch_files, daemon=True)
        self.reload_thread.start()
        
    def stop_watching(self):
        """停止监控"""
        self.watching = False
        
    def _watch_files(self):
        """监控文件变化"""
        watch_files = [
            'cybercorp/desktop_client.py',
            'cybercorp/server.py'
        ]
        
        while self.watching:
            try:
                for file_path in watch_files:
                    if os.path.exists(file_path):
                        current_mtime = os.path.getmtime(file_path)
                        
                        if file_path not in self.last_modified:
                            self.last_modified[file_path] = current_mtime
                        elif self.last_modified[file_path] < current_mtime:
                            self.last_modified[file_path] = current_mtime
                            self.client.log_message(f"检测到文件变化: {file_path}")
                            self.client.trigger_hot_reload()
                            
                time.sleep(1)
            except Exception as e:
                logger.error(f"热重载监控错误: {e}")
                time.sleep(5)

class CyberCorpDesktopClient:
    def __init__(self):
        # 检查单实例
        if SingleInstanceChecker.is_already_running():
            messagebox.showwarning("警告", "CyberCorp客户端已在运行中！")
            sys.exit(0)
            
        self.root = tk.Tk()
        self.root.title("CyberCorp 动态规划系统 - 桌面客户端")
        self.root.geometry("1200x800")
        
        # 热重载管理器
        self.hot_reload = HotReloadManager(self)
        
        # 服务器配置
        self.server_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws"
        
        # 数据存储
        self.employees = []
        self.tasks = []
        self.dashboard_data = {}
        
        # WebSocket
        self.ws = None
        self.ws_thread = None
        
        self.setup_ui()
        self.start_websocket()
        self.hot_reload.start_watching()
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标签页
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 监控面板
        self.setup_dashboard_tab(notebook)
        
        # 员工管理
        self.setup_employees_tab(notebook)
        
        # 任务管理
        self.setup_tasks_tab(notebook)
        
        # 系统状态
        self.setup_status_tab(notebook)
        
        # 热重载控制
        self.setup_hot_reload_tab(notebook)
        
    def setup_hot_reload_tab(self, notebook):
        """设置热重载控制标签页"""
        reload_frame = ttk.Frame(notebook)
        notebook.add(reload_frame, text="热重载")
        
        ttk.Label(reload_frame, text="热重载控制面板", font=("Arial", 14, "bold")).pack(pady=10)
        
        # 控制按钮
        control_frame = ttk.Frame(reload_frame)
        control_frame.pack(pady=20)
        
        self.reload_status = tk.StringVar(value="监控已启动")
        ttk.Label(control_frame, textvariable=self.reload_status).pack(pady=10)
        
        ttk.Button(control_frame, text="手动触发重载", 
                  command=self.trigger_hot_reload).pack(pady=5)
        
        ttk.Button(control_frame, text="停止监控", 
                  command=self.hot_reload.stop_watching).pack(pady=5)
        
        ttk.Button(control_frame, text="启动监控", 
                  command=self.hot_reload.start_watching).pack(pady=5)
        
        # 测试区域
        test_frame = ttk.LabelFrame(reload_frame, text="热重载测试")
        test_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ttk.Label(test_frame, text="测试步骤：").pack(anchor=tk.W, padx=5, pady=5)
        ttk.Label(test_frame, text="1. 修改 desktop_client.py 文件").pack(anchor=tk.W, padx=5)
        ttk.Label(test_frame, text="2. 观察日志中的热重载提示").pack(anchor=tk.W, padx=5)
        ttk.Label(test_frame, text="3. 验证界面是否自动更新").pack(anchor=tk.W, padx=5)
        
        self.test_log = tk.Text(test_frame, height=8)
        self.test_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def trigger_hot_reload(self):
        """触发热重载"""
        self.log_message("正在执行热重载...")
        self.reload_status.set("正在重载...")
        
        # 重新加载数据
        threading.Thread(target=self.fetch_initial_data, daemon=True).start()
        
        # 更新UI
        self.root.after(1000, lambda: self.reload_status.set("重载完成"))
        
    def setup_dashboard_tab(self, notebook):
        """设置监控面板"""
        dashboard_frame = ttk.Frame(notebook)
        notebook.add(dashboard_frame, text="监控面板")
        
        # 标题
        title = ttk.Label(dashboard_frame, text="CyberCorp 实时监控", 
                         font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # 统计框架
        stats_frame = ttk.Frame(dashboard_frame)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 统计标签
        self.total_employees_label = ttk.Label(stats_frame, text="总员工: 0", 
                                             font=("Arial", 12))
        self.total_employees_label.grid(row=0, column=0, padx=20)
        
        self.total_tasks_label = ttk.Label(stats_frame, text="总任务: 0", 
                                         font=("Arial", 12))
        self.total_tasks_label.grid(row=0, column=1, padx=20)
        
        self.active_tasks_label = ttk.Label(stats_frame, text="活跃任务: 0", 
                                          font=("Arial", 12))
        self.active_tasks_label.grid(row=0, column=2, padx=20)
        
        self.completed_tasks_label = ttk.Label(stats_frame, text="已完成: 0", 
                                             font=("Arial", 12))
        self.completed_tasks_label.grid(row=0, column=3, padx=20)
        
        # 实时日志
        log_frame = ttk.LabelFrame(dashboard_frame, text="系统日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.log_text = tk.Text(log_frame, height=15, width=80)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, 
                                command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def setup_employees_tab(self, notebook):
        """设置员工管理标签页"""
        employees_frame = ttk.Frame(notebook)
        notebook.add(employees_frame, text="员工管理")
        
        # 员工列表框架
        list_frame = ttk.LabelFrame(employees_frame, text="员工列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建Treeview
        columns = ("ID", "姓名", "角色", "状态", "技能", "当前任务")
        self.employee_tree = ttk.Treeview(list_frame, columns=columns, 
                                        show="headings", height=10)
        
        for col in columns:
            self.employee_tree.heading(col, text=col)
            self.employee_tree.column(col, width=150)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                command=self.employee_tree.yview)
        self.employee_tree.configure(yscrollcommand=scrollbar.set)
        
        self.employee_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(employees_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        refresh_btn = ttk.Button(button_frame, text="刷新", 
                               command=self.refresh_employees)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        add_btn = ttk.Button(button_frame, text="添加员工", 
                           command=self.add_employee_dialog)
        add_btn.pack(side=tk.LEFT, padx=5)
        
    def setup_tasks_tab(self, notebook):
        """设置任务管理标签页"""
        tasks_frame = ttk.Frame(notebook)
        notebook.add(tasks_frame, text="任务管理")
        
        # 任务列表框架
        list_frame = ttk.LabelFrame(tasks_frame, text="任务列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建Treeview
        columns = ("ID", "名称", "描述", "优先级", "状态", "员工", "创建时间")
        self.task_tree = ttk.Treeview(list_frame, columns=columns, 
                                    show="headings", height=10)
        
        for col in columns:
            self.task_tree.heading(col, text=col)
            self.task_tree.column(col, width=120)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(tasks_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        refresh_btn = ttk.Button(button_frame, text="刷新", 
                               command=self.refresh_tasks)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        add_btn = ttk.Button(button_frame, text="创建任务", 
                           command=self.create_task_dialog)
        add_btn.pack(side=tk.LEFT, padx=5)
        
    def setup_status_tab(self, notebook):
        """设置系统状态标签页"""
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="系统状态")
        
        # 连接状态
        conn_frame = ttk.LabelFrame(status_frame, text="连接状态")
        conn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.connection_label = ttk.Label(conn_frame, text="服务器: 未连接", 
                                        font=("Arial", 12))
        self.connection_label.pack(pady=10)
        
        # 系统信息
        info_frame = ttk.LabelFrame(status_frame, text="系统信息")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.info_text = tk.Text(info_frame, height=10, width=60)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 连接按钮
        connect_btn = ttk.Button(conn_frame, text="连接服务器", 
                               command=self.connect_to_server)
        connect_btn.pack(pady=5)
        
    def start_websocket(self):
        """启动WebSocket连接"""
        self.ws_thread = threading.Thread(target=self.run_websocket, daemon=True)
        self.ws_thread.start()
        
    def run_websocket(self):
        """运行WebSocket客户端"""
        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self.on_websocket_message,
                on_error=self.on_websocket_error,
                on_close=self.on_websocket_close,
                on_open=self.on_websocket_open
            )
            self.ws.run_forever()
        except Exception as e:
            self.log_message(f"WebSocket错误: {e}")
            
    def on_websocket_open(self, ws):
        """WebSocket连接打开"""
        self.connection_label.config(text="服务器: 已连接 (WebSocket)")
        self.log_message("WebSocket连接已建立")
        
    def on_websocket_message(self, ws, message):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "task_created":
                self.log_message(f"新任务创建: {data.get('task_name')}")
                self.refresh_tasks()
            elif message_type == "task_cancelled":
                self.log_message(f"任务取消: {data.get('task_id')}")
                self.refresh_tasks()
            elif message_type == "employee_created":
                self.log_message(f"新员工: {data.get('employee_name')}")
                self.refresh_employees()
        except Exception as e:
            self.log_message(f"WebSocket消息处理错误: {e}")
            
    def on_websocket_error(self, ws, error):
        """WebSocket错误处理"""
        self.connection_label.config(text=f"服务器: WebSocket错误 - {error}")
        self.log_message(f"WebSocket错误: {error}")
        
    def on_websocket_close(self, ws, close_status_code, close_msg):
        """WebSocket连接关闭"""
        self.connection_label.config(text="服务器: WebSocket断开")
        self.log_message("WebSocket连接断开")
        
    def connect_to_server(self):
        """连接到服务器"""
        threading.Thread(target=self.fetch_initial_data, daemon=True).start()
        
    def fetch_initial_data(self):
        """获取初始数据"""
        try:
            # 获取员工数据
            response = requests.get(f"{self.server_url}/api/employees")
            if response.status_code == 200:
                self.employees = response.json()
                self.root.after(0, self.update_employee_display)
                
            # 获取任务数据
            response = requests.get(f"{self.server_url}/api/tasks")
            if response.status_code == 200:
                self.tasks = response.json()
                self.root.after(0, self.update_task_display)
                
            # 获取仪表板数据
            response = requests.get(f"{self.server_url}/api/monitoring/dashboard")
            if response.status_code == 200:
                self.dashboard_data = response.json()
                self.root.after(0, self.update_dashboard)
                
            self.connection_label.config(text="服务器: 已连接")
            self.log_message("数据加载完成")
            
        except Exception as e:
            self.connection_label.config(text=f"服务器: 连接失败 - {e}")
            self.log_message(f"数据加载失败: {e}")
            
    def update_employee_display(self):
        """更新员工显示"""
        for item in self.employee_tree.get_children():
            self.employee_tree.delete(item)
            
        for emp in self.employees:
            self.employee_tree.insert("", "end", values=(
                emp["id"][:8] + "...",
                emp["name"],
                emp["role"],
                emp["state"],
                ", ".join(emp["skills"][:3]) if emp["skills"] else "无",
                emp["current_task"] or "无"
            ))
            
    def update_task_display(self):
        """更新任务显示"""
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
            
        for task in self.tasks:
            self.task_tree.insert("", "end", values=(
                task["id"][:8] + "...",
                task["name"],
                task["description"][:20] + "..." if len(task["description"]) > 20 else task["description"],
                task["priority"],
                task["status"],
                task["assigned_employee"] or "未分配",
                task["created_at"][:19] if len(task["created_at"]) > 19 else task["created_at"]
            ))
            
    def update_dashboard(self):
        """更新仪表板"""
        if self.dashboard_data:
            system_status = self.dashboard_data.get("system_status", {})
            self.total_employees_label.config(
                text=f"总员工: {system_status.get('total_employees', 0)}")
            self.total_tasks_label.config(
                text=f"总任务: {system_status.get('total_tasks', 0)}")
            self.active_tasks_label.config(
                text=f"活跃任务: {system_status.get('active_tasks', 0)}")
            self.completed_tasks_label.config(
                text=f"已完成: {system_status.get('completed_tasks', 0)}")
                
    def refresh_employees(self):
        """刷新员工数据"""
        threading.Thread(target=self.fetch_employees, daemon=True).start()
        
    def fetch_employees(self):
        """获取员工数据"""
        try:
            response = requests.get(f"{self.server_url}/api/employees")
            if response.status_code == 200:
                self.employees = response.json()
                self.root.after(0, self.update_employee_display)
        except Exception as e:
            self.log_message(f"刷新员工失败: {e}")
            
    def refresh_tasks(self):
        """刷新任务数据"""
        threading.Thread(target=self.fetch_tasks, daemon=True).start()
        
    def fetch_tasks(self):
        """获取任务数据"""
        try:
            response = requests.get(f"{self.server_url}/api/tasks")
            if response.status_code == 200:
                self.tasks = response.json()
                self.root.after(0, self.update_task_display)
        except Exception as e:
            self.log_message(f"刷新任务失败: {e}")
            
    def add_employee_dialog(self):
        """添加员工对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加新员工")
        dialog.geometry("300x200")
        
        ttk.Label(dialog, text="姓名:").pack(pady=5)
        name_entry = ttk.Entry(dialog)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="角色:").pack(pady=5)
        role_var = tk.StringVar()
        role_combo = ttk.Combobox(dialog, textvariable=role_var, 
                                values=["ceo", "secretary", "developer", 
                                       "analyst", "operator", "monitor"])
        role_combo.pack(pady=5)
        
        def add_employee():
            name = name_entry.get()
            role = role_var.get()
            if name and role:
                threading.Thread(target=self.create_employee, 
                               args=(name, role), daemon=True).start()
                dialog.destroy()
                
        ttk.Button(dialog, text="添加", command=add_employee).pack(pady=10)
        
    def create_employee(self, name, role):
        """创建员工"""
        try:
            response = requests.post(
                f"{self.server_url}/api/employees",
                json={"name": name, "role": role}
            )
            if response.status_code == 200:
                self.log_message(f"员工 {name} 创建成功")
                self.refresh_employees()
        except Exception as e:
            self.log_message(f"创建员工失败: {e}")
            
    def create_task_dialog(self):
        """创建任务对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("创建新任务")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="任务名称:").pack(pady=5)
        name_entry = ttk.Entry(dialog)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="描述:").pack(pady=5)
        desc_entry = tk.Text(dialog, height=3, width=30)
        desc_entry.pack(pady=5)
        
        ttk.Label(dialog, text="优先级 (1-5):").pack(pady=5)
        priority_entry = ttk.Entry(dialog)
        priority_entry.insert(0, "3")
        priority_entry.pack(pady=5)
        
        def create_task():
            name = name_entry.get()
            desc = desc_entry.get("1.0", tk.END).strip()
            try:
                priority = int(priority_entry.get())
            except ValueError:
                priority = 3
                
            if name and desc:
                threading.Thread(target=self.create_task_async, 
                               args=(name, desc, priority), daemon=True).start()
                dialog.destroy()
                
        ttk.Button(dialog, text="创建", command=create_task).pack(pady=10)
        
    def