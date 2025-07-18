#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面窗口管理应用程序
左侧：窗口列表
右侧：窗口结构化数据显示
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from window_manager import WindowManager
from window_analyzer import WindowAnalyzer
from logger import app_logger


class DesktopWindowApp:
    def __init__(self, root):
        app_logger.info("初始化桌面窗口管理器")
        self.root = root
        self.root.title("桌面窗口管理器")
        self.root.geometry("1200x800")
        
        try:
            self.window_manager = WindowManager()
            self.window_analyzer = WindowAnalyzer()
            self.selected_window = None
            
            self.setup_ui()
            self.refresh_window_list()
            app_logger.info("桌面窗口管理器初始化完成")
            
        except Exception as e:
            app_logger.exception(f"初始化失败: {str(e)}")
            messagebox.showerror("初始化错误", f"程序初始化失败: {str(e)}")
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧面板 - 窗口列表
        left_frame = ttk.LabelFrame(main_frame, text="窗口列表", width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        # 刷新按钮
        refresh_btn = ttk.Button(left_frame, text="刷新窗口列表", command=self.refresh_window_list)
        refresh_btn.pack(pady=5)
        
        # 窗口列表
        self.window_listbox = tk.Listbox(left_frame, selectmode=tk.SINGLE)
        self.window_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.window_listbox.bind('<<ListboxSelect>>', self.on_window_select)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.window_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.window_listbox.config(yscrollcommand=scrollbar.set)
        
        # 右侧面板 - 窗口操作区
        right_frame = ttk.LabelFrame(main_frame, text="窗口结构化数据")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 窗口信息显示区
        self.info_text = tk.Text(right_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 信息显示区滚动条
        info_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=info_scrollbar.set)
        
        # 分析按钮
        analyze_btn = ttk.Button(right_frame, text="分析窗口结构", command=self.analyze_window)
        analyze_btn.pack(pady=5)
    
    def refresh_window_list(self):
        """刷新窗口列表"""
        try:
            app_logger.info("刷新窗口列表")
            self.window_listbox.delete(0, tk.END)
            windows = self.window_manager.get_all_windows()
            
            for window in windows:
                hwnd, title = window['hwnd'], window['title']
                display_text = f"[{hwnd}] {title}"
                self.window_listbox.insert(tk.END, display_text)
            
            self.window_listbox.insert(0, f"找到 {len(windows)} 个窗口")
            app_logger.info(f"窗口列表刷新完成，共 {len(windows)} 个窗口")
            
        except Exception as e:
            app_logger.exception(f"刷新窗口列表失败: {str(e)}")
            messagebox.showerror("错误", f"刷新窗口列表失败: {str(e)}")
    
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
            
            info_str = f"""窗口句柄: {info['hwnd']}
窗口标题: {info['title']}
窗口类名: {info['class_name']}
窗口位置: ({info['rect'][0]}, {info['rect'][1]})
窗口大小: {info['rect'][2] - info['rect'][0]} x {info['rect'][3] - info['rect'][1]}
是否可见: {'是' if info['visible'] else '否'}
是否启用: {'是' if info['enabled'] else '否'}

点击"分析窗口结构"按钮获取详细的结构化数据...
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
        
        app_logger.info(f"开始分析窗口 {self.selected_window}")
        
        # 在新线程中执行分析，避免界面卡顿
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, "\n\n正在分析窗口结构...\n")
        self.info_text.config(state=tk.DISABLED)
        
        def analyze_thread():
            try:
                analysis_result = self.window_analyzer.analyze_window(self.selected_window)
                app_logger.info(f"窗口 {self.selected_window} 分析完成")
                
                # 在主线程中更新UI
                self.root.after(0, self.display_analysis_result, analysis_result)
                
            except Exception as e:
                app_logger.exception(f"窗口 {self.selected_window} 分析失败: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"窗口分析失败: {str(e)}"))
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    def display_analysis_result(self, result):
        """显示分析结果"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, "\n" + "="*50 + "\n")
        self.info_text.insert(tk.END, "窗口结构化数据分析结果:\n")
        self.info_text.insert(tk.END, "="*50 + "\n\n")
        
        if result.get('elements'):
            self.info_text.insert(tk.END, f"发现 {len(result['elements'])} 个UI元素:\n\n")
            
            for i, element in enumerate(result['elements'], 1):
                element_info = f"""元素 {i}:
  类型: {element.get('type', 'Unknown')}
  文本: {element.get('text', 'N/A')}
  位置: ({element.get('x', 0)}, {element.get('y', 0)})
  大小: {element.get('width', 0)} x {element.get('height', 0)}
  是否可见: {'是' if element.get('visible', False) else '否'}
  是否可点击: {'是' if element.get('clickable', False) else '否'}

"""
                self.info_text.insert(tk.END, element_info)
        
        if result.get('screenshot_path'):
            self.info_text.insert(tk.END, f"窗口截图已保存: {result['screenshot_path']}\n")
        
        self.info_text.config(state=tk.DISABLED)
        self.info_text.see(tk.END)


def main():
    try:
        app_logger.info("启动桌面窗口管理器")
        root = tk.Tk()
        app = DesktopWindowApp(root)
        app_logger.info("进入主循环")
        root.mainloop()
        app_logger.info("程序正常退出")
        
    except Exception as e:
        app_logger.exception(f"程序异常退出: {str(e)}")
        messagebox.showerror("程序错误", f"程序运行时发生严重错误: {str(e)}")


if __name__ == "__main__":
    main() 