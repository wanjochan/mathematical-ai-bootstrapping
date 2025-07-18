"""
UI-TARS 抽象层核心模块
定义平台无关的接口和数据结构，为跨平台支持奠定基础
"""

import abc
import time
import platform
from typing import Dict, Any, Optional, List, Callable, Protocol
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

# 数据结构定义（避免循环导入）
class UITarsConfig(BaseModel):
    fps: float = 1.0  # 帧率，默认1帧/秒
    max_width: int = 1920
    max_height: int = 1080
    compression_quality: int = 85
    enable_smart_resize: bool = True
    target_window: Optional[str] = None  # 目标窗口标题或句柄

@dataclass
class WindowInfo:
    hwnd: int
    title: str
    class_name: str
    rect: tuple  # (left, top, right, bottom)
    is_visible: bool
    is_enabled: bool
    process_id: int

@dataclass
class UIElement:
    element_type: str
    text: str
    rect: tuple
    attributes: Dict[str, Any]
    children: List["UIElement"]

@dataclass
class WindowSnapshot:
    timestamp: datetime
    window_info: WindowInfo
    screenshot_base64: Optional[str]
    ui_elements: List[UIElement]
    frame_size: tuple  # (width, height)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class PlatformType(Enum):
    """支持的平台类型"""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"

class PerformanceMetrics:
    """性能监控指标"""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.cpu_usage_percent = 0.0
        self.memory_usage_mb = 0.0
        self.frame_rate = 0.0
        self.capture_time_ms = 0.0
        self.processing_time_ms = 0.0
        self.last_update = datetime.now()
    
    def update_metrics(self, cpu: float, memory: float, fps: float, 
                      capture_time: float, processing_time: float):
        """更新性能指标"""
        self.cpu_usage_percent = cpu
        self.memory_usage_mb = memory
        self.frame_rate = fps
        self.capture_time_ms = capture_time
        self.processing_time_ms = processing_time
        self.last_update = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_usage_percent": self.cpu_usage_percent,
            "memory_usage_mb": self.memory_usage_mb,
            "frame_rate": self.frame_rate,
            "capture_time_ms": self.capture_time_ms,
            "processing_time_ms": self.processing_time_ms,
            "last_update": self.last_update.isoformat(),
            "meets_prd_requirements": self._meets_prd_requirements()
        }
    
    def _meets_prd_requirements(self) -> Dict[str, bool]:
        """检查是否满足PRD性能要求"""
        return {
            "cpu_under_5_percent": self.cpu_usage_percent < 5.0,
            "memory_under_200mb": self.memory_usage_mb < 200.0,
            "frame_rate_adequate": self.frame_rate >= 0.8,  # 允许略低于1FPS
        }

class WindowCaptureBase(abc.ABC):
    """窗口捕获抽象基类"""
    
    def __init__(self, config: UITarsConfig = None):
        self.config = config or UITarsConfig()
        self.metrics = PerformanceMetrics()
        self._subscribers: List[Callable[[WindowSnapshot], None]] = []
    
    @abc.abstractmethod
    def enumerate_windows(self) -> List[WindowInfo]:
        """枚举所有可见窗口"""
        pass
    
    @abc.abstractmethod
    def find_window_by_title(self, title: str) -> Optional[int]:
        """根据标题查找窗口句柄"""
        pass
    
    @abc.abstractmethod
    def get_window_info(self, window_handle: int) -> WindowInfo:
        """获取窗口详细信息"""
        pass
    
    @abc.abstractmethod
    def capture_window_screenshot(self, window_handle: int) -> Optional[str]:
        """捕获窗口截图，返回base64编码"""
        pass
    
    @abc.abstractmethod
    def extract_ui_elements(self, window_handle: int) -> List[UIElement]:
        """提取窗口UI元素结构"""
        pass
    
    @abc.abstractmethod
    def get_platform_info(self) -> Dict[str, Any]:
        """获取平台特定信息"""
        pass
    
    def add_subscriber(self, callback: Callable[[WindowSnapshot], None]):
        """添加数据流订阅者"""
        self._subscribers.append(callback)
    
    def remove_subscriber(self, callback: Callable[[WindowSnapshot], None]):
        """移除数据流订阅者"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def _notify_subscribers(self, snapshot: WindowSnapshot):
        """通知所有订阅者"""
        for callback in self._subscribers:
            try:
                callback(snapshot)
            except Exception as e:
                print(f"通知订阅者时出错: {e}")
    
    def create_window_snapshot(self, window_handle: int) -> WindowSnapshot:
        """创建窗口快照（通用逻辑）"""
        start_time = time.time()
        
        # 获取窗口信息
        window_info = self.get_window_info(window_handle)
        
        # 截图
        capture_start = time.time()
        screenshot_base64 = self.capture_window_screenshot(window_handle)
        capture_time = (time.time() - capture_start) * 1000
        
        # 提取UI元素
        processing_start = time.time()
        ui_elements = self.extract_ui_elements(window_handle)
        processing_time = (time.time() - processing_start) * 1000
        
        # 计算帧大小
        rect = window_info.rect
        frame_size = (rect[2] - rect[0], rect[3] - rect[1])
        
        # 更新性能指标
        total_time = (time.time() - start_time) * 1000
        self._update_performance_metrics(capture_time, processing_time)
        
        snapshot = WindowSnapshot(
            timestamp=datetime.now(),
            window_info=window_info,
            screenshot_base64=screenshot_base64,
            ui_elements=ui_elements,
            frame_size=frame_size
        )
        
        return snapshot
    
    def _update_performance_metrics(self, capture_time: float, processing_time: float):
        """更新性能指标（子类实现具体的CPU/内存监控）"""
        # 基础实现，子类可以重写
        self.metrics.capture_time_ms = capture_time
        self.metrics.processing_time_ms = processing_time
        self.metrics.frame_rate = 1.0 / self.config.fps if self.config.fps > 0 else 0.0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能监控指标"""
        return self.metrics.to_dict()

