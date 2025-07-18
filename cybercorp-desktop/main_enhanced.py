#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版桌面窗口管理应用程序
新增功能：
- WinMgr 标签页：集中承载窗口管理与窗口分析 UIA 功能
- SysDash 标签页：虚拟公司主界面雏形，内置 CPU 与内存实时监控
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import psutil
import os
import getpass
from datetime import datetime
from window_manager import WindowManager
from window_analyzer import WindowAnalyzer
from logger import app_logger


class SystemMonitor:
    """系统监控类"""
    
    def __init__(self):
        self.current_user = getpass.getuser()
        self.monitoring = False
        self.monitor_thread = None
        self.callbacks = []
    
    def add_callback(self, callback):
        """添加监控数据回调函数"""
        self.callbacks.append(callback)
    
    def start_monitoring(self):
        """开始监控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                data = self.get_system_stats()
                for callback in self.callbacks:
                    callback(data)
                time.sleep(1)  # 每秒更新一次
            except Exception as e:
                app_logger.exception(f"监控循环异常: {str(e)}")
                time.sleep(5)  # 出错时等待5秒再重试
    
    def get_system_stats(self, scope="system"):
        """获取系统统计信息
        
        Args:
            scope: "system" 全系统统计, "user" 当前用户统计
        """
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 网络统计
            net_io = psutil.net_io_counters()
            
            # 进程统计
            if scope == "user":
                user_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                    try:
                        if proc.info['username'] == self.current_user:
                            user_processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                process_count = len(user_processes)
                user_cpu = sum(p['cpu_percent'] or 0 for p in user_processes)
                user_memory = sum(p['memory_percent'] or 0 for p in user_processes)
            else:
                process_count = len(psutil.pids())
                user_cpu = cpu_percent
                user_memory = memory.percent
            
            return {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'scope': scope,
                'cpu': {
                    'percent': user_cpu if scope == "user" else cpu_percent,
                    'count': cpu_count,
                    'freq': cpu_freq.current if cpu_freq else 0
                },
                'memory': {
                    'percent': user_memory if scope == "user" else memory.percent,
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used
                },
                'swap': {
                    'percent': swap.percent,
                    'total': swap.total,
                    'used': swap.used
                },
                'disk': {
                    'percent': disk.percent if scope == "system" else 0,
                    'total': disk.total if scope == "system" else 0,
                    'used': disk.used if scope == "system" else 0
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent if scope == "system" else 0,
                    'bytes_recv': net_io.bytes_recv if scope == "system" else 0
                },
                'processes': {
                    'count': process_count,
                    'user': self.current_user
                }
            }
            
        except Exception as e:
            app_logger.exception(f"获取系统统计信息失败: {str(e)}")
            return None


class WinMgrTab:
    """窗口管理标签页"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window_manager = WindowManager()
        self.window_analyzer = WindowAnalyzer()
        self.selected_window = None
        self.setup_ui()
    
    def setup_ui(self):
        """设置窗口管理界面"""
        # 主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧面板 - 窗口列表
        left_frame = ttk.LabelFrame(main_frame, text="窗口列表", width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        # 控制按钮框架
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 刷新按钮
        refresh_btn = ttk.Button(control_frame, text="刷新窗口列表", command=self.refresh_window_list)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 搜索框
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 窗口列表
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.window_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        self.window_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.window_listbox.bind('<<ListboxSelect>>', self.on_window_select)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.window_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.window_listbox.config(yscrollcommand=scrollbar.set)
        
        # 右侧面板 - 窗口操作区
        right_frame = ttk.LabelFrame(main_frame, text="窗口详细信息与UIA分析")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 操作按钮框架
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 分析按钮
        analyze_btn = ttk.Button(btn_frame, text="UIA结构分析", command=self.analyze_window)
        analyze_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 截图按钮
        screenshot_btn = ttk.Button(btn_frame, text="窗口截图", command=self.take_screenshot)
        screenshot_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 子窗口按钮
        child_btn = ttk.Button(btn_frame, text="子窗口列表", command=self.show_child_windows)
        child_btn.pack(side=tk.LEFT)
        
        # 信息显示区
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.info_text = tk.Text(info_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 信息显示区滚动条
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=info_scrollbar.set)
        
        # 初始化窗口列表
        self.all_windows = []
        self.refresh_window_list()
    
    def refresh_window_list(self):
        """刷新窗口列表"""
        try:
            app_logger.info("刷新窗口列表")
            self.window_listbox.delete(0, tk.END)
            self.all_windows = self.window_manager.get_all_windows()
            
            self.window_listbox.insert(0, f"找到 {len(self.all_windows)} 个窗口")
            
            for window in self.all_windows:
                hwnd, title, process_name = window['hwnd'], window['title'], window['process_name']
                display_text = f"[{hwnd}] {title} ({process_name})"
                self.window_listbox.insert(tk.END, display_text)
            
            app_logger.info(f"窗口列表刷新完成，共 {len(self.all_windows)} 个窗口")
            
        except Exception as e:
            app_logger.exception(f"刷新窗口列表失败: {str(e)}")
            messagebox.showerror("错误", f"刷新窗口列表失败: {str(e)}")
    
    def on_search_change(self, *args):
        """搜索框内容变化事件"""
        search_text = self.search_var.get().lower()
        self.window_listbox.delete(0, tk.END)
        
        if not search_text:
            # 显示所有窗口
            self.window_listbox.insert(0, f"找到 {len(self.all_windows)} 个窗口")
            for window in self.all_windows:
                hwnd, title, process_name = window['hwnd'], window['title'], window['process_name']
                display_text = f"[{hwnd}] {title} ({process_name})"
                self.window_listbox.insert(tk.END, display_text)
        else:
            # 过滤窗口
            filtered_windows = []
            for window in self.all_windows:
                title, process_name = window['title'], window['process_name']
                if (search_text in title.lower() or 
                    search_text in process_name.lower()):
                    filtered_windows.append(window)
            
            self.window_listbox.insert(0, f"找到 {len(filtered_windows)} 个匹配窗口")
            for window in filtered_windows:
                hwnd, title, process_name = window['hwnd'], window['title'], window['process_name']
                display_text = f"[{hwnd}] {title} ({process_name})"
                self.window_listbox.insert(tk.END, display_text)
    
    def on_window_select(self, event):
        """窗口选择事件"""
        selection = self.window_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.window_listbox.get(selection[0])
        if selected_text.startswith("找到"):
            return
        
        # 解析选中的窗口句柄
        try:
            hwnd_str = selected_text.split(']')[0][1:]  # 提取[hwnd]中的hwnd
            self.selected_window = int(hwnd_str)
            
            # 显示基本窗口信息
            self.show_window_info()
            
        except (ValueError, IndexError) as e:
            messagebox.showerror("错误", f"解析窗口句柄失败: {str(e)}")
    
    def show_window_info(self):
        """显示窗口基本信息"""
        if not self.selected_window:
            return
        
        try:
            info = self.window_manager.get_window_info(self.selected_window)
            
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            
            info_str = f"""窗口基本信息:
{'='*50}
窗口句柄: {info['hwnd']}
窗口标题: {info['title']}
窗口类名: {info['class_name']}
进程名称: {info['process_name']}
进程ID: {info['pid']}
窗口状态: {info['state']}
窗口位置: ({info['rect'][0]}, {info['rect'][1]})
窗口大小: {info['rect'][2] - info['rect'][0]} x {info['rect'][3] - info['rect'][1]}
是否可见: {'是' if info['visible'] else '否'}
是否启用: {'是' if info['enabled'] else '否'}

操作说明:
- 点击"UIA结构分析"按钮获取详细的UI元素结构
- 点击"窗口截图"按钮保存窗口截图
- 点击"子窗口列表"按钮查看子窗口信息
"""
            
            self.info_text.insert(tk.END, info_str)
            self.info_text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取窗口信息失败: {str(e)}")
    
    def analyze_window(self):
        """分析窗口结构"""
        if not self.selected_window:
            app_logger.warning("用户未选择窗口就尝试分析")
            messagebox.showwarning("警告", "请先选择一个窗口")
            return
        
        app_logger.info(f"开始UIA分析窗口 {self.selected_window}")
        
        # 在新线程中执行分析，避免界面卡顿
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, "\n\n正在进行UIA结构分析...\n")
        self.info_text.config(state=tk.DISABLED)
        
        def analyze_thread():
            try:
                analysis_result = self.window_analyzer.analyze_window(self.selected_window)
                app_logger.info(f"窗口 {self.selected_window} UIA分析完成")
                
                # 在主线程中更新UI
                self.parent.after(0, self.display_analysis_result, analysis_result)
                
            except Exception as e:
                app_logger.exception(f"窗口 {self.selected_window} UIA分析失败: {str(e)}")
                self.parent.after(0, lambda: messagebox.showerror("错误", f"UIA分析失败: {str(e)}"))
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    def take_screenshot(self):
        """窗口截图"""
        if not self.selected_window:
            messagebox.showwarning("警告", "请先选择一个窗口")
            return
        
        try:
            # 这里可以调用window_analyzer的截图功能
            result = self.window_analyzer.capture_window_screenshot(self.selected_window)
            if result and result.get('screenshot_path'):
                self.info_text.config(state=tk.NORMAL)
                self.info_text.insert(tk.END, f"\n\n窗口截图已保存: {result['screenshot_path']}\n")
                self.info_text.config(state=tk.DISABLED)
                messagebox.showinfo("成功", f"窗口截图已保存: {result['screenshot_path']}")
            else:
                messagebox.showerror("错误", "截图失败")
        except Exception as e:
            messagebox.showerror("错误", f"截图失败: {str(e)}")
    
    def show_child_windows(self):
        """显示子窗口列表"""
        if not self.selected_window:
            messagebox.showwarning("警告", "请先选择一个窗口")
            return
        
        try:
            child_windows = self.window_manager.get_child_windows(self.selected_window)
            
            self.info_text.config(state=tk.NORMAL)
            self.info_text.insert(tk.END, f"\n\n子窗口列表 (共 {len(child_windows)} 个):\n")
            self.info_text.insert(tk.END, "="*50 + "\n")
            
            for i, child in enumerate(child_windows, 1):
                child_info = f"""子窗口 {i}:
  句柄: {child['hwnd']}
  标题: {child['title']}
  类名: {child['class_name']}
  位置: ({child['rect'][0]}, {child['rect'][1]})
  大小: {child['rect'][2] - child['rect'][0]} x {child['rect'][3] - child['rect'][1]}
  可见: {'是' if child['visible'] else '否'}

"""
                self.info_text.insert(tk.END, child_info)
            
            self.info_text.config(state=tk.DISABLED)
            self.info_text.see(tk.END)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取子窗口失败: {str(e)}")
    
    def display_analysis_result(self, result):
        """显示UIA分析结果"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, "\n" + "="*50 + "\n")
        self.info_text.insert(tk.END, "UIA结构分析结果:\n")
        self.info_text.insert(tk.END, "="*50 + "\n\n")
        
        if result.get('elements'):
            self.info_text.insert(tk.END, f"发现 {len(result['elements'])} 个UI元素:\n\n")
            
            for i, element in enumerate(result['elements'], 1):
                element_info = f"""UI元素 {i}:
  类型: {element.get('type', 'Unknown')}
  文本: {element.get('text', 'N/A')}
  位置: ({element.get('x', 0)}, {element.get('y', 0)})
  大小: {element.get('width', 0)} x {element.get('height', 0)}
  是否可见: {'是' if element.get('visible', False) else '否'}
  是否可点击: {'是' if element.get('clickable', False) else '否'}
  控件ID: {element.get('automation_id', 'N/A')}

