"""
基础Computer-Use操作接口
基于UI-TARS窗口信息流，提供Computer-Use技术的核心操作能力

功能：
1. 屏幕识别和元素定位
2. 鼠标操作（点击、拖拽、滚轮）
3. 键盘操作（输入、快捷键、组合键）
4. 基础界面自动化
"""

import time
import base64
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import win32gui
import win32con
import win32api
import win32clipboard
import pyautogui
from PIL import Image, ImageDraw
import io

from .ui_tars import get_stream_instance, WindowSnapshot

# 配置pyautogui
pyautogui.FAILSAFE = True  # 鼠标移到左上角停止
pyautogui.PAUSE = 0.1  # 操作间隔

class ActionType(str, Enum):
    """操作类型枚举"""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    DRAG = "drag"
    SCROLL = "scroll"
    TYPE = "type"
    KEY = "key"
    HOTKEY = "hotkey"
    SCREENSHOT = "screenshot"
    LOCATE = "locate"

class ClickType(str, Enum):
    """点击类型"""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"

class MouseAction(BaseModel):
    """鼠标操作模型"""
    action: ActionType
    x: Optional[int] = None
    y: Optional[int] = None
    button: ClickType = ClickType.LEFT
    clicks: int = 1
    duration: float = 0.1
    
class DragAction(BaseModel):
    """拖拽操作模型"""
    start_x: int
    start_y: int
    end_x: int
    end_y: int
    duration: float = 1.0
    button: ClickType = ClickType.LEFT

class ScrollAction(BaseModel):
    """滚轮操作模型"""
    x: int
    y: int
    direction: str = Field(..., description="up/down/left/right")
    clicks: int = 3

class KeyboardAction(BaseModel):
    """键盘操作模型"""
    action: ActionType
    text: Optional[str] = None
    key: Optional[str] = None
    keys: Optional[List[str]] = None  # 组合键
    interval: float = 0.01

class LocateAction(BaseModel):
    """元素定位模型"""
    window_id: Optional[str] = None
    element_text: Optional[str] = None
    element_class: Optional[str] = None
    confidence: float = 0.8
    region: Optional[Tuple[int, int, int, int]] = None