class WindowStreamManager:
    """窗口流管理器 - 平台无关的流控制逻辑"""
    
    def __init__(self, capture_backend: WindowCaptureBase):
        self.capture = capture_backend
        self.is_streaming = False
        self.current_window_handle = None
        self.frame_count = 0
        self._stream_thread = None
    
    def start_streaming(self, window_identifier: Optional[str] = None):
        """开始窗口数据流"""
        if self.is_streaming:
            return
        
        self.is_streaming = True
        
        import threading
        def stream_worker():
            interval = 1.0 / self.capture.config.fps
            
            while self.is_streaming:
                try:
                    # 确定目标窗口
                    window_handle = self._resolve_window_handle(window_identifier)
                    if window_handle:
                        snapshot = self.capture.create_window_snapshot(window_handle)
                        self.capture._notify_subscribers(snapshot)
                        self.frame_count += 1
                
                except Exception as e:
                    print(f"流式处理错误: {e}")
                
                time.sleep(interval)
        
        self._stream_thread = threading.Thread(target=stream_worker, daemon=True)
        self._stream_thread.start()
    
    def stop_streaming(self):
        """停止窗口数据流"""
        self.is_streaming = False
        if self._stream_thread:
            self._stream_thread.join(timeout=2.0)
    
    def get_single_snapshot(self, window_identifier: Optional[str] = None) -> WindowSnapshot:
        """获取单次窗口快照"""
        window_handle = self._resolve_window_handle(window_identifier)
        if not window_handle:
            raise ValueError("未找到指定窗口")
        
        return self.capture.create_window_snapshot(window_handle)
    
    def get_window_snapshot(self, window_identifier: Optional[str] = None) -> WindowSnapshot:
        """获取窗口快照（向后兼容方法）"""
        return self.get_single_snapshot(window_identifier)
    
    def _resolve_window_handle(self, window_identifier: Optional[str] = None) -> Optional[int]:
        """解析窗口标识符为窗口句柄"""
        if window_identifier:
            if window_identifier.isdigit():
                return int(window_identifier)
            else:
                return self.capture.find_window_by_title(window_identifier)
        elif self.capture.config.target_window:
            return self.capture.find_window_by_title(self.capture.config.target_window)
        elif self.current_window_handle:
            return self.current_window_handle
        else:
            # 使用前台窗口（平台特定实现）
            return self._get_foreground_window()
    
    def _get_foreground_window(self) -> Optional[int]:
        """获取前台窗口（子类或平台特定实现）"""
        # 这里返回None，具体实现由平台特定的类提供
        return None

def get_platform_type() -> PlatformType:
    """检测当前平台类型"""
    system = platform.system().lower()
    if system == "windows":
        return PlatformType.WINDOWS
    elif system == "darwin":
        return PlatformType.MACOS
    elif system == "linux":
        return PlatformType.LINUX
    else:
        raise NotImplementedError(f"不支持的平台: {system}")

def create_platform_capture(config: UITarsConfig = None) -> WindowCaptureBase:
    """工厂方法：根据平台创建合适的捕获实现"""
    platform_type = get_platform_type()
    
    if platform_type == PlatformType.WINDOWS:
        from .ui_tars_windows import WindowsWindowCapture
        return WindowsWindowCapture(config)
    elif platform_type == PlatformType.MACOS:
        # TODO: 实现macOS支持
        raise NotImplementedError("macOS支持正在开发中")
    elif platform_type == PlatformType.LINUX:
        # TODO: 实现Linux支持
        raise NotImplementedError("Linux支持正在开发中")
    else:
        raise NotImplementedError(f"不支持的平台: {platform_type}")

def create_stream_manager(config: UITarsConfig = None) -> WindowStreamManager:
    """便捷函数：创建完整的流管理器"""
    capture = create_platform_capture(config)
    return WindowStreamManager(capture) 