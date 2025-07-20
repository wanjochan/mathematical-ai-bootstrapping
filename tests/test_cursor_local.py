"""本地Cursor IDE控制测试 - 不依赖websocket服务器"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
import logging
import win32gui
import win32con
import win32api
import cv2
import numpy as np
from typing import Optional, List, Dict, Any

from cybercorp_node.utils.vision_model_optimized import UIVisionModelOptimized

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LocalCursorController:
    """本地Cursor IDE控制器 - 直接使用Windows API"""
    
    def __init__(self):
        self.vision_model = UIVisionModelOptimized()
        self.cursor_hwnd = None
        
    def find_cursor_window(self) -> Optional[int]:
        """查找Cursor IDE窗口"""
        logger.info("搜索Cursor IDE窗口...")
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and 'cursor' in title.lower():
                    windows.append((hwnd, title))
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        if not windows:
            logger.error("未找到Cursor IDE窗口")
            return None
        
        # 选择第一个找到的Cursor窗口
        hwnd, title = windows[0]
        self.cursor_hwnd = hwnd
        logger.info(f"找到Cursor窗口: {title} (HWND: {hwnd})")
        return hwnd
    
    def capture_window(self, hwnd: int) -> Optional[np.ndarray]:
        """捕获窗口截图"""
        try:
            import win32ui
            import win32con
            from PIL import Image
            
            # 获取窗口尺寸
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # 获取窗口DC
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            # 创建bitmap
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            # 复制窗口内容
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
            
            # 转换为PIL Image
            bmp_info = save_bitmap.GetInfo()
            bmp_str = save_bitmap.GetBitmapBits(True)
            
            img = Image.frombuffer(
                'RGB',
                (bmp_info['bmWidth'], bmp_info['bmHeight']),
                bmp_str, 'raw', 'BGRX', 0, 1
            )
            
            # 转换为numpy数组
            img_array = np.array(img)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # 清理资源
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            logger.info(f"成功捕获窗口截图: {img_bgr.shape}")
            return img_bgr
            
        except Exception as e:
            logger.error(f"捕获窗口失败: {e}")
            return None
    
    def send_text(self, text: str):
        """发送文本到活动窗口"""
        try:
            # 确保Cursor窗口处于前台
            if self.cursor_hwnd:
                win32gui.SetForegroundWindow(self.cursor_hwnd)
                time.sleep(0.5)
            
            # 逐字符发送文本
            for char in text:
                if char == '\n':
                    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                else:
                    # 发送字符
                    vk_code = ord(char.upper())
                    if char.islower():
                        win32api.keybd_event(vk_code, 0, 0, 0)
                        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                    else:
                        # 大写字母需要Shift
                        win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
                        win32api.keybd_event(vk_code, 0, 0, 0)
                        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                        win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
                
                time.sleep(0.05)  # 小延迟避免输入过快
            
            logger.info(f"成功发送文本: {text[:50]}...")
            
        except Exception as e:
            logger.error(f"发送文本失败: {e}")
    
    def click_position(self, x: int, y: int):
        """点击指定位置"""
        try:
            # 获取窗口位置
            if self.cursor_hwnd:
                left, top, right, bottom = win32gui.GetWindowRect(self.cursor_hwnd)
                # 转换为屏幕坐标
                screen_x = left + x
                screen_y = top + y
                
                # 移动鼠标并点击
                win32api.SetCursorPos((screen_x, screen_y))
                time.sleep(0.2)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
                
                logger.info(f"点击位置: ({x}, {y}) -> 屏幕({screen_x}, {screen_y})")
                
        except Exception as e:
            logger.error(f"点击失败: {e}")
    
    def send_enter(self):
        """发送回车键"""
        try:
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
            win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
            logger.info("发送回车键")
        except Exception as e:
            logger.error(f"发送回车失败: {e}")


async def test_cursor_interaction():
    """测试Cursor IDE交互"""
    print("🚀 本地Cursor IDE交互测试")
    print("=" * 50)
    
    controller = LocalCursorController()
    
    # 步骤1: 查找Cursor窗口
    print("1. 查找Cursor IDE窗口...")
    hwnd = controller.find_cursor_window()
    
    if not hwnd:
        print("❌ 未找到Cursor IDE窗口")
        print("请确保Cursor IDE已经启动")
        return False
    
    print(f"✅ 找到Cursor IDE窗口: {hwnd}")
    
    # 步骤2: 捕获窗口并分析UI
    print("\n2. 分析Cursor IDE界面...")
    screenshot = controller.capture_window(hwnd)
    
    if screenshot is None:
        print("❌ 无法捕获窗口截图")
        return False
    
    print(f"✅ 成功捕获截图: {screenshot.shape}")
    
    # 步骤3: 使用vision模型检测UI元素
    print("\n3. 检测UI元素...")
    elements = controller.vision_model.detect_ui_elements(screenshot)
    
    print(f"检测到 {len(elements)} 个UI元素:")
    input_elements = []
    button_elements = []
    
    for i, elem in enumerate(elements):
        print(f"  {i+1}. {elem.element_type} at {elem.center} (conf: {elem.confidence:.2f})")
        
        if elem.element_type == 'input':
            input_elements.append(elem)
        elif elem.element_type == 'button':
            button_elements.append(elem)
    
    # 保存可视化结果
    vis_image = screenshot.copy()
    for elem in elements:
        x1, y1, x2, y2 = elem.bbox
        color = (0, 255, 0) if elem.clickable else (255, 0, 0)
        cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(vis_image, f"{elem.element_type}", (x1, y1-5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    cv2.imwrite("tests/cursor_local_detection.png", vis_image)
    print("📷 UI检测结果已保存到: tests/cursor_local_detection.png")
    
    # 步骤4: 尝试与Cursor交互
    if input_elements:
        print(f"\n4. 找到 {len(input_elements)} 个输入框，准备发送测试消息...")
        
        # 用户确认
        user_input = input("是否继续发送测试消息到Cursor IDE? (y/n): ")
        if user_input.lower() not in ['y', 'yes']:
            print("用户取消测试")
            return True
        
        # 选择最大的输入框（通常是主要的聊天输入框）
        main_input = max(input_elements, key=lambda x: x.area)
        print(f"选择主输入框: {main_input.center}")
        
        # 点击输入框
        controller.click_position(main_input.center[0], main_input.center[1])
        time.sleep(1)
        
        # 发送测试消息
        test_message = "Hello, this is a test message from cybercorp_node!"
        print(f"发送测试消息: {test_message}")
        controller.send_text(test_message)
        time.sleep(1)
        
        # 尝试按回车发送
        controller.send_enter()
        
        print("✅ 测试消息已发送")
        print("请检查Cursor IDE是否收到消息")
        
        return True
    else:
        print("❌ 未找到输入框，无法发送消息")
        return False


async def main():
    """主函数"""
    print("Cursor IDE本地控制测试")
    print("=" * 50)
    print("注意事项:")
    print("1. 请确保Cursor IDE已经启动")
    print("2. 请确保AI助手聊天界面可见")
    print("3. 此测试将实际向Cursor发送消息")
    print()
    
    try:
        success = await test_cursor_interaction()
        
        if success:
            print("\n🎉 测试成功完成!")
            print("cybercorp_node可以成功控制Cursor IDE")
        else:
            print("\n❌ 测试失败")
            print("请检查Cursor IDE状态和权限设置")
        
        return success
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
        return False
    except Exception as e:
        print(f"\n测试过程出错: {e}")
        return False


if __name__ == "__main__":
    print("准备开始Cursor IDE本地控制测试...")
    print("请确保Cursor IDE已启动并且AI助手面板可见")
    input("按Enter开始测试...")
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)