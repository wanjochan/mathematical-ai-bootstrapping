#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可重载的UI组件模块
支持热重载的界面组件
"""

import tkinter as tk
from tkinter import ttk
from logger import app_logger


class WindowListPanel:
    """左侧窗口列表面板"""
    
    def __init__(self, parent, refresh_callback=None, select_callback=None):
        self.parent = parent
        self.refresh_callback = refresh_callback
        self.select_callback = select_callback
        
        self.frame = ttk.LabelFrame(parent, text="窗口列表 (热重载版本)", width=400)
        self.setup_ui()
        app_logger.info("WindowListPanel 初始化完成")
    
    def setup_ui(self):
        """设置UI"""
        self.frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        self.frame.pack_propagate(False)
        
        # 刷新按钮 - 支持自定义样式
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=5, fill=tk.X, padx=5)
        
        refresh_btn = ttk.Button(button_frame, text="🔄 刷新窗口", command=self.on_refresh)
        refresh_btn.pack(side=tk.LEFT)
        
        # 热重载按钮
        reload_btn = ttk.Button(button_frame, text="⚡ 热重载", command=self.trigger_reload)
        reload_btn.pack(side=tk.RIGHT)
        
        # 窗口列表
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.window_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        self.window_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.window_listbox.bind('<<ListboxSelect>>', self.on_select)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.window_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.window_listbox.config(yscrollcommand=scrollbar.set)
        
        # 状态标签
        self.status_label = ttk.Label(self.frame, text="准备就绪", foreground="green")
        self.status_label.pack(pady=(0, 5))
    
    def on_refresh(self):
        """刷新事件"""
        app_logger.info("WindowListPanel: 触发刷新")
        if self.refresh_callback:
            self.refresh_callback()
    
    def on_select(self, event):
        """选择事件"""
        if self.select_callback:
            self.select_callback(event)
    
    def trigger_reload(self):
        """触发热重载"""
        app_logger.info("触发组件热重载")
        try:
            import requests
            response = requests.post('http://localhost:8888/reload', 
                                   json={'component': 'window_list_panel'})
            if response.status_code == 200:
                self.update_status("热重载成功!", "green")
            else:
                self.update_status("热重载失败!", "red")
        except Exception as e:
            app_logger.error(f"热重载请求失败: {str(e)}")
            self.update_status("热重载请求失败!", "red")
    
    def update_status(self, text, color="black"):
        """更新状态"""
        self.status_label.config(text=text, foreground=color)
        
        # 3秒后恢复默认状态
        self.frame.after(3000, lambda: self.status_label.config(text="准备就绪", foreground="green"))
    
    def update_window_list(self, windows):
        """更新窗口列表"""
        self.window_listbox.delete(0, tk.END)
        
        for window in windows:
            hwnd, title = window['hwnd'], window['title']
            display_text = f"[{hwnd}] {title}"
            self.window_listbox.insert(tk.END, display_text)
        
        self.window_listbox.insert(0, f"找到 {len(windows)} 个窗口")
        self.update_status(f"已加载 {len(windows)} 个窗口", "blue")


class WindowAnalysisPanel:
    """右侧窗口分析面板"""
    
    def __init__(self, parent, analyze_callback=None):
        self.parent = parent
        self.analyze_callback = analyze_callback
        
        self.frame = ttk.LabelFrame(parent, text="窗口结构化数据 (热重载版本)")
        self.setup_ui()
        app_logger.info("WindowAnalysisPanel 初始化完成")
    
    def setup_ui(self):
        """设置UI"""
        self.frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 顶部控制区
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 分析按钮
        analyze_btn = ttk.Button(control_frame, text="🔍 分析窗口结构", command=self.on_analyze)
        analyze_btn.pack(side=tk.LEFT)
        
        # 清空按钮
        clear_btn = ttk.Button(control_frame, text="🗑️ 清空", command=self.clear_info)
        clear_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # 保存报告按钮
        save_btn = ttk.Button(control_frame, text="💾 保存报告", command=self.save_report)
        save_btn.pack(side=tk.RIGHT)
        
        # 信息显示区
        text_frame = ttk.Frame(self.frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.info_text = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED, 
                                font=("Consolas", 10))
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        info_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=info_scrollbar.set)
        
        # 进度条
        self.progress = ttk.Progressbar(self.frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # 初始提示
        self.update_info("欢迎使用窗口分析工具!\n\n请先在左侧选择一个窗口，然后点击'分析窗口结构'按钮。\n\n🔥 这是热重载版本，支持实时更新界面!")
    
    def on_analyze(self):
        """分析事件"""
        app_logger.info("WindowAnalysisPanel: 触发分析")
        self.progress.start()
        if self.analyze_callback:
            self.analyze_callback()
    
    def clear_info(self):
        """清空信息"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state=tk.DISABLED)
        app_logger.info("分析信息已清空")
    
    def save_report(self):
        """保存报告"""
        try:
            from tkinter import filedialog
            import time
            
            content = self.info_text.get(1.0, tk.END)
            if content.strip():
                filename = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                    initialname=f"window_analysis_{int(time.time())}.txt"
                )
                
                if filename:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    app_logger.info(f"报告已保存: {filename}")
                    self.update_info(f"\n\n✅ 报告已保存到: {filename}")
            else:
                self.update_info("\n\n⚠️ 没有内容可保存")
                
        except Exception as e:
            app_logger.exception(f"保存报告失败: {str(e)}")
            self.update_info(f"\n\n❌ 保存失败: {str(e)}")
    
    def update_info(self, text, append=False):
        """更新信息显示"""
        self.info_text.config(state=tk.NORMAL)
        if not append:
            self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, text)
        self.info_text.config(state=tk.DISABLED)
        self.info_text.see(tk.END)
    
    def show_analysis_result(self, result):
        """显示分析结果"""
        self.progress.stop()
        
        # 检查分析方法
        analysis_method = result.get('analysis_method', 'Unknown')
        
        self.update_info("\n" + "="*60 + "\n")
        self.update_info(f"🔍 窗口结构化数据分析结果 ({analysis_method}):\n", True)
        self.update_info("="*60 + "\n\n", True)
        
        # 显示分析摘要（如果是UIA分析）
        if analysis_method == 'UIA_Advanced' and result.get('summary'):
            self._show_uia_summary(result['summary'])
        
        # 显示详细元素信息
        if result.get('elements'):
            self.update_info(f"✨ 发现 {len(result['elements'])} 个UI元素:\n\n", True)
            
            # 根据分析方法显示不同的详细信息
            if analysis_method == 'UIA_Advanced':
                self._show_uia_elements(result['elements'])
            else:
                self._show_traditional_elements(result['elements'])
        
        # 显示UIA详细分析结果
        if analysis_method == 'UIA_Advanced' and result.get('uia_analysis'):
            self._show_uia_detailed_analysis(result['uia_analysis'])
        
        # 显示截图信息
        if result.get('screenshot_path'):
            self.update_info(f"📸 窗口截图已保存: {result['screenshot_path']}\n", True)
        
        if result.get('labeled_screenshot_path'):
            self.update_info(f"🏷️ 标签截图已保存: {result['labeled_screenshot_path']}\n", True)
        
        self.update_info(f"\n⏰ 分析时间: {result.get('analysis_time', 'N/A')}\n", True)
    
    def _show_uia_summary(self, summary):
        """显示UIA分析摘要"""
        self.update_info("📊 分析摘要:\n", True)
        self.update_info(f"   总元素数: {summary.get('total_elements', 0)}\n", True)
        self.update_info(f"   交互元素: {summary.get('interactive_elements', 0)}\n", True)
        self.update_info(f"   文本元素: {summary.get('text_elements', 0)}\n", True)
        self.update_info(f"   控件类型: {summary.get('control_type_count', 0)} 种\n", True)
        
        complexity = summary.get('complexity_level', 'Unknown')
        complexity_emoji = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}.get(complexity, '⚪')
        self.update_info(f"   复杂度: {complexity_emoji} {complexity} ({summary.get('complexity_score', 0)}分)\n", True)
        
        accessibility = summary.get('accessibility_ratio', 0)
        acc_emoji = '🟢' if accessibility > 0.8 else '🟡' if accessibility > 0.6 else '🔴'
        self.update_info(f"   可访问性: {acc_emoji} {accessibility:.1%}\n", True)
        
        # 显示建议
        suggestions = summary.get('suggestions', [])
        if suggestions:
            self.update_info("\n💡 优化建议:\n", True)
            for suggestion in suggestions:
                self.update_info(f"   • {suggestion}\n", True)
        
        # 显示主要控件类型
        top_types = summary.get('top_control_types', [])
        if top_types:
            self.update_info("\n🏷️ 主要控件类型:\n", True)
            for ctrl_type, elements in top_types:
                self.update_info(f"   • {ctrl_type}: {len(elements)}个\n", True)
        
        self.update_info("\n" + "-"*50 + "\n\n", True)
    
    def _show_uia_elements(self, elements):
        """显示UIA元素详情"""
        interactive_elements = [e for e in elements if e.get('clickable')]
        text_elements = [e for e in elements if not e.get('clickable')]
        
        if interactive_elements:
            self.update_info(f"🎯 交互元素 ({len(interactive_elements)}个):\n\n", True)
            for i, element in enumerate(interactive_elements[:10], 1):  # 限制显示数量
                patterns = element.get('patterns', [])
                patterns_str = ', '.join(patterns) if patterns else 'None'
                
                element_info = f"""   I{i}. {element.get('type', 'Unknown')}
      文本: {element.get('text', 'N/A')[:50]}
      位置: ({element.get('x', 0)}, {element.get('y', 0)})
      大小: {element.get('width', 0)}×{element.get('height', 0)}
      模式: {patterns_str}
      ID: {element.get('automation_id', 'N/A')}

"""
                self.update_info(element_info, True)
        
        if text_elements and len(text_elements) <= 15:  # 只在文本元素不太多时显示
            self.update_info(f"📝 文本元素 ({len(text_elements)}个):\n\n", True)
            for i, element in enumerate(text_elements, 1):
                text = element.get('text', '')
                if len(text) > 100:
                    text = text[:100] + "..."
                
                self.update_info(f"   T{i}. {text}\n", True)
            self.update_info("\n", True)
    
    def _show_traditional_elements(self, elements):
        """显示传统分析的元素详情"""
        for i, element in enumerate(elements, 1):
            element_info = f"""📌 元素 {i}:
   类型: {element.get('type', 'Unknown')}
   文本: {element.get('text', 'N/A')}
   位置: ({element.get('x', 0)}, {element.get('y', 0)})
   大小: {element.get('width', 0)} x {element.get('height', 0)}
   可见: {'✓' if element.get('visible', False) else '✗'}
   可点击: {'✓' if element.get('clickable', False) else '✗'}

"""
            self.update_info(element_info, True)
    
    def _show_uia_detailed_analysis(self, uia_analysis):
        """显示UIA详细分析信息"""
        self.update_info("🔬 详细分析信息:\n\n", True)
        
        # 布局分析
        layout = uia_analysis.get('layout_analysis', {})
        if layout:
            self.update_info("🏗️ 布局分析:\n", True)
            self.update_info(f"   层次深度: {layout.get('depth_levels', 0)}\n", True)
            self.update_info(f"   可见元素: {layout.get('visible_elements_count', 0)}\n", True)
            
            bounds = layout.get('total_bounds')
            if bounds:
                self.update_info(f"   总体范围: {bounds.get('min_x', 0)},{bounds.get('min_y', 0)} - {bounds.get('max_x', 0)},{bounds.get('max_y', 0)}\n", True)
            
            density = layout.get('layout_density', 0)
            if density > 0:
                self.update_info(f"   布局密度: {density:.6f}\n", True)
            
            self.update_info("\n", True)
        
        # 控件类型分布
        type_dist = layout.get('control_type_distribution', {})
        if type_dist:
            self.update_info("📊 控件类型分布:\n", True)
            sorted_types = sorted(type_dist.items(), key=lambda x: x[1], reverse=True)
            for ctrl_type, count in sorted_types[:8]:  # 显示前8种
                self.update_info(f"   {ctrl_type}: {count}个\n", True)
            self.update_info("\n", True)
        
        # 可访问性信息
        accessibility = uia_analysis.get('accessibility_info', {})
        if accessibility:
            self.update_info("♿ 可访问性分析:\n", True)
            self.update_info(f"   可访问元素: {accessibility.get('accessible_elements', 0)}/{accessibility.get('total_elements', 0)}\n", True)
            self.update_info(f"   可访问性比例: {accessibility.get('accessibility_ratio', 0):.1%}\n", True)
            self.update_info(f"   可聚焦元素: {accessibility.get('focusable_elements', 0)}\n", True)
            self.update_info(f"   键盘导航比例: {accessibility.get('keyboard_navigable_ratio', 0):.1%}\n", True)


