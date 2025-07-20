"""改进的Cursor IDE控制测试 - 针对实际UI优化"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
import win32gui
import win32con
import win32api
import cv2
import numpy as np
from typing import Optional, List, Dict, Any

from cybercorp_node.utils.vision_model_optimized import UIVisionModelOptimized

logger = logging.getLogger(__name__)


class CursorIDEOptimizedController:
    """针对Cursor IDE优化的控制器"""
    
    def __init__(self):
        self.vision_model = UIVisionModelOptimized()
        self.cursor_hwnd = None
        
    def find_cursor_window(self) -> Optional[int]:
        """查找Cursor IDE窗口"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and 'cursor' in title.lower():
                    windows.append((hwnd, title))
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        if windows:
            hwnd, title = windows[0]
            self.cursor_hwnd = hwnd
            print(f"✅ 找到Cursor IDE: {title}")
            return hwnd
        return None
    
    def capture_window(self, hwnd: int) -> Optional[np.ndarray]:
        """捕获窗口截图"""
        try:
            import win32ui
            from PIL import Image
            
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
            
            bmp_info = save_bitmap.GetInfo()
            bmp_str = save_bitmap.GetBitmapBits(True)
            
            img = Image.frombuffer(
                'RGB',
                (bmp_info['bmWidth'], bmp_info['bmHeight']),
                bmp_str, 'raw', 'BGRX', 0, 1
            )
            
            img_array = np.array(img)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # 清理资源
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            return img_bgr
            
        except Exception as e:
            print(f"❌ 捕获窗口失败: {e}")
            return None
    
    def detect_cursor_chat_elements(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """专门检测Cursor IDE聊天元素"""
        height, width = screenshot.shape[:2]
        
        # 重点分析右侧区域（聊天面板通常在右侧）
        right_panel = screenshot[:, int(width*0.6):]  # 右侧40%区域
        
        print(f"🔍 分析聊天面板区域 (右侧 {right_panel.shape[1]}x{right_panel.shape[0]})")
        
        # 使用标准vision检测
        all_elements = self.vision_model.detect_ui_elements(screenshot)
        
        # 另外，手动寻找Cursor特有的元素
        chat_elements = self.find_cursor_specific_elements(screenshot)
        
        # 合并结果
        result = {
            'standard_elements': all_elements,
            'chat_elements': chat_elements,
            'right_panel_region': (int(width*0.6), 0, width, height)
        }
        
        return result
    
    def find_cursor_specific_elements(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """寻找Cursor IDE特有的聊天元素"""
        height, width = screenshot.shape[:2]
        
        # 重点查找右侧面板的输入区域
        # 基于观察到的UI，聊天输入框通常在右下角
        
        # 定义搜索区域：右侧面板的下半部分
        search_x_start = int(width * 0.6)  # 从60%宽度开始
        search_y_start = int(height * 0.5)  # 从50%高度开始
        
        search_region = screenshot[search_y_start:, search_x_start:]
        
        print(f"🎯 搜索聊天输入区域: {search_region.shape}")
        
        # 在搜索区域内查找潜在的输入框
        gray = cv2.cvtColor(search_region, cv2.COLOR_BGR2GRAY)
        
        # 寻找水平边缘（输入框通常有明显的上下边框）
        edges = cv2.Canny(gray, 30, 100)
        
        # 查找矩形轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        potential_inputs = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # 输入框特征：比较宽，不太高
            if w > 100 and 15 < h < 60 and w/h > 3:
                # 转换回全图坐标
                global_x = x + search_x_start
                global_y = y + search_y_start
                
                # 检查区域内容（输入框通常有较浅的背景）
                roi = search_region[y:y+h, x:x+w]
                if roi.size > 0:
                    mean_brightness = cv2.mean(roi)[0]
                    
                    potential_inputs.append({
                        'bbox': (global_x, global_y, global_x + w, global_y + h),
                        'center': (global_x + w//2, global_y + h//2),
                        'area': w * h,
                        'aspect_ratio': w / h,
                        'brightness': mean_brightness,
                        'confidence': 0.7  # 手动检测的置信度
                    })
        
        # 排序：优先选择面积大、宽高比合适的元素
        potential_inputs.sort(key=lambda x: (x['area'], x['aspect_ratio']), reverse=True)
        
        return {
            'potential_chat_inputs': potential_inputs,
            'search_region': (search_x_start, search_y_start, width, height)
        }
    
    def visualize_detection(self, screenshot: np.ndarray, detection_result: Dict) -> np.ndarray:
        """可视化检测结果"""
        vis_image = screenshot.copy()
        
        # 绘制标准检测元素
        for elem in detection_result['standard_elements']:
            x1, y1, x2, y2 = elem.bbox
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(vis_image, f"{elem.element_type}", (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # 绘制聊天输入候选
        chat_inputs = detection_result['chat_elements'].get('potential_chat_inputs', [])
        for i, inp in enumerate(chat_inputs):
            x1, y1, x2, y2 = inp['bbox']
            color = (0, 0, 255) if i == 0 else (0, 165, 255)  # 第一个用红色，其他用橙色
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 3)
            cv2.putText(vis_image, f"Chat Input {i+1}", (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.circle(vis_image, inp['center'], 5, color, -1)
        
        # 绘制搜索区域
        search_region = detection_result['chat_elements'].get('search_region')
        if search_region:
            x1, y1, x2, y2 = search_region
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), (255, 255, 0), 2)
            cv2.putText(vis_image, "Chat Search Area", (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        return vis_image
    
    def click_chat_input(self, screenshot: np.ndarray, detection_result: Dict) -> bool:
        """点击聊天输入框"""
        chat_inputs = detection_result['chat_elements'].get('potential_chat_inputs', [])
        
        if not chat_inputs:
            print("❌ 未找到聊天输入框")
            return False
        
        # 选择最佳候选（第一个，已按优先级排序）
        best_input = chat_inputs[0]
        center = best_input['center']
        
        print(f"🎯 准备点击聊天输入框: {center}")
        
        try:
            # 获取窗口位置并转换为屏幕坐标
            if self.cursor_hwnd:
                left, top, right, bottom = win32gui.GetWindowRect(self.cursor_hwnd)
                screen_x = left + center[0]
                screen_y = top + center[1]
                
                # 确保Cursor窗口在前台
                win32gui.SetForegroundWindow(self.cursor_hwnd)
                time.sleep(0.5)
                
                # 点击输入框
                win32api.SetCursorPos((screen_x, screen_y))
                time.sleep(0.2)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
                
                print(f"✅ 点击成功: 窗口坐标{center} -> 屏幕坐标({screen_x}, {screen_y})")
                return True
                
        except Exception as e:
            print(f"❌ 点击失败: {e}")
            return False
    
    def send_message_to_cursor(self, message: str) -> bool:
        """发送消息到Cursor IDE"""
        try:
            # 清除现有内容 (Ctrl+A + Delete)
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.2)
            
            win32api.keybd_event(win32con.VK_DELETE, 0, 0, 0)
            win32api.keybd_event(win32con.VK_DELETE, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.2)
            
            # 发送消息文本
            for char in message:
                if char == ' ':
                    win32api.keybd_event(win32con.VK_SPACE, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)
                elif char.isalnum():
                    vk_code = ord(char.upper())
                    if char.isupper():
                        win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
                        win32api.keybd_event(vk_code, 0, 0, 0)
                        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                        win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
                    else:
                        win32api.keybd_event(vk_code, 0, 0, 0)
                        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.05)
            
            # 发送回车
            time.sleep(0.5)
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
            win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            print(f"✅ 消息已发送: {message}")
            return True
            
        except Exception as e:
            print(f"❌ 发送消息失败: {e}")
            return False


def main():
    """主测试函数"""
    print("🚀 Cursor IDE 改进版控制测试")
    print("=" * 60)
    
    controller = CursorIDEOptimizedController()
    
    # 步骤1: 查找Cursor窗口
    print("1. 查找Cursor IDE窗口...")
    hwnd = controller.find_cursor_window()
    if not hwnd:
        print("❌ 未找到Cursor IDE窗口")
        return False
    
    # 步骤2: 捕获截图
    print("\n2. 捕获Cursor IDE截图...")
    screenshot = controller.capture_window(hwnd)
    if screenshot is None:
        return False
    
    print(f"✅ 截图尺寸: {screenshot.shape}")
    
    # 步骤3: 检测聊天元素
    print("\n3. 检测Cursor IDE聊天元素...")
    detection_result = controller.detect_cursor_chat_elements(screenshot)
    
    # 显示检测结果
    standard_count = len(detection_result['standard_elements'])
    chat_inputs = detection_result['chat_elements'].get('potential_chat_inputs', [])
    
    print(f"检测结果:")
    print(f"  - 标准UI元素: {standard_count}")
    print(f"  - 潜在聊天输入框: {len(chat_inputs)}")
    
    for i, inp in enumerate(chat_inputs):
        print(f"    输入框 {i+1}: 位置{inp['center']}, 面积{inp['area']}, 宽高比{inp['aspect_ratio']:.1f}")
    
    # 步骤4: 保存可视化
    print("\n4. 保存检测可视化...")
    vis_image = controller.visualize_detection(screenshot, detection_result)
    cv2.imwrite("tests/cursor_improved_detection.png", vis_image)
    print("📷 检测结果保存到: tests/cursor_improved_detection.png")
    
    # 步骤5: 实际交互测试
    if chat_inputs:
        print(f"\n5. 实际交互测试...")
        print(f"找到 {len(chat_inputs)} 个潜在聊天输入框")
        
        # 模拟用户确认（在实际环境中会有交互）
        proceed = True  # input("是否继续进行实际交互测试? (y/n): ").lower().startswith('y')
        
        if proceed:
            print("🎯 开始与Cursor IDE交互...")
            
            # 点击输入框
            if controller.click_chat_input(screenshot, detection_result):
                time.sleep(1)
                
                # 发送测试消息
                test_message = "Hello from cybercorp_node"
                print(f"📝 发送测试消息: '{test_message}'")
                
                if controller.send_message_to_cursor(test_message):
                    print("🎉 交互测试成功!")
                    print("cybercorp_node已成功向Cursor IDE发送消息")
                    return True
                else:
                    print("❌ 发送消息失败")
                    return False
            else:
                print("❌ 无法点击输入框")
                return False
        else:
            print("用户跳过交互测试")
            return True
    else:
        print(f"\n⚠️ 未找到聊天输入框")
        print(f"建议:")
        print(f"  - 确保Cursor IDE的AI助手面板已打开")
        print(f"  - 检查右侧是否有'New Chat'面板")
        return False


if __name__ == "__main__":
    try:
        success = main()
        if success:
            print(f"\n🎉 测试成功完成!")
            print(f"cybercorp_node可以控制Cursor IDE!")
        else:
            print(f"\n❌ 测试未完全成功")
            print(f"请检查Cursor IDE状态和UI布局")
    except Exception as e:
        print(f"\n💥 测试出错: {e}")
        import traceback
        traceback.print_exc()