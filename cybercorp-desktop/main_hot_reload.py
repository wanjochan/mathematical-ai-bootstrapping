#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支持热重载的桌面窗口管理器主程序
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from window_manager import WindowManager
from window_analyzer import WindowAnalyzer
from logger import app_logger
from hot_reload import global_reloader, global_api
import ui_components


class HotReloadDesktopApp:
    def __init__(self, root):
        app_logger.info("初始化热重载桌面窗口管理器")
        self.root = root
        self.root.title("桌面窗口管理器 (热重载版)")
        self.root.geometry("1400x900")
        
        # 核心组件
        self.window_manager = WindowManager()
        self.window_analyzer = WindowAnalyzer()
        self.selected_window = None
        
        # UI组件实例
        self.toolbar = None
        self.window_list_panel = None
        self.analysis_panel = None
        
        # 主容器
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # 设置热重载
        self.setup_hot_reload()
        
        # 初始化UI
        self.init_ui()
        
        # 启动API服务器
        global_api.start_api_server()
        
        app_logger.info("热重载桌面窗口管理器初始化完成")
    
    def setup_hot_reload(self):
        """设置热重载"""
        # 注册可重载的组件
        global_reloader.register_component(
            "toolbar", 
            "ui_components", 
            "ToolBar",
            self.reload_toolbar
        )
        
        global_reloader.register_component(
            "window_list_panel", 
            "ui_components", 
            "WindowListPanel",
            self.reload_window_list_panel
        )
        
        global_reloader.register_component(
            "analysis_panel", 
            "ui_components", 
            "WindowAnalysisPanel",
            self.reload_analysis_panel
        )
        
        # 开始监控文件变化
        global_reloader.start_watching(['ui_components.py'])
        
        app_logger.info("热重载设置完成")
    
    def init_ui(self):
        """初始化UI"""
        self.create_toolbar()
        self.create_panels()
        self.refresh_window_list()
    
    def create_toolbar(self):
        """创建工具栏"""
        if self.toolbar:
            self.toolbar.frame.destroy()
        
        self.toolbar = ui_components.ToolBar(self.main_container)
        app_logger.info("工具栏创建完成")
    
    def create_panels(self):
        """创建面板"""
        # 面板容器
        if hasattr(self, 'panels_frame'):
            self.panels_frame.destroy()
        
        self.panels_frame = ttk.Frame(self.main_container)
        self.panels_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左右面板
        self.create_window_list_panel()
        self.create_analysis_panel()
    
    def create_window_list_panel(self):
        """创建窗口列表面板"""
        if self.window_list_panel:
            self.window_list_panel.frame.destroy()
        
        self.window_list_panel = ui_components.WindowListPanel(
            self.panels_frame,
            refresh_callback=self.refresh_window_list,
            select_callback=self.on_window_select
        )
        app_logger.info("窗口列表面板创建完成")
    
    def create_analysis_panel(self):
        """创建分析面板"""
        if self.analysis_panel:
            self.analysis_panel.frame.destroy()
        
        self.analysis_panel = ui_components.WindowAnalysisPanel(
            self.panels_frame,
            analyze_callback=self.analyze_window
        )
        app_logger.info("分析面板创建完成")
    
    def refresh_window_list(self):
        """刷新窗口列表"""
        try:
            app_logger.info("刷新窗口列表")
            windows = self.window_manager.get_all_windows()
            self.window_list_panel.update_window_list(windows)
            app_logger.info(f"窗口列表刷新完成，共 {len(windows)} 个窗口")
            
        except Exception as e:
            app_logger.exception(f"刷新窗口列表失败: {str(e)}")
            messagebox.showerror("错误", f"刷新窗口列表失败: {str(e)}")
    
    def on_window_select(self, event):
        """窗口选择事件"""
        selection = self.window_list_panel.window_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.window_list_panel.window_listbox.get(selection[0])
        if selected_text.startswith("找到"):
            return
        
        try:
            hwnd_str = selected_text.split(']')[0][1:]
            self.selected_window = int(hwnd_str)
            
            # 显示基本窗口信息
            self.show_window_info()
            
        except (ValueError, IndexError) as e:
            app_logger.exception(f"解析窗口句柄失败: {str(e)}")
            messagebox.showerror("错误", f"解析窗口句柄失败: {str(e)}")
    
    def show_window_info(self):
        """显示窗口基本信息"""
        if not self.selected_window:
            return
        
        try:
            info = self.window_manager.get_window_info(self.selected_window)
            
            info_str = f"""🪟 窗口基本信息:

📋 窗口句柄: {info['hwnd']}
📝 窗口标题: {info['title']}
🏷️ 窗口类名: {info['class_name']}
📍 窗口位置: ({info['rect'][0]}, {info['rect'][1]})
📏 窗口大小: {info['rect'][2] - info['rect'][0]} x {info['rect'][3] - info['rect'][1]}
👁️ 是否可见: {'是' if info['visible'] else '否'}
✅ 是否启用: {'是' if info['enabled'] else '否'}
🔧 进程名称: {info['process_name']}
🆔 进程ID: {info['pid']}
📊 窗口状态: {info['state']}

点击"🔍 分析窗口结构"按钮获取详细的结构化数据...
"""
            
            self.analysis_panel.update_info(info_str)
            
        except Exception as e:
            app_logger.exception(f"获取窗口信息失败: {str(e)}")
            messagebox.showerror("错误", f"获取窗口信息失败: {str(e)}")
    
    def analyze_window(self):
        """分析窗口结构"""
        if not self.selected_window:
            app_logger.warning("用户未选择窗口就尝试分析")
            messagebox.showwarning("警告", "请先选择一个窗口")
            return
        
        app_logger.info(f"开始分析窗口 {self.selected_window}")
        
        def analyze_thread():
            try:
                analysis_result = self.window_analyzer.analyze_window(self.selected_window)
                app_logger.info(f"窗口 {self.selected_window} 分析完成")
                
                # 在主线程中更新UI
                self.root.after(0, self.analysis_panel.show_analysis_result, analysis_result)
                
            except Exception as e:
                app_logger.exception(f"窗口 {self.selected_window} 分析失败: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"窗口分析失败: {str(e)}"))
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    # 热重载回调函数
    def reload_toolbar(self, new_class, context=None):
        """重载工具栏"""
        try:
            app_logger.info("重载工具栏组件")
            old_frame = self.toolbar.frame if self.toolbar else None
            
            self.toolbar = new_class(self.main_container)
            
            if old_frame:
                old_frame.destroy()
            
            # 重新排序
            self.toolbar.frame.pack_forget()
            self.toolbar.frame.pack(fill=tk.X, padx=5, pady=5)
            if hasattr(self, 'panels_frame'):
                self.panels_frame.pack_forget()
                self.panels_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            app_logger.info("工具栏重载完成")
            return self.toolbar
            
        except Exception as e:
            app_logger.exception(f"工具栏重载失败: {str(e)}")
            return None
    
    def reload_window_list_panel(self, new_class, context=None):
        """重载窗口列表面板"""
        try:
            app_logger.info("重载窗口列表面板")
            
            # 保存当前状态
            current_windows = []
            selected_index = None
            if self.window_list_panel and hasattr(self.window_list_panel, 'window_listbox'):
                current_windows = [self.window_list_panel.window_listbox.get(i) 
                                 for i in range(self.window_list_panel.window_listbox.size())]
                selection = self.window_list_panel.window_listbox.curselection()
                if selection:
                    selected_index = selection[0]
            
            # 销毁旧组件
            if self.window_list_panel:
                self.window_list_panel.frame.destroy()
            
            # 创建新组件
            self.window_list_panel = new_class(
                self.panels_frame,
                refresh_callback=self.refresh_window_list,
                select_callback=self.on_window_select
            )
            
            # 恢复状态
            if current_windows:
                for window in current_windows:
                    self.window_list_panel.window_listbox.insert(tk.END, window)
                if selected_index is not None:
                    self.window_list_panel.window_listbox.selection_set(selected_index)
            
            app_logger.info("窗口列表面板重载完成")
            return self.window_list_panel
            
        except Exception as e:
            app_logger.exception(f"窗口列表面板重载失败: {str(e)}")
            return None
    
    def reload_analysis_panel(self, new_class, context=None):
        """重载分析面板"""
        try:
            app_logger.info("重载分析面板")
            
            # 保存当前内容
            current_content = ""
            if self.analysis_panel and hasattr(self.analysis_panel, 'info_text'):
                current_content = self.analysis_panel.info_text.get(1.0, tk.END)
            
            # 销毁旧组件
            if self.analysis_panel:
                self.analysis_panel.frame.destroy()
            
            # 创建新组件
            self.analysis_panel = new_class(
                self.panels_frame,
                analyze_callback=self.analyze_window
            )
            
            # 恢复内容
            if current_content.strip():
                self.analysis_panel.update_info(current_content)
            
            app_logger.info("分析面板重载完成")
            return self.analysis_panel
            
        except Exception as e:
            app_logger.exception(f"分析面板重载失败: {str(e)}")
            return None
    
    def on_closing(self):
        """程序关闭事件"""
        try:
            app_logger.info("程序正在关闭...")
            global_reloader.stop_watching()
            global_api.stop_api_server()
            self.root.destroy()
            
        except Exception as e:
            app_logger.exception(f"程序关闭时发生错误: {str(e)}")
            self.root.destroy()


def main():
    try:
        app_logger.info("启动热重载桌面窗口管理器")
        root = tk.Tk()
        app = HotReloadDesktopApp(root)
        
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