class ToolBar:
    """工具栏组件"""
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        app_logger.info("ToolBar 初始化完成")
    
    def setup_ui(self):
        """设置UI"""
        self.frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 左侧工具
        left_frame = ttk.Frame(self.frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_frame, text="🛠️ 桌面窗口管理器", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # 右侧工具
        right_frame = ttk.Frame(self.frame)
        right_frame.pack(side=tk.RIGHT)
        
        ttk.Button(right_frame, text="❓ 帮助", command=self.show_help).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(right_frame, text="⚙️ 设置", command=self.show_settings).pack(side=tk.RIGHT)
    
    def show_help(self):
        """显示帮助"""
        from tkinter import messagebox
        help_text = """
🔥 热重载桌面窗口管理器

功能说明：
• 左侧：窗口列表，显示当前所有窗口
• 右侧：窗口分析，显示结构化数据
• 支持热重载：修改代码后自动更新界面

热重载使用：
1. 修改 ui_components.py 文件
2. 文件保存后自动触发重载
3. 或点击"⚡ 热重载"按钮手动触发
4. 或调用 API: POST localhost:8888/reload

API接口：
• GET /status - 查看状态
• POST /reload - 触发重载
        """
        messagebox.showinfo("帮助", help_text)
    
    def show_settings(self):
        """显示设置"""
        from tkinter import messagebox
        messagebox.showinfo("设置", "设置功能开发中...") 