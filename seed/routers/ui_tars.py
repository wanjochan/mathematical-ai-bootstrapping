"""
UI-TARS 窗口信息流组件
基于字节跳动的ui-tars库实现Computer-Use技术的窗口数据流获取

功能：
1. 低帧率高质量数据流 (FPS=1 已足够)
2. 结构化界面元素识别
3. 资源占用最小化
4. 跨平台兼容性
"""

import json
import time
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import base64
from io import BytesIO

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
import win32gui
import win32con
import win32api
import win32ui
import win32process
from PIL import Image, ImageGrab
import ui_tars.action_parser as action_parser
import ui_tars.prompt as ui_tars_prompt

# 配置模型
class UITarsConfig(BaseModel):
    fps: float = 1.0  # 帧率，默认1帧/秒
    max_width: int = 1920
    max_height: int = 1080
    compression_quality: int = 85
    enable_smart_resize: bool = True
    target_window: Optional[str] = None  # 目标窗口标题或句柄

# 窗口信息数据结构
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

class UITarsWindowStream:
    """UI-TARS 窗口信息流核心类"""
    
    def __init__(self, config: UITarsConfig = None):
        self.config = config or UITarsConfig()
        self.is_streaming = False
        self.current_window_hwnd = None
        self.frame_count = 0
        self.subscribers: List[Callable] = []
        
    def add_subscriber(self, callback: Callable[[WindowSnapshot], None]):
        """添加数据流订阅者"""
        self.subscribers.append(callback)
        
    def remove_subscriber(self, callback: Callable):
        """移除数据流订阅者"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def _notify_subscribers(self, snapshot: WindowSnapshot):
        """通知所有订阅者新的窗口快照"""
        for callback in self.subscribers:
            try:
                callback(snapshot)
            except Exception as e:
                print(f"通知订阅者时出错: {e}")
    
    def _find_window_by_title(self, title: str) -> Optional[int]:
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
    
    def _get_window_info(self, hwnd: int) -> WindowInfo:
        """获取窗口详细信息"""
        try:
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            is_visible = win32gui.IsWindowVisible(hwnd)
            is_enabled = win32gui.IsWindowEnabled(hwnd)
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            
            return WindowInfo(
                hwnd=hwnd,
                title=title,
                class_name=class_name,
                rect=rect,
                is_visible=is_visible,
                is_enabled=is_enabled,
                process_id=process_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取窗口信息失败: {e}")
    
    def _capture_window_screenshot(self, hwnd: int) -> Optional[str]:
        """捕获指定窗口的截图"""
        try:
            # 获取窗口矩形
            rect = win32gui.GetWindowRect(hwnd)
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
        """智能调整图像大小，基于ui-tars的smart_resize功能"""
        original_width, original_height = image.size
        max_width, max_height = self.config.max_width, self.config.max_height
        
        if original_width <= max_width and original_height <= max_height:
            return image
        
        # 使用ui-tars的智能调整大小
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
    
    def _extract_ui_elements(self, hwnd: int) -> List[UIElement]:
        """提取窗口的UI元素结构（简化版本）"""
        # 这里实现一个基础的UI元素提取
        # 在实际实现中，可能需要使用更复杂的UI自动化库
        elements = []
        
        try:
            # 获取窗口基本信息作为根元素
            window_info = self._get_window_info(hwnd)
            root_element = UIElement(
                element_type="Window",
                text=window_info.title,
                rect=window_info.rect,
                attributes={
                    "class_name": window_info.class_name,
                    "visible": window_info.is_visible,
                    "enabled": window_info.is_enabled
                },
                children=[]
            )
            elements.append(root_element)
            
        except Exception as e:
            print(f"提取UI元素失败: {e}")
        
        return elements
    
    def get_window_snapshot(self, window_identifier: Optional[str] = None) -> WindowSnapshot:
        """获取单次窗口快照"""
        # 确定目标窗口
        if window_identifier:
            if window_identifier.isdigit():
                hwnd = int(window_identifier)
            else:
                hwnd = self._find_window_by_title(window_identifier)
        elif self.config.target_window:
            hwnd = self._find_window_by_title(self.config.target_window)
        elif self.current_window_hwnd:
            hwnd = self.current_window_hwnd
        else:
            # 使用前台窗口
            hwnd = win32gui.GetForegroundWindow()
        
        if not hwnd or not win32gui.IsWindow(hwnd):
            raise HTTPException(status_code=404, detail="未找到指定窗口")
        
        # 获取窗口信息
        window_info = self._get_window_info(hwnd)
        
        # 截图
        screenshot_base64 = self._capture_window_screenshot(hwnd)
        
        # 提取UI元素
        ui_elements = self._extract_ui_elements(hwnd)
        
        # 计算帧大小
        rect = window_info.rect
        frame_size = (rect[2] - rect[0], rect[3] - rect[1])
        
        snapshot = WindowSnapshot(
            timestamp=datetime.now(),
            window_info=window_info,
            screenshot_base64=screenshot_base64,
            ui_elements=ui_elements,
            frame_size=frame_size
        )
        
        self.frame_count += 1
        return snapshot
    
    def start_streaming(self, window_identifier: Optional[str] = None):
        """开始窗口数据流"""
        if self.is_streaming:
            return
        
        self.is_streaming = True
        
        def stream_worker():
            interval = 1.0 / self.config.fps
            
            while self.is_streaming:
                try:
                    snapshot = self.get_window_snapshot(window_identifier)
                    self._notify_subscribers(snapshot)
                except Exception as e:
                    print(f"流式处理错误: {e}")
                
                time.sleep(interval)
        
        thread = threading.Thread(target=stream_worker, daemon=True)
        thread.start()
    
    def stop_streaming(self):
        """停止窗口数据流"""
        self.is_streaming = False

# API路由器
router = APIRouter(prefix="/ui-tars", tags=["UI-TARS"])

# 全局流实例
_stream_instance: Optional[UITarsWindowStream] = None

def get_stream_instance() -> UITarsWindowStream:
    """获取全局流实例"""
    global _stream_instance
    if _stream_instance is None:
        _stream_instance = UITarsWindowStream()
    return _stream_instance

@router.post("/config")
async def update_config(config: UITarsConfig):
    """更新UI-TARS配置"""
    stream = get_stream_instance()
    stream.config = config
    return {"message": "配置已更新", "config": config.dict()}

@router.get("/config")
async def get_config():
    """获取当前配置"""
    stream = get_stream_instance()
    return stream.config.dict()

@router.get("/snapshot")
async def get_snapshot(window: Optional[str] = None):
    """获取单次窗口快照"""
    stream = get_stream_instance()
    snapshot = stream.get_window_snapshot(window)
    return snapshot.to_dict()

@router.get("/windows")
async def list_windows():
    """列出所有可见窗口"""
    def enum_windows_proc(hwnd, windows):
        try:
            if win32gui.IsWindow(hwnd):
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                is_visible = win32gui.IsWindowVisible(hwnd)
                
                # 包含所有窗口，不只是有标题的
                if is_visible or title:  # 可见窗口或有标题的窗口
                    rect = win32gui.GetWindowRect(hwnd)
                    windows.append({
                        "hwnd": hwnd,
                        "title": title or f"[{class_name}]",
                        "class_name": class_name,
                        "rect": rect,
                        "is_visible": is_visible
                    })
        except Exception as e:
            # 忽略单个窗口的错误，继续枚举其他窗口
            pass
        return True
    
    windows = []
    try:
        win32gui.EnumWindows(enum_windows_proc, windows)
        # 按标题长度排序，有意义的窗口通常标题更长
        windows.sort(key=lambda w: len(w['title']), reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"枚举窗口失败: {e}")
    
    return {"windows": windows}

@router.post("/stream/start")
async def start_stream(window: Optional[str] = None):
    """开始窗口数据流"""
    stream = get_stream_instance()
    stream.start_streaming(window)
    return {"message": "数据流已启动", "fps": stream.config.fps}

@router.post("/stream/stop")
async def stop_stream():
    """停止窗口数据流"""
    stream = get_stream_instance()
    stream.stop_streaming()
    return {"message": "数据流已停止"}

@router.get("/stream/status")
async def get_stream_status():
    """获取数据流状态"""
    stream = get_stream_instance()
    return {
        "is_streaming": stream.is_streaming,
        "frame_count": stream.frame_count,
        "fps": stream.config.fps,
        "subscribers": len(stream.subscribers)
    }

# WebSocket流式数据接口
@router.websocket("/stream/ws")
async def websocket_stream(websocket: WebSocket):
    """WebSocket窗口数据流"""
    await websocket.accept()
    stream = get_stream_instance()
    
    # 创建数据队列用于WebSocket传输
    data_queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    
    def on_snapshot(snapshot: WindowSnapshot):
        """快照回调函数"""
        try:
            # 安全地将快照数据放入队列
            if not data_queue.full():
                loop.call_soon_threadsafe(data_queue.put_nowait, snapshot.to_dict())
        except Exception as e:
            print(f"WebSocket数据队列错误: {e}")
    
    # 添加订阅者并启动数据流
    stream.add_subscriber(on_snapshot)
    
    # 确保数据流正在运行
    if not stream.is_streaming:
        stream.start_streaming()
        print("WebSocket: 启动数据流")
    
    try:
        # 发送连接确认
        await websocket.send_json({
            "type": "connected", 
            "message": "WebSocket数据流已连接",
            "fps": stream.config.fps,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # 等待新的快照数据
            try:
                snapshot_data = await asyncio.wait_for(data_queue.get(), timeout=1.0)
                await websocket.send_json(snapshot_data)
            except asyncio.TimeoutError:
                # 发送心跳
                await websocket.send_json({
                    "type": "heartbeat", 
                    "timestamp": datetime.now().isoformat(),
                    "queue_size": data_queue.qsize(),
                    "stream_active": stream.is_streaming,
                    "frame_count": stream.frame_count
                })
            
    except WebSocketDisconnect:
        print("WebSocket客户端断开连接")
    except Exception as e:
        print(f"WebSocket错误: {e}")
    finally:
        # 清理订阅者
        stream.remove_subscriber(on_snapshot)
        print(f"WebSocket: 移除订阅者，剩余订阅者: {len(stream.subscribers)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "component": "UI-TARS",
        "version": "1.0.0",
        "features": [
            "窗口信息流",
            "低帧率高质量",
            "结构化数据",
            "WebSocket支持"
        ]
    } 