class ActionResult(BaseModel):
    """操作结果模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: float
    action_type: str

@dataclass
class ComputerUseContext:
    """Computer-Use上下文"""
    last_screenshot: Optional[str] = None
    last_action: Optional[Dict[str, Any]] = None
    active_window: Optional[int] = None
    screen_size: Optional[Tuple[int, int]] = None

class ComputerUseController:
    """Computer-Use控制器"""
    
    def __init__(self):
        self.context = ComputerUseContext()
        self.ui_stream = get_stream_instance()
        self._update_screen_info()
    
    def _update_screen_info(self):
        """更新屏幕信息"""
        try:
            self.context.screen_size = pyautogui.size()
            self.context.active_window = win32gui.GetForegroundWindow()
        except Exception as e:
            print(f"更新屏幕信息失败: {e}")
    
    def _safe_execute(self, action_func, action_type: str) -> ActionResult:
        """安全执行操作"""
        start_time = time.time()
        try:
            result = action_func()
            return ActionResult(
                success=True,
                message="操作成功执行",
                data=result,
                timestamp=start_time,
                action_type=action_type
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"操作失败: {str(e)}",
                data=None,
                timestamp=start_time,
                action_type=action_type
            )
    
    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> Dict[str, Any]:
        """截取屏幕截图"""
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # 转换为base64
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            self.context.last_screenshot = img_base64
            
            return {
                "screenshot_base64": img_base64,
                "size": screenshot.size,
                "region": region
            }
        except Exception as e:
            raise Exception(f"截图失败: {e}")
    
    def click(self, action: MouseAction) -> Dict[str, Any]:
        """执行点击操作"""
        try:
            if action.x is None or action.y is None:
                raise ValueError("点击坐标不能为空")
            
            # 执行点击
            if action.action == ActionType.DOUBLE_CLICK:
                pyautogui.doubleClick(action.x, action.y, duration=action.duration)
            elif action.button == ClickType.RIGHT:
                pyautogui.rightClick(action.x, action.y, duration=action.duration)
            elif action.button == ClickType.MIDDLE:
                pyautogui.middleClick(action.x, action.y, duration=action.duration)
            else:
                pyautogui.click(action.x, action.y, clicks=action.clicks, duration=action.duration)
            
            self.context.last_action = {
                "type": "click",
                "position": (action.x, action.y),
                "button": action.button
            }
            
            return {
                "position": (action.x, action.y),
                "button": action.button,
                "clicks": action.clicks
            }
        except Exception as e:
            raise Exception(f"点击操作失败: {e}")
    
    def drag(self, action: DragAction) -> Dict[str, Any]:
        """执行拖拽操作"""
        try:
            pyautogui.drag(
                action.end_x - action.start_x,
                action.end_y - action.start_y,
                duration=action.duration,
                button=action.button.value
            )
            
            self.context.last_action = {
                "type": "drag",
                "start": (action.start_x, action.start_y),
                "end": (action.end_x, action.end_y)
            }
            
            return {
                "start": (action.start_x, action.start_y),
                "end": (action.end_x, action.end_y),
                "distance": (action.end_x - action.start_x, action.end_y - action.start_y)
            }
        except Exception as e:
            raise Exception(f"拖拽操作失败: {e}")
    
    def scroll(self, action: ScrollAction) -> Dict[str, Any]:
        """执行滚轮操作"""
        try:
            # 先移动到指定位置
            pyautogui.moveTo(action.x, action.y)
            
            # 执行滚轮操作
            if action.direction in ["up", "down"]:
                clicks = action.clicks if action.direction == "up" else -action.clicks
                pyautogui.scroll(clicks, x=action.x, y=action.y)
            else:
                # 水平滚轮（如果支持）
                pyautogui.hscroll(action.clicks if action.direction == "right" else -action.clicks, 
                                x=action.x, y=action.y)
            
            return {
                "position": (action.x, action.y),
                "direction": action.direction,
                "clicks": action.clicks
            }
        except Exception as e:
            raise Exception(f"滚轮操作失败: {e}")
    
    def type_text(self, action: KeyboardAction) -> Dict[str, Any]:
        """输入文本"""
        try:
            if not action.text:
                raise ValueError("输入文本不能为空")
            
            pyautogui.write(action.text, interval=action.interval)
            
            self.context.last_action = {
                "type": "type",
                "text": action.text
            }
            
            return {
                "text": action.text,
                "length": len(action.text)
            }
        except Exception as e:
            raise Exception(f"文本输入失败: {e}")
    
    def press_key(self, action: KeyboardAction) -> Dict[str, Any]:
        """按键操作"""
        try:
            if action.action == ActionType.HOTKEY and action.keys:
                # 组合键
                pyautogui.hotkey(*action.keys)
                return {
                    "keys": action.keys,
                    "type": "hotkey"
                }
            elif action.key:
                # 单个按键
                pyautogui.press(action.key)
                return {
                    "key": action.key,
                    "type": "single_key"
                }
            else:
                raise ValueError("按键参数不正确")
                
        except Exception as e:
            raise Exception(f"按键操作失败: {e}")
    
    def locate_element(self, action: LocateAction) -> Dict[str, Any]:
        """定位元素"""
        try:
            results = []
            
            # 如果指定了窗口，获取窗口快照
            if action.window_id:
                snapshot = self.ui_stream.get_window_snapshot(action.window_id)
                # 这里可以在UI元素中搜索
                for element in snapshot.ui_elements:
                    if action.element_text and action.element_text.lower() in element.text.lower():
                        results.append({
                            "type": "ui_element",
                            "text": element.text,
                            "rect": element.rect,
                            "element_type": element.element_type
                        })
                    if action.element_class and action.element_class in element.element_type:
                        results.append({
                            "type": "ui_element_class",
                            "text": element.text,
                            "rect": element.rect,
                            "element_type": element.element_type
                        })
            
            return {
                "found_elements": results,
                "count": len(results),
                "window_id": action.window_id
            }
            
        except Exception as e:
            raise Exception(f"元素定位失败: {e}")
    
    def get_screen_info(self) -> Dict[str, Any]:
        """获取屏幕信息"""
        self._update_screen_info()
        return {
            "screen_size": self.context.screen_size,
            "active_window": self.context.active_window,
            "mouse_position": pyautogui.position(),
            "fail_safe_enabled": pyautogui.FAILSAFE
        }

# 创建路由器
router = APIRouter(prefix="/computer-use", tags=["Computer-Use"])

# 全局控制器实例
_controller_instance: Optional[ComputerUseController] = None

def get_controller() -> ComputerUseController:
    """获取控制器实例"""
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = ComputerUseController()
    return _controller_instance

@router.get("/info")
async def get_system_info():
    """获取系统信息"""
    controller = get_controller()
    return controller.get_screen_info()

@router.post("/screenshot")
async def take_screenshot(
    x: Optional[int] = Query(None, description="截图区域左上角X坐标"),
    y: Optional[int] = Query(None, description="截图区域左上角Y坐标"),
    width: Optional[int] = Query(None, description="截图区域宽度"),
    height: Optional[int] = Query(None, description="截图区域高度")
):
    """截取屏幕截图"""
    controller = get_controller()
    
    region = None
    if all(param is not None for param in [x, y, width, height]):
        region = (x, y, width, height)
    
    def screenshot_action():
        return controller.take_screenshot(region)
    
    result = controller._safe_execute(screenshot_action, "screenshot")
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return result

@router.post("/click")
async def click(action: MouseAction):
    """执行点击操作"""
    controller = get_controller()
    
    def click_action():
        return controller.click(action)
    
    result = controller._safe_execute(click_action, "click")
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return result

@router.post("/drag")
async def drag(action: DragAction):
    """执行拖拽操作"""
    controller = get_controller()
    
    def drag_action():
        return controller.drag(action)
    
    result = controller._safe_execute(drag_action, "drag")
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return result

@router.post("/scroll")
async def scroll(action: ScrollAction):
    """执行滚轮操作"""
    controller = get_controller()
    
    def scroll_action():
        return controller.scroll(action)
    
    result = controller._safe_execute(scroll_action, "scroll")
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return result

@router.post("/type")
async def type_text(action: KeyboardAction):
    """输入文本"""
    controller = get_controller()
    
    def type_action():
        return controller.type_text(action)
    
    result = controller._safe_execute(type_action, "type")
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return result

@router.post("/key")
async def press_key(action: KeyboardAction):
    """按键操作"""
    controller = get_controller()
    
    def key_action():
        return controller.press_key(action)
    
    result = controller._safe_execute(key_action, "key")
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return result

@router.post("/locate")
async def locate_element(action: LocateAction):
    """定位元素"""
    controller = get_controller()
    
    def locate_action():
        return controller.locate_element(action)
    
    result = controller._safe_execute(locate_action, "locate")
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return result

@router.get("/context")
async def get_context():
    """获取当前Computer-Use上下文"""
    controller = get_controller()
    return {
        "last_action": controller.context.last_action,
        "active_window": controller.context.active_window,
        "screen_size": controller.context.screen_size,
        "has_screenshot": controller.context.last_screenshot is not None
    }

@router.post("/sequence")
async def execute_sequence(actions: List[Dict[str, Any]]):
    """执行一系列操作"""
    controller = get_controller()
    results = []
    
    for i, action_data in enumerate(actions):
        try:
            action_type = action_data.get("type")
            
            if action_type == "click":
                action = MouseAction(**action_data)
                result = controller._safe_execute(lambda: controller.click(action), "click")
            elif action_type == "type":
                action = KeyboardAction(**action_data)
                result = controller._safe_execute(lambda: controller.type_text(action), "type")
            elif action_type == "key":
                action = KeyboardAction(**action_data)
                result = controller._safe_execute(lambda: controller.press_key(action), "key")
            elif action_type == "drag":
                action = DragAction(**action_data)
                result = controller._safe_execute(lambda: controller.drag(action), "drag")
            elif action_type == "scroll":
                action = ScrollAction(**action_data)
                result = controller._safe_execute(lambda: controller.scroll(action), "scroll")
            elif action_type == "wait":
                wait_time = action_data.get("duration", 1.0)
                time.sleep(wait_time)
                result = ActionResult(
                    success=True,
                    message=f"等待 {wait_time} 秒",
                    timestamp=time.time(),
                    action_type="wait"
                )
            else:
                result = ActionResult(
                    success=False,
                    message=f"未知操作类型: {action_type}",
                    timestamp=time.time(),
                    action_type="unknown"
                )
            
            results.append({
                "step": i + 1,
                "action": action_data,
                "result": result
            })
            
            # 如果某个步骤失败，根据配置决定是否继续
            if not result.success and action_data.get("critical", True):
                break
                
        except Exception as e:
            results.append({
                "step": i + 1,
                "action": action_data,
                "result": ActionResult(
                    success=False,
                    message=f"步骤执行异常: {str(e)}",
                    timestamp=time.time(),
                    action_type="error"
                )
            })
            break
    
    return {
        "total_steps": len(actions),
        "completed_steps": len(results),
        "success": all(r["result"].success for r in results),
        "results": results
    }

@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        controller = get_controller()
        screen_info = controller.get_screen_info()
        
        return {
            "status": "ok",
            "component": "Computer-Use",
            "version": "1.0.0",
            "features": [
                "屏幕截图",
                "鼠标操作",
                "键盘操作", 
                "拖拽操作",
                "滚轮操作",
                "元素定位",
                "操作序列"
            ],
            "system_info": screen_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Computer-Use组件异常: {e}") 