"""
                self.info_text.insert(tk.END, element_info)
        
        if result.get('screenshot_path'):
            self.info_text.insert(tk.END, f"窗口截图已保存: {result['screenshot_path']}\n")
        
        self.info_text.config(state=tk.DISABLED)
        self.info_text.see(tk.END)


class SysDashTab:
    """系统仪表板标签页"""
    
    def __init__(self, parent):
        self.parent = parent
        self.system_monitor = SystemMonitor()
        self.monitoring_scope = tk.StringVar(value="system")  # "system" 或 "user"
        self.setup_ui()
        
        # 添加监控回调
        self.system_monitor.add_callback(self.update_dashboard)
        
        # 启动监控
        self.system_monitor.start_monitoring()
    
    def setup_ui(self):
        """设置系统仪表板界面"""
        # 主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题和控制区
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 标题
        title_label = ttk.Label(header_frame, text="CyberCorp 系统监控仪表板", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # 视角切换
        scope_frame = ttk.LabelFrame(header_frame, text="统计视角")
        scope_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        system_radio = ttk.Radiobutton(scope_frame, text="全系统", 
                                      variable=self.monitoring_scope, 
                                      value="system",
                                      command=self.on_scope_change)
        system_radio.pack(side=tk.LEFT, padx=5)
        
        user_radio = ttk.Radiobutton(scope_frame, text="当前用户", 
                                    variable=self.monitoring_scope, 
                                    value="user",
                                    command=self.on_scope_change)
        user_radio.pack(side=tk.LEFT, padx=5)
        
        # 监控数据显示区
        data_frame = ttk.Frame(main_frame)
        data_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧 - 实时数据
        left_frame = ttk.LabelFrame(data_frame, text="实时监控数据")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # CPU 监控
        cpu_frame = ttk.LabelFrame(left_frame, text="CPU 使用率")
        cpu_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.cpu_label = ttk.Label(cpu_frame, text="CPU: 0.0%", font=('Arial', 12, 'bold'))
        self.cpu_label.pack(pady=5)
        
        self.cpu_progress = ttk.Progressbar(cpu_frame, length=300, mode='determinate')
        self.cpu_progress.pack(pady=5)
        
        self.cpu_info_label = ttk.Label(cpu_frame, text="核心数: 0 | 频率: 0 MHz")
        self.cpu_info_label.pack(pady=2)
        
        # 内存监控
        memory_frame = ttk.LabelFrame(left_frame, text="内存使用情况")
        memory_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.memory_label = ttk.Label(memory_frame, text="内存: 0.0%", font=('Arial', 12, 'bold'))
        self.memory_label.pack(pady=5)
        
        self.memory_progress = ttk.Progressbar(memory_frame, length=300, mode='determinate')
        self.memory_progress.pack(pady=5)
        
        self.memory_info_label = ttk.Label(memory_frame, text="已用: 0 MB / 总计: 0 MB")
        self.memory_info_label.pack(pady=2)
        
        # 进程信息
        process_frame = ttk.LabelFrame(left_frame, text="进程信息")
        process_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.process_label = ttk.Label(process_frame, text="进程数: 0", font=('Arial', 12, 'bold'))
        self.process_label.pack(pady=5)
        
        self.user_label = ttk.Label(process_frame, text="当前用户: Unknown")
        self.user_label.pack(pady=2)
        
        # 右侧 - 详细信息和历史
        right_frame = ttk.LabelFrame(data_frame, text="系统详细信息")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 详细信息显示区
        self.detail_text = tk.Text(right_frame, wrap=tk.WORD, state=tk.DISABLED, 
                                  font=('Consolas', 9))
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 详细信息滚动条
        detail_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, 
                                        command=self.detail_text.yview)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_text.config(yscrollcommand=detail_scrollbar.set)
        
        # 底部状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="系统监控已启动...")
        self.status_label.pack(side=tk.LEFT)
        
        self.time_label = ttk.Label(status_frame, text="")
        self.time_label.pack(side=tk.RIGHT)
    
    def on_scope_change(self):
        """监控视角切换事件"""
        scope = self.monitoring_scope.get()
        scope_text = "全系统" if scope == "system" else "当前用户"
        self.status_label.config(text=f"监控视角: {scope_text}")
    
    def update_dashboard(self, data):
        """更新仪表板数据"""
        if not data:
            return
        
        try:
            scope = self.monitoring_scope.get()
            
            # 如果当前视角与数据不匹配，重新获取数据
            if data['scope'] != scope:
                data = self.system_monitor.get_system_stats(scope)
                if not data:
                    return
            
            # 更新时间
            self.time_label.config(text=f"更新时间: {data['timestamp']}")
            
            # 更新CPU信息
            cpu_percent = data['cpu']['percent']
            self.cpu_label.config(text=f"CPU: {cpu_percent:.1f}%")
            self.cpu_progress['value'] = cpu_percent
            
            cpu_info = f"核心数: {data['cpu']['count']} | 频率: {data['cpu']['freq']:.0f} MHz"
            self.cpu_info_label.config(text=cpu_info)
            
            # 更新内存信息
            memory_percent = data['memory']['percent']
            self.memory_label.config(text=f"内存: {memory_percent:.1f}%")
            self.memory_progress['value'] = memory_percent
            
            memory_used_mb = data['memory']['used'] / (1024 * 1024)
            memory_total_mb = data['memory']['total'] / (1024 * 1024)
            memory_info = f"已用: {memory_used_mb:.0f} MB / 总计: {memory_total_mb:.0f} MB"
            self.memory_info_label.config(text=memory_info)
            
            # 更新进程信息
            self.process_label.config(text=f"进程数: {data['processes']['count']}")
            
            # 仅在当前用户视角时显示用户信息
            if data['scope'] == "user":
                self.user_label.config(text=f"当前用户: {data['processes']['user']}")
                self.user_label.pack(pady=2)
            else:
                # 全系统视角时隐藏用户信息
                self.user_label.pack_forget()
            
            # 更新详细信息
            self.update_detail_info(data)
            
        except Exception as e:
            app_logger.exception(f"更新仪表板失败: {str(e)}")
    
    def update_detail_info(self, data):
        """更新详细信息显示"""
        try:
            scope_text = "全系统统计" if data['scope'] == "system" else "当前用户统计"
            
            detail_info = f"""CyberCorp 系统监控报告 - {scope_text}
{'='*60}
更新时间: {data['timestamp']}
监控视角: {scope_text}

