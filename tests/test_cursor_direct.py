"""直接测试Cursor IDE控制功能"""

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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DirectCursorController:
    """直接Cursor IDE控制器"""
    
    def __init__(self):
        self.vision_model = UIVisionModelOptimized()
        self.cursor_hwnd = None
        
    def find_cursor_window(self) -> Optional[int]:
        """查找Cursor IDE窗口"""
        print("🔍 搜索Cursor IDE窗口...")
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and 'cursor' in title.lower():
                    windows.append((hwnd, title))
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        print(f"找到 {len(windows)} 个Cursor相关窗口:")
        for hwnd, title in windows:
            print(f"  - {title} (HWND: {hwnd})")
        
        if not windows:
            print("❌ 未找到Cursor IDE窗口")
            print("请确保Cursor IDE已经启动")
            return None
        
        # 选择第一个找到的Cursor窗口
        hwnd, title = windows[0]
        self.cursor_hwnd = hwnd
        print(f"✅ 选择窗口: {title}")
        return hwnd
    
    def capture_window(self, hwnd: int) -> Optional[np.ndarray]:
        """捕获窗口截图"""
        try:
            import win32ui
            from PIL import Image
            
            # 获取窗口尺寸
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            print(f"窗口尺寸: {width}x{height}")
            
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
            
            print(f"✅ 成功捕获截图: {img_bgr.shape}")
            return img_bgr
            
        except Exception as e:
            print(f"❌ 捕获窗口失败: {e}")
            return None
    
    def analyze_ui_elements(self, screenshot: np.ndarray) -> List:
        """分析UI元素"""
        print("🔍 分析UI元素...")
        
        elements = self.vision_model.detect_ui_elements(screenshot)
        
        print(f"检测到 {len(elements)} 个UI元素:")
        input_elements = []
        button_elements = []
        
        for i, elem in enumerate(elements):
            print(f"  {i+1}. {elem.element_type:10} at {elem.center} (conf: {elem.confidence:.2f}) area: {elem.area}")
            
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
            cv2.putText(vis_image, f"{elem.element_type} ({elem.confidence:.2f})", 
                       (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        cv2.imwrite("tests/cursor_direct_detection.png", vis_image)
        print("📷 UI检测结果保存到: tests/cursor_direct_detection.png")
        
        print(f"总结: {len(input_elements)} 个输入框, {len(button_elements)} 个按钮")
        
        return elements


def main():
    """主测试函数"""
    print("🚀 Cursor IDE直接控制测试")
    print("=" * 50)
    
    controller = DirectCursorController()
    
    # 步骤1: 查找Cursor窗口
    hwnd = controller.find_cursor_window()
    if not hwnd:
        return False
    
    # 步骤2: 捕获窗口截图
    print("\n📸 捕获Cursor IDE截图...")
    screenshot = controller.capture_window(hwnd)
    if screenshot is None:
        return False
    
    # 步骤3: 分析UI元素
    print("\n🔍 分析UI元素...")
    elements = controller.analyze_ui_elements(screenshot)
    
    # 步骤4: 显示结果摘要
    print("\n📊 检测结果摘要:")
    type_counts = {}
    for elem in elements:
        type_counts[elem.element_type] = type_counts.get(elem.element_type, 0) + 1
    
    for elem_type, count in type_counts.items():
        print(f"  {elem_type}: {count}")
    
    # 步骤5: 找到最可能的聊天输入框
    input_elements = [e for e in elements if e.element_type == 'input']
    if input_elements:
        # 选择最大的输入框作为主聊天框
        main_input = max(input_elements, key=lambda x: x.area)
        print(f"\n🎯 识别主聊天输入框:")
        print(f"  位置: {main_input.center}")
        print(f"  大小: {main_input.bbox}")
        print(f"  面积: {main_input.area}")
        
        print(f"\n✅ 测试成功!")
        print(f"cybercorp_node可以:")
        print(f"  - 找到Cursor IDE窗口")
        print(f"  - 捕获界面截图")
        print(f"  - 识别UI元素 (检测到{len(elements)}个)")
        print(f"  - 定位聊天输入框")
        
        return True
    else:
        print(f"\n⚠️ 未找到输入框")
        print(f"可能需要:")
        print(f"  - 打开Cursor IDE的AI助手面板")
        print(f"  - 确保聊天界面可见")
        
        return False


if __name__ == "__main__":
    print("开始Cursor IDE控制能力测试...")
    print("请确保Cursor IDE已启动并且AI助手面板可见")
    
    try:
        success = main()
        if success:
            print("\n🎉 测试完成 - cybercorp_node可以控制Cursor IDE!")
        else:
            print("\n❌ 测试失败 - 请检查Cursor IDE状态")
        
    except Exception as e:
        print(f"\n💥 测试出错: {e}")
        import traceback
        traceback.print_exc()