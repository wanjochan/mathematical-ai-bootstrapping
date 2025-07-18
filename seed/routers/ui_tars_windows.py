"""
UI-TARS Windows平台实现
基于现有Windows API的具体实现，继承抽象基类
"""

import psutil
import base64
from io import BytesIO
from typing import Dict, Any, Optional, List
from PIL import Image, ImageGrab

import win32gui
import win32con
import win32api
import win32ui
import win32process

from .ui_tars_core import WindowCaptureBase, PerformanceMetrics, UITarsConfig, WindowInfo, UIElement

class WindowsWindowCapture(WindowCaptureBase):
    """Windows平台窗口捕获实现"""
    
    def __init__(self, config: UITarsConfig = None):
        super().__init__(config)
        self._process = psutil.Process()  # 当前进程，用于性能监控
    
    def enumerate_windows(self) -> List[WindowInfo]:
        """枚举所有可见窗口"""
        windows = []
        
        def enum_windows_proc(hwnd, windows_list):
            try:
                if win32gui.IsWindow(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    is_visible = win32gui.IsWindowVisible(hwnd)
                    
                    # 包含所有窗口，不只是有标题的
                    if is_visible or title:
                        rect = win32gui.GetWindowRect(hwnd)
                        is_enabled = win32gui.IsWindowEnabled(hwnd)
                        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                        
                        window_info = WindowInfo(
                            hwnd=hwnd,
                            title=title or f"[{class_name}]",
                            class_name=class_name,
                            rect=rect,
                            is_visible=is_visible,
                            is_enabled=is_enabled,
                            process_id=process_id
                        )
                        windows_list.append(window_info)
            except Exception:
                # 忽略单个窗口的错误，继续枚举其他窗口
                pass
            return True
        
        win32gui.EnumWindows(enum_windows_proc, windows)
        # 按标题长度排序，有意义的窗口通常标题更长
        windows.sort(key=lambda w: len(w.title), reverse=True)
        return windows
    
    def find_window_by_title(self, title: str) -> Optional[int]:
        """根据标题查找窗口句柄"""
        def enum_windows_proc(hwnd, lParam):
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if title.lower() in window_title.lower():
                    lParam.append(hwnd)
            return True
            
        windows = []
        win32gui.EnumWindows(enum_windows_proc, windows)
        return windows[0] if windows else None
    
    def get_window_info(self, window_handle: int) -> WindowInfo:
        """获取窗口详细信息"""
        try:
            title = win32gui.GetWindowText(window_handle)
            class_name = win32gui.GetClassName(window_handle)
            rect = win32gui.GetWindowRect(window_handle)
            is_visible = win32gui.IsWindowVisible(window_handle)
            is_enabled = win32gui.IsWindowEnabled(window_handle)
            _, process_id = win32process.GetWindowThreadProcessId(window_handle)
            
            return WindowInfo(
                hwnd=window_handle,
                title=title,
                class_name=class_name,
                rect=rect,
                is_visible=is_visible,
                is_enabled=is_enabled,
                process_id=process_id
            )
        except Exception as e:
            raise Exception(f"获取窗口信息失败: {e}")
    
    def capture_window_screenshot(self, window_handle: int) -> Optional[str]:
        """捕获指定窗口的截图"""
        try:
            # 获取窗口矩形
            rect = win32gui.GetWindowRect(window_handle)
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                return None
            
            # 使用PIL的ImageGrab来捕获窗口
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            
            # 智能调整大小
            if self.config.enable_smart_resize:
                screenshot = self._smart_resize_image(screenshot)
            
            # 转换为base64
            buffered = BytesIO()
            screenshot.save(buffered, format="JPEG", quality=self.config.compression_quality)
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return img_base64
            
        except Exception as e:
            print(f"截图失败: {e}")
            return None
    
    def _smart_resize_image(self, image: Image.Image) -> Image.Image:
        """智能调整图像大小"""
        original_width, original_height = image.size
        max_width, max_height = self.config.max_width, self.config.max_height
        
        if original_width <= max_width and original_height <= max_height:
            return image
        
        try:
            # 计算缩放比例
            scale_w = max_width / original_width
            scale_h = max_height / original_height
            scale = min(scale_w, scale_h)
            
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except Exception:
            # 如果智能调整失败，使用简单调整
            return image.resize((max_width, max_height), Image.Resampling.LANCZOS)
    
    def extract_ui_elements(self, window_handle: int) -> List[UIElement]:
        """提取窗口的UI元素结构"""
        elements = []
        
        try:
            # 获取窗口基本信息作为根元素
            window_info = self.get_window_info(window_handle)
            root_element = UIElement(
                element_type="Window",
                text=window_info.title,
                rect=window_info.rect,
                attributes={
                    "class_name": window_info.class_name,
                    "visible": window_info.is_visible,
                    "enabled": window_info.is_enabled,
                    "process_id": window_info.process_id
                },
                children=[]
            )
            elements.append(root_element)
            
            # TODO: 添加更复杂的UI元素提取逻辑
            # 可以使用UI Automation API或其他Windows UI库
            
        except Exception as e:
            print(f"提取UI元素失败: {e}")
        
        return elements
    
    def get_platform_info(self) -> Dict[str, Any]:
        """获取Windows平台特定信息"""
        import platform
        return {
            "platform": "Windows",
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "screen_resolution": self._get_screen_resolution(),
            "dpi_scale": self._get_dpi_scale()
        }
    
    def _get_screen_resolution(self) -> tuple:
        """获取屏幕分辨率"""
        try:
            import tkinter as tk
            root = tk.Tk()
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            root.destroy()
            return (width, height)
        except:
            return (1920, 1080)  # 默认值
    
    def _get_dpi_scale(self) -> float:
        """获取DPI缩放比例"""
        try:
            import ctypes
            # 获取DPI感知
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            dc = user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
            user32.ReleaseDC(0, dc)
            return dpi / 96.0  # 96 DPI是标准
        except:
            return 1.0  # 默认值
    
    def get_foreground_window(self) -> Optional[int]:
        """获取前台窗口"""
        try:
            return win32gui.GetForegroundWindow()
        except:
            return None
    
    def _update_performance_metrics(self, capture_time: float, processing_time: float):
        """更新性能指标 - Windows特定实现"""
        try:
            # 获取CPU使用率
            cpu_percent = self._process.cpu_percent()
            
            # 获取内存使用
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # 转换为MB
            
            # 计算帧率
            fps = 1.0 / self.config.fps if self.config.fps > 0 else 0.0
            
            # 更新指标
            self.metrics.update_metrics(
                cpu=cpu_percent,
                memory=memory_mb,
                fps=fps,
                capture_time=capture_time,
                processing_time=processing_time
            )
            
        except Exception as e:
            # 如果性能监控失败，使用基础实现
            super()._update_performance_metrics(capture_time, processing_time)
            print(f"性能监控更新失败: {e}")

# 便捷类，继承现有WindowStreamManager但添加Windows特定功能
class WindowsStreamManager:
    """Windows特定的流管理器"""
    
    def __init__(self, config: UITarsConfig = None):
        from .ui_tars_core import WindowStreamManager
        self.capture = WindowsWindowCapture(config)
        self.manager = WindowStreamManager(self.capture)
    
    def get_foreground_window(self) -> Optional[int]:
        """获取前台窗口"""
        return self.capture.get_foreground_window()
    
    def __getattr__(self, name):
        """代理其他方法到manager"""
        return getattr(self.manager, name) 