CPU 信息:
  使用率: {data['cpu']['percent']:.1f}%
  核心数: {data['cpu']['count']}
  当前频率: {data['cpu']['freq']:.0f} MHz

内存信息:
  使用率: {data['memory']['percent']:.1f}%
  总内存: {data['memory']['total'] / (1024**3):.2f} GB
  已用内存: {data['memory']['used'] / (1024**3):.2f} GB
  可用内存: {data['memory']['available'] / (1024**3):.2f} GB

交换空间:
  使用率: {data['swap']['percent']:.1f}%
  总交换空间: {data['swap']['total'] / (1024**3):.2f} GB
  已用交换空间: {data['swap']['used'] / (1024**3):.2f} GB

磁盘信息:
  使用率: {data['disk']['percent']:.1f}%
  总磁盘空间: {data['disk']['total'] / (1024**3):.2f} GB
  已用磁盘空间: {data['disk']['used'] / (1024**3):.2f} GB

网络统计:
  发送字节: {data['network']['bytes_sent']:,}
  接收字节: {data['network']['bytes_recv']:,}

进程信息:
  总进程数: {data['processes']['count']}
  当前用户: {data['processes']['user'] if data['scope'] == 'user' else 'N/A (全系统统计)'}

系统状态: {"正常" if data['cpu']['percent'] < 80 and data['memory']['percent'] < 80 else "警告"}
"""
            
            self.detail_text.config(state=tk.NORMAL)
            self.detail_text.delete(1.0, tk.END)
            self.detail_text.insert(tk.END, detail_info)
            self.detail_text.config(state=tk.DISABLED)
            
        except Exception as e:
            app_logger.exception(f"更新详细信息失败: {str(e)}")


class EnhancedDesktopApp:
    """增强版桌面窗口管理应用程序"""
    
    def __init__(self, root):
        app_logger.info("启动增强版桌面窗口管理器")
        self.root = root
        self.root.title("CyberCorp 桌面管理器 - 增强版")
        self.root.geometry("1400x900")
        
        try:
            self.setup_ui()
            app_logger.info("增强版桌面窗口管理器初始化完成")
            
        except Exception as e:
            app_logger.exception(f"初始化失败: {str(e)}")
            messagebox.showerror("初始化错误", f"程序初始化失败: {str(e)}")
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标签页
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建标签页
        self.create_tabs()
    
    def create_tabs(self):
        """创建标签页"""
        # WinMgr 标签页 - 窗口管理
        winmgr_frame = ttk.Frame(self.notebook)
        self.notebook.add(winmgr_frame, text="WinMgr")
        self.winmgr_tab = WinMgrTab(winmgr_frame)
        
        # SysDash 标签页 - 系统仪表板
        sysdash_frame = ttk.Frame(self.notebook)
        self.notebook.add(sysdash_frame, text="SysDash")
        self.sysdash_tab = SysDashTab(sysdash_frame)
        
        # 原始窗口管理标签页（保留兼容性）
        legacy_frame = ttk.Frame(self.notebook)
        self.notebook.add(legacy_frame, text="Legacy")
        self.create_legacy_tab(legacy_frame)
    
    def create_legacy_tab(self, parent):
        """创建原始窗口管理界面（兼容性）"""
        # 帮助信息框架
        help_frame = ttk.Frame(parent)
        help_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(help_frame, text="CyberCorp 桌面管理器 - 帮助中心",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 帮助内容
        help_text = tk.Text(help_frame, wrap=tk.WORD, state=tk.NORMAL,
                           font=('Consolas', 10), height=25)
        help_text.pack(fill=tk.BOTH, expand=True)
        
        help_content = """
