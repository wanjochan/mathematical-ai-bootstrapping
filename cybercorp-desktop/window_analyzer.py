#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窗口分析模块
负责分析窗口的结构化数据，获取UI元素信息
"""

import win32gui
import win32ui
import win32con
import win32api
from PIL import Image, ImageDraw, ImageFont
import os
import time
from typing import List, Dict, Optional
from window_manager import WindowManager
from logger import analyzer_logger

try:
    from uia_analyzer import UIAAnalyzer
    UIA_AVAILABLE = True
except Exception as e:
    analyzer_logger.warning(f"UIA分析器不可用: {str(e)}")
    UIA_AVAILABLE = False


class WindowAnalyzer:
    def __init__(self):
        self.window_manager = WindowManager()
        self.screenshots_dir = "screenshots"
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
        
        # 初始化UIA分析器
        self.uia_analyzer = None
        self.uia_initialization_attempted = False
        self.uia_failure_reason = None
        
        if UIA_AVAILABLE:
            self._initialize_uia_analyzer()
        else:
            analyzer_logger.warning("UIA模块不可用，将使用传统分析方法")
            self.uia_failure_reason = "UIA模块导入失败"
    
    def _initialize_uia_analyzer(self):
        """安全初始化UIA分析器"""
        try:
            analyzer_logger.info("开始初始化UIA分析器...")
            self.uia_analyzer = UIAAnalyzer()
            
            # 验证UIA分析器是否真正可用
            if self.uia_analyzer.uia is not None:
                analyzer_logger.info(f"UIA分析器初始化成功 - 方法: {self.uia_analyzer.initialization_method}")
                self.uia_initialization_attempted = True
            else:
                analyzer_logger.warning("UIA分析器初始化失败 - UIA对象为None")
                self.uia_analyzer = None
                self.uia_failure_reason = "UIA对象初始化失败"
                self.uia_initialization_attempted = True
                
        except Exception as e:
            analyzer_logger.error(f"UIA分析器初始化异常: {str(e)}")
            self.uia_analyzer = None
            self.uia_failure_reason = str(e)
            self.uia_initialization_attempted = True
    
    def analyze_window(self, hwnd: int, use_uia: bool = True) -> Dict:
        """分析窗口结构 - 增强版本，包含智能回退机制"""
        try:
            # 获取基本窗口信息
            window_info = self.window_manager.get_window_info(hwnd)
            analyzer_logger.info(f"开始分析窗口: {window_info.get('title', 'Unknown')} (HWND: {hwnd})")
            
            # 记录分析策略选择过程
            analysis_strategy = self._determine_analysis_strategy(use_uia, hwnd)
            analyzer_logger.info(f"选择的分析策略: {analysis_strategy}")
            
            # 根据策略执行分析
            if analysis_strategy == "UIA_Primary":
                return self._analyze_with_uia_enhanced(hwnd, window_info)
            elif analysis_strategy == "UIA_Retry":
                return self._analyze_with_uia_retry(hwnd, window_info)
            else:  # Traditional_Fallback
                return self._analyze_traditional_enhanced(hwnd, window_info)
            
        except Exception as e:
            analyzer_logger.exception(f"窗口分析完全失败: {str(e)}")
            # 最后的安全网 - 返回基本信息
            return self._create_minimal_analysis_result(hwnd, str(e))
    
    def _determine_analysis_strategy(self, use_uia: bool, hwnd: int) -> str:
        """确定分析策略"""
        if not use_uia:
            analyzer_logger.info("用户禁用UIA，使用传统方法")
            return "Traditional_Fallback"
        
        if not self.uia_initialization_attempted:
            analyzer_logger.info("UIA未尝试初始化，重新初始化")
            self._initialize_uia_analyzer()
        
        if self.uia_analyzer and self.uia_analyzer.uia:
            analyzer_logger.info("UIA可用，使用UIA主要策略")
            return "UIA_Primary"
        elif self.uia_failure_reason:
            analyzer_logger.warning(f"UIA不可用 ({self.uia_failure_reason})，但尝试重试策略")
            return "UIA_Retry"
        else:
            analyzer_logger.info("UIA不可用，使用传统回退策略")
            return "Traditional_Fallback"
    
    def _analyze_with_uia_enhanced(self, hwnd: int, window_info: Dict) -> Dict:
        """增强的UIA分析，包含错误恢复"""
        try:
            analyzer_logger.info("执行UIA主要分析策略")
            return self._analyze_with_uia(hwnd, window_info)
        except Exception as e:
            analyzer_logger.warning(f"UIA主要策略失败: {str(e)}，回退到传统方法")
            return self._analyze_traditional_enhanced(hwnd, window_info, uia_failure=str(e))
    
    def _analyze_with_uia_retry(self, hwnd: int, window_info: Dict) -> Dict:
        """UIA重试策略"""
        try:
            analyzer_logger.info("执行UIA重试策略")
            # 重新初始化UIA分析器
            self._initialize_uia_analyzer()
            
            if self.uia_analyzer and self.uia_analyzer.uia:
                analyzer_logger.info("UIA重新初始化成功，尝试分析")
                return self._analyze_with_uia(hwnd, window_info)
            else:
                analyzer_logger.warning("UIA重新初始化失败，使用传统方法")
                return self._analyze_traditional_enhanced(hwnd, window_info, uia_failure="UIA重新初始化失败")
                
        except Exception as e:
            analyzer_logger.warning(f"UIA重试策略失败: {str(e)}，回退到传统方法")
            return self._analyze_traditional_enhanced(hwnd, window_info, uia_failure=str(e))
    
    def _analyze_traditional_enhanced(self, hwnd: int, window_info: Dict, uia_failure: str = None) -> Dict:
        """增强的传统分析方法"""
        try:
            analyzer_logger.info("执行增强传统分析策略")
            result = self._analyze_traditional(hwnd, window_info)
            
            # 添加UIA失败信息
            if uia_failure:
                result['uia_failure_reason'] = uia_failure
                result['analysis_method'] = 'Traditional_Fallback'
            
            # 添加诊断信息
            result['diagnostic_info'] = {
                'uia_available': UIA_AVAILABLE,
                'uia_initialization_attempted': self.uia_initialization_attempted,
                'uia_failure_reason': self.uia_failure_reason,
                'fallback_used': True
            }
            
            return result
            
        except Exception as e:
            analyzer_logger.error(f"传统分析方法也失败: {str(e)}")
            return self._create_minimal_analysis_result(hwnd, f"所有分析方法失败: {str(e)}")
    
    def _create_minimal_analysis_result(self, hwnd: int, error_message: str) -> Dict:
        """创建最小分析结果作为最后的安全网"""
        try:
            # 尝试获取基本窗口信息
            basic_info = {
                'hwnd': hwnd,
                'title': win32gui.GetWindowText(hwnd),
                'class_name': win32gui.GetClassName(hwnd),
                'rect': win32gui.GetWindowRect(hwnd),
                'visible': win32gui.IsWindowVisible(hwnd),
                'enabled': win32gui.IsWindowEnabled(hwnd)
            }
        except Exception:
            basic_info = {'hwnd': hwnd, 'error': 'Unable to get basic window info'}
        
        return {
            'analysis_method': 'Minimal_Fallback',
            'window_info': basic_info,
            'elements': [],
            'error': error_message,
            'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'diagnostic_info': {
                'uia_available': UIA_AVAILABLE,
                'uia_initialization_attempted': self.uia_initialization_attempted,
                'uia_failure_reason': self.uia_failure_reason,
                'critical_failure': True
            }
        }
    
    def _analyze_with_uia(self, hwnd: int, window_info: Dict) -> Dict:
        """使用UIA进行详细分析"""
        try:
            # UIA详细分析
            uia_result = self.uia_analyzer.analyze_window_detailed(hwnd)
            
            # 截取窗口截图
            screenshot_path = self.capture_window_screenshot(hwnd)
            
            # 从UIA结果提取简化的元素列表用于标签截图
            simplified_elements = self._extract_elements_for_labeling(uia_result)
            
            # 创建带标签的截图
            labeled_screenshot_path = None
            if screenshot_path and simplified_elements:
                labeled_screenshot_path = self.create_labeled_screenshot_advanced(
                    screenshot_path, simplified_elements, window_info, uia_result
                )
            
            # 合并结果
            result = {
                'analysis_method': 'UIA_Advanced',
                'window_info': window_info,
                'uia_analysis': uia_result,
                'elements': simplified_elements,
                'screenshot_path': screenshot_path,
                'labeled_screenshot_path': labeled_screenshot_path,
                'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'summary': self._generate_analysis_summary(uia_result)
            }
            
            return result
            
        except Exception as e:
            analyzer_logger.warning(f"UIA分析失败，回退到传统方法: {str(e)}")
            return self._analyze_traditional(hwnd, window_info)
    
    def _analyze_traditional(self, hwnd: int, window_info: Dict) -> Dict:
        """使用传统方法分析（向后兼容）"""
        try:
            # 获取子窗口/控件
            child_windows = self.window_manager.get_child_windows(hwnd)
            
            # 截取窗口截图
            screenshot_path = self.capture_window_screenshot(hwnd)
            
            # 分析UI元素
            ui_elements = self.analyze_ui_elements(hwnd, child_windows)
            
            # 创建带标签的截图
            labeled_screenshot_path = None
            if screenshot_path:
                labeled_screenshot_path = self.create_labeled_screenshot(
                    screenshot_path, ui_elements, window_info
                )
            
            return {
                'analysis_method': 'Traditional',
                'window_info': window_info,
                'elements': ui_elements,
                'screenshot_path': screenshot_path,
                'labeled_screenshot_path': labeled_screenshot_path,
                'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            raise Exception(f"传统分析方法失败: {str(e)}")
    
    def capture_window_screenshot(self, hwnd: int) -> Optional[str]:
        """截取窗口截图"""
        try:
            analyzer_logger.info(f"开始截取窗口 {hwnd} 的截图")
            
            # 获取窗口矩形
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            analyzer_logger.debug(f"窗口大小: {width}x{height}")
            
            if width <= 0 or height <= 0:
                analyzer_logger.warning(f"窗口大小无效: {width}x{height}")
                return None
            
            # 方法1: 使用 PrintWindow (需要从user32.dll导入)
            try:
                import ctypes
                from ctypes import windll
                
                # 创建设备上下文
                hwndDC = win32gui.GetWindowDC(hwnd)
                mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                saveDC = mfcDC.CreateCompatibleDC()
                
                # 创建位图对象
                saveBitMap = win32ui.CreateBitmap()
                saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
                saveDC.SelectObject(saveBitMap)
                
                # 使用ctypes调用PrintWindow
                result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
                
                if result == 0:
                    analyzer_logger.warning("PrintWindow失败，尝试使用BitBlt")
                    # PrintWindow失败，尝试使用BitBlt
                    saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
                else:
                    analyzer_logger.debug("PrintWindow截图成功")
                
                # 保存截图
                bmpstr = saveBitMap.GetBitmapBits(True)
                img = Image.frombuffer('RGB', (width, height), bmpstr, 'raw', 'BGRX', 0, 1)
                
                timestamp = int(time.time())
                filename = f"window_{hwnd}_{timestamp}.png"
                filepath = os.path.join(self.screenshots_dir, filename)
                img.save(filepath)
                
                analyzer_logger.info(f"截图保存至: {filepath}")
                
                # 清理资源
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwndDC)
                
                return filepath
                
            except Exception as e:
                analyzer_logger.error(f"PrintWindow方法截图失败: {str(e)}")
                
                # 方法2: 使用屏幕截图的方式
                try:
                    analyzer_logger.info("尝试使用屏幕截图方式")
                    
                    import pyautogui
                    
                    # 获取窗口位置
                    left, top, right, bottom = rect
                    
                    # 截取屏幕区域
                    screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    timestamp = int(time.time())
                    filename = f"window_{hwnd}_{timestamp}.png"
                    filepath = os.path.join(self.screenshots_dir, filename)
                    screenshot.save(filepath)
                    
                    analyzer_logger.info(f"屏幕截图保存至: {filepath}")
                    return filepath
                    
                except Exception as e2:
                    analyzer_logger.error(f"屏幕截图方法也失败: {str(e2)}")
                    return None
            
        except Exception as e:
            analyzer_logger.exception(f"截图完全失败: {str(e)}")
            return None
    
    def analyze_ui_elements(self, parent_hwnd: int, child_windows: List[Dict]) -> List[Dict]:
        """分析UI元素"""
        elements = []
        
        # 获取父窗口位置作为偏移基准
        parent_rect = win32gui.GetWindowRect(parent_hwnd)
        parent_x, parent_y = parent_rect[0], parent_rect[1]
        
        for child in child_windows:
            try:
                element = self.analyze_single_element(child, parent_x, parent_y)
                if element:
                    elements.append(element)
            except Exception as e:
                print(f"分析元素失败: {str(e)}")
                continue
        
        return elements
    
    def analyze_single_element(self, window_info: Dict, parent_x: int, parent_y: int) -> Optional[Dict]:
        """分析单个UI元素"""
        try:
            hwnd = window_info['hwnd']
            rect = window_info['rect']
            
            # 计算相对于父窗口的位置
            x = rect[0] - parent_x
            y = rect[1] - parent_y
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            # 跳过太小的元素
            if width < 5 or height < 5:
                return None
            
            # 获取元素文本
            text = win32gui.GetWindowText(hwnd)
            class_name = window_info['class_name']
            
            # 判断元素类型
            element_type = self.determine_element_type(class_name, text)
            
            # 判断是否可点击
            clickable = self.is_clickable_element(class_name, hwnd)
            
            # 判断是否可见
            visible = win32gui.IsWindowVisible(hwnd)
            
            # 获取元素状态
            enabled = win32gui.IsWindowEnabled(hwnd)
            
            element = {
                'hwnd': hwnd,
                'type': element_type,
                'text': text if text else '',
                'class_name': class_name,
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'visible': visible,
                'enabled': enabled,
                'clickable': clickable
            }
            
            return element
            
        except Exception as e:
            print(f"分析单个元素失败: {str(e)}")
            return None
    
    def determine_element_type(self, class_name: str, text: str) -> str:
        """判断元素类型"""
        class_name_lower = class_name.lower()
        
        # 常见控件类型映射
        if 'button' in class_name_lower:
            return 'Button'
        elif 'edit' in class_name_lower:
            return 'TextBox'
        elif 'static' in class_name_lower:
            return 'Label'
        elif 'listbox' in class_name_lower:
            return 'ListBox'
        elif 'combobox' in class_name_lower:
            return 'ComboBox'
        elif 'scrollbar' in class_name_lower:
            return 'ScrollBar'
        elif 'menu' in class_name_lower:
            return 'Menu'
        elif 'toolbar' in class_name_lower:
            return 'ToolBar'
        elif 'status' in class_name_lower:
            return 'StatusBar'
        elif 'tree' in class_name_lower:
            return 'TreeView'
        elif 'list' in class_name_lower:
            return 'ListView'
        elif 'tab' in class_name_lower:
            return 'TabControl'
        elif 'check' in class_name_lower:
            return 'CheckBox'
        elif 'radio' in class_name_lower:
            return 'RadioButton'
        elif 'progress' in class_name_lower:
            return 'ProgressBar'
        elif 'slider' in class_name_lower:
            return 'Slider'
        else:
            return 'Unknown'
    
    def is_clickable_element(self, class_name: str, hwnd: int) -> bool:
        """判断元素是否可点击"""
        try:
            class_name_lower = class_name.lower()
            
            # 常见可点击控件
            clickable_classes = [
                'button', 'combobox', 'listbox', 'check', 'radio',
                'menu', 'toolbar', 'tree', 'list'
            ]
            
            for clickable_class in clickable_classes:
                if clickable_class in class_name_lower:
                    return True
            
            # 检查窗口样式
            try:
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                if style & win32con.WS_TABSTOP:  # 可以获得焦点的控件通常可点击
                    return True
            except Exception:
                pass
            
            return False
            
        except Exception:
            return False
    
    def create_labeled_screenshot(self, screenshot_path: str, elements: List[Dict], 
                                 window_info: Dict) -> Optional[str]:
        """创建带标签的截图"""
        try:
            if not os.path.exists(screenshot_path):
                return None
            
            # 打开原始截图
            img = Image.open(screenshot_path)
            draw = ImageDraw.Draw(img)
            
            # 尝试加载字体
            try:
                font = ImageFont.truetype("arial.ttf", 12)
            except Exception:
                font = ImageFont.load_default()
            
            # 为每个元素绘制边框和标签
            for i, element in enumerate(elements, 1):
                x, y = element['x'], element['y']
                width, height = element['width'], element['height']
                
                # 确保坐标在图片范围内
                if x < 0 or y < 0 or x + width > img.width or y + height > img.height:
                    continue
                
                # 根据元素类型选择颜色
                color = self.get_element_color(element['type'])
                
                # 绘制边框
                draw.rectangle([x, y, x + width, y + height], outline=color, width=2)
                
                # 绘制标签
                label = f"{i}:{element['type']}"
                if element['text']:
                    label += f"({element['text'][:10]})"
                
                # 绘制标签背景
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                label_x = max(0, min(x, img.width - text_width))
                label_y = max(0, y - text_height - 2)
                
                draw.rectangle([label_x, label_y, label_x + text_width, label_y + text_height], 
                             fill=color)
                draw.text((label_x, label_y), label, fill='white', font=font)
            
            # 保存带标签的截图
            timestamp = int(time.time())
            labeled_filename = f"labeled_window_{window_info['hwnd']}_{timestamp}.png"
            labeled_filepath = os.path.join(self.screenshots_dir, labeled_filename)
            img.save(labeled_filepath)
            
            return labeled_filepath
            
        except Exception as e:
            print(f"创建标签截图失败: {str(e)}")
            return None
    
    def get_element_color(self, element_type: str) -> str:
        """根据元素类型获取颜色"""
        color_map = {
            'Button': 'red',
            'TextBox': 'blue',
            'Label': 'green',
            'ListBox': 'orange',
            'ComboBox': 'purple',
            'CheckBox': 'cyan',
            'RadioButton': 'magenta',
            'Menu': 'yellow',
            'ToolBar': 'brown',
            'StatusBar': 'pink',
            'TreeView': 'darkgreen',
            'ListView': 'darkorange',
            'TabControl': 'darkblue',
            'ProgressBar': 'darkred',
            'ScrollBar': 'gray',
            'Slider': 'lightblue'
        }
        
        return color_map.get(element_type, 'black')
    
    def _extract_elements_for_labeling(self, uia_result: Dict) -> List[Dict]:
        """从UIA结果提取元素用于标签截图"""
        elements = []
        
        try:
            interactive_elements = uia_result.get('interactive_elements', [])
            
            for i, elem in enumerate(interactive_elements):
                bounds = elem.get('bounds', {})
                if bounds.get('width', 0) > 5 and bounds.get('height', 0) > 5:
                    element = {
                        'type': elem.get('type', 'Unknown'),
                        'text': elem.get('text', '') or elem.get('name', ''),
                        'x': bounds.get('x', 0),
                        'y': bounds.get('y', 0),
                        'width': bounds.get('width', 0),
                        'height': bounds.get('height', 0),
                        'visible': True,
                        'clickable': True,
                        'automation_id': elem.get('automation_id', ''),
                        'patterns': elem.get('patterns', [])
                    }
                    elements.append(element)
            
            # 也添加一些文本元素
            text_elements = uia_result.get('text_content', [])
            for elem in text_elements[:20]:  # 限制数量
                if elem.get('is_visible') and elem.get('text'):
                    bounds = elem.get('bounds', {})
                    if bounds.get('width', 0) > 10 and bounds.get('height', 0) > 5:
                        element = {
                            'type': 'Text',
                            'text': elem.get('text', '')[:30],  # 限制文本长度
                            'x': bounds.get('x', 0),
                            'y': bounds.get('y', 0),
                            'width': bounds.get('width', 0),
                            'height': bounds.get('height', 0),
                            'visible': True,
                            'clickable': False
                        }
                        elements.append(element)
            
            return elements
            
        except Exception as e:
            analyzer_logger.error(f"提取标签元素失败: {str(e)}")
            return []
    
    def create_labeled_screenshot_advanced(self, screenshot_path: str, elements: List[Dict], 
                                         window_info: Dict, uia_result: Dict) -> Optional[str]:
        """创建高级带标签的截图"""
        try:
            if not os.path.exists(screenshot_path):
                return None
            
            # 打开原始截图
            img = Image.open(screenshot_path)
            draw = ImageDraw.Draw(img)
            
            # 尝试加载字体
            try:
                font = ImageFont.truetype("arial.ttf", 10)
                title_font = ImageFont.truetype("arial.ttf", 14)
            except Exception:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()
            
            # 分组元素
            interactive_count = 0
            text_count = 0
            
            for element in elements:
                x, y = element['x'], element['y']
                width, height = element['width'], element['height']
                
                # 确保坐标在图片范围内
                if x < 0 or y < 0 or x + width > img.width or y + height > img.height:
                    continue
                
                # 根据元素类型选择标记方式
                if element.get('clickable', False):
                    interactive_count += 1
                    color = 'red'
                    label = f"I{interactive_count}:{element['type']}"
                    border_width = 2
                else:
                    text_count += 1
                    color = 'blue'
                    label = f"T{text_count}"
                    border_width = 1
                
                # 绘制边框
                draw.rectangle([x, y, x + width, y + height], outline=color, width=border_width)
                
                # 绘制标签
                if element.get('text'):
                    display_text = element['text'][:15]
                    if len(element['text']) > 15:
                        display_text += "..."
                    label += f"({display_text})"
                
                # 绘制标签背景和文字
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                label_x = max(0, min(x, img.width - text_width))
                label_y = max(0, y - text_height - 2)
                
                draw.rectangle([label_x, label_y, label_x + text_width, label_y + text_height], 
                             fill=color)
                draw.text((label_x, label_y), label, fill='white', font=font)
            
            # 添加分析摘要
            summary = uia_result.get('layout_analysis', {})
            total_elements = uia_result.get('total_elements', 0)
            
            summary_text = f"UIA分析: {total_elements}个元素, {interactive_count}个交互, {text_count}个文本"
            
            # 在图片顶部绘制摘要
            draw.rectangle([0, 0, img.width, 25], fill='black')
            draw.text((5, 5), summary_text, fill='white', font=title_font)
            
            # 保存带标签的截图
            timestamp = int(time.time())
            labeled_filename = f"uia_labeled_window_{window_info['hwnd']}_{timestamp}.png"
            labeled_filepath = os.path.join(self.screenshots_dir, labeled_filename)
            img.save(labeled_filepath)
            
            return labeled_filepath
            
        except Exception as e:
            analyzer_logger.exception(f"创建高级标签截图失败: {str(e)}")
            return None
    
    def _generate_analysis_summary(self, uia_result: Dict) -> Dict:
        """生成分析摘要"""
        try:
            total_elements = uia_result.get('total_elements', 0)
            interactive_elements = len(uia_result.get('interactive_elements', []))
            text_elements = len(uia_result.get('text_content', []))
            
            layout_info = uia_result.get('layout_analysis', {})
            control_types = uia_result.get('elements_by_type', {})
            
            # 计算复杂度评分
            complexity_score = min(100, total_elements * 2 + interactive_elements * 5)
            
            # 生成建议
            suggestions = []
            if interactive_elements > 20:
                suggestions.append("界面交互元素较多，建议简化")
            if layout_info.get('depth_levels', 0) > 8:
                suggestions.append("控件层次较深，可能影响性能")
            
            accessibility_info = uia_result.get('accessibility_info', {})
            accessibility_ratio = accessibility_info.get('accessibility_ratio', 0)
            if accessibility_ratio < 0.7:
                suggestions.append("可访问性待改善，建议增加控件标识")
            
            summary = {
                'total_elements': total_elements,
                'interactive_elements': interactive_elements,
                'text_elements': text_elements,
                'control_type_count': len(control_types),
                'complexity_score': complexity_score,
                'complexity_level': 'High' if complexity_score > 70 else 'Medium' if complexity_score > 30 else 'Low',
                'accessibility_ratio': accessibility_ratio,
                'suggestions': suggestions,
                'top_control_types': sorted(control_types.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            }
            
            return summary
            
        except Exception as e:
            analyzer_logger.error(f"生成分析摘要失败: {str(e)}")
            return {} 