CyberCorp 桌面管理器 - 使用帮助
================================

欢迎使用增强版桌面管理器！本应用提供三大核心功能模块：

📋 功能模块说明
----------------

1. WinMgr (窗口管理器)
   • 功能：集中管理所有可见窗口
   • 特性：实时窗口列表、搜索过滤、UIA结构分析
   • 操作：选择窗口 → 查看详情 → 执行分析/截图

2. SysDash (系统仪表板)
   • 功能：实时系统资源监控
   • 特性：CPU/内存/磁盘/网络监控
   • 视角：支持"全系统"和"当前用户"两种统计模式

3. Legacy (兼容性模式)
   • 功能：保留原始界面兼容性
   • 建议：请优先使用WinMgr获取完整功能

🔍 快速上手
------------

WinMgr 使用步骤：
1. 点击"刷新窗口列表"获取当前所有窗口
2. 在搜索框输入关键词过滤窗口
3. 选择目标窗口查看详细信息
4. 点击"UIA结构分析"获取UI元素详情
5. 点击"窗口截图"保存窗口图片

SysDash 使用步骤：
1. 选择监控视角（全系统/当前用户）
2. 实时查看左侧监控数据
3. 右侧查看详细系统报告
4. 数据每秒自动更新

⚙️ 技术特性
------------

• 异步处理：UIA分析在后台线程执行
• 实时更新：监控数据每秒刷新
• 智能搜索：支持标题和进程名搜索
• 双视角监控：系统级 vs 用户级进程
• 完整日志：所有操作记录在logs目录

🛠️ 故障排除
------------

常见问题：
1. 权限不足 → 以管理员身份运行
2. 依赖缺失 → 运行 pip install -r requirements_enhanced.txt
3. UIA失败 → 检查Windows UIA服务状态

技术支持：
• 日志文件：logs/app.log
• 版本信息：v2.0 增强版
• 更新日期：2025-07-18

快捷键：
• Ctrl+Tab：切换标签页
• F5：刷新窗口列表
• Esc：退出应用
"""
        
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(help_frame, orient=tk.VERTICAL, command=help_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        help_text.config(yscrollcommand=scrollbar.set)
    
    def on_closing(self):
        """窗口关闭事件"""
        try:
            # 停止系统监控
            if hasattr(self, 'sysdash_tab'):
                self.sysdash_tab.system_monitor.stop_monitoring()
            
            app_logger.info("程序正常退出")
            self.root.destroy()
            
        except Exception as e:
            app_logger.exception(f"程序退出异常: {str(e)}")
            self.root.destroy()


def main():
    try:
        app_logger.info("启动增强版桌面窗口管理器")
        root = tk.Tk()
        app = EnhancedDesktopApp(root)
        
        # 设置关闭事件
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        app_logger.info("进入主循环")
        root.mainloop()
        app_logger.info("程序正常退出")
        
    except Exception as e:
        app_logger.exception(f"程序异常退出: {str(e)}")
        messagebox.showerror("程序错误", f"程序运行时发生严重错误: {str(e)}")


if __name__ == "__main__":
    main()