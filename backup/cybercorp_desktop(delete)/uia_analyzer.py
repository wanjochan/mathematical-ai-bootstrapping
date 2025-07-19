#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于UIA (UI Automation) 的高级窗口分析器
提供详细的控件层次结构和布局信息
"""

import win32gui
from comtypes import client
import comtypes.gen.UIAutomationClient as UIA
from comtypes.client import CreateObject
import time
import json
from typing import List, Dict, Optional, Any
from logger import analyzer_logger


class UIAAnalyzer:
    """基于UIA的窗口分析器"""
    
    def __init__(self):
        self.uia = None
        self.tree_walker = None
        self.initialization_method = None
        self.com_initialized = False
        
        # 添加详细的诊断日志
        analyzer_logger.info("开始UIA分析器初始化诊断")
        
        # 诊断1: 检查Windows版本
        self._log_system_info()
        
        # 诊断2: 检查COM环境
        self._diagnose_com_environment()
        
        # 尝试多种UIA初始化策略
        self._initialize_uia_with_strategies()
    
    def _log_system_info(self):
        """记录系统信息用于诊断"""
        try:
            import platform
            import sys
            
            analyzer_logger.info(f"系统诊断:")
            analyzer_logger.info(f"  - Windows版本: {platform.platform()}")
            analyzer_logger.info(f"  - Python版本: {sys.version}")
            analyzer_logger.info(f"  - Python架构: {platform.architecture()}")
            
        except Exception as e:
            analyzer_logger.warning(f"无法获取系统信息: {str(e)}")
    
    def _diagnose_com_environment(self):
        """诊断COM环境"""
        try:
            import pythoncom
            import win32api
            
            analyzer_logger.info("COM环境诊断:")
            
            # 检查COM初始化状态
            try:
                # 尝试获取当前线程的COM状态
                pythoncom.CoInitialize()
                self.com_initialized = True
                analyzer_logger.info("  - COM初始化: 成功")
                
                # 检查COM安全设置
                try:
                    pythoncom.CoInitializeSecurity(None, -1, None, None,
                                                 pythoncom.RPC_C_AUTHN_LEVEL_NONE,
                                                 pythoncom.RPC_C_IMP_LEVEL_IMPERSONATE,
                                                 None, pythoncom.EOAC_NONE, None)
                    analyzer_logger.info("  - COM安全设置: 已配置")
                except Exception as sec_e:
                    analyzer_logger.warning(f"  - COM安全设置失败: {str(sec_e)}")
                
            except Exception as com_e:
                analyzer_logger.error(f"  - COM初始化失败: {str(com_e)}")
                self.com_initialized = False
            
            # 检查UIA相关注册表项
            self._check_uia_registration()
            
        except ImportError as e:
            analyzer_logger.error(f"缺少必要的COM模块: {str(e)}")
        except Exception as e:
            analyzer_logger.error(f"COM环境诊断失败: {str(e)}")
    
    def _check_uia_registration(self):
        """检查UIA COM组件注册状态"""
        try:
            import winreg
            
            analyzer_logger.info("UIA注册状态检查:")
            
            # 检查常见的UIA CLSID
            uia_clsids = [
                ("CUIAutomation8.CUIAutomation", "{E22AD333-B25F-460C-83D0-0581107395C9}"),
                ("CUIAutomation.CUIAutomation", "{FF48DBA4-60EF-4201-AA87-54103EEF594E}"),
            ]
            
            for prog_id, clsid in uia_clsids:
                try:
                    # 检查ProgID注册
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, prog_id):
                        analyzer_logger.info(f"  - {prog_id}: 已注册")
                except FileNotFoundError:
                    analyzer_logger.warning(f"  - {prog_id}: 未注册")
                except Exception as e:
                    analyzer_logger.warning(f"  - {prog_id}: 检查失败 - {str(e)}")
                
                try:
                    # 检查CLSID注册
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"CLSID\\{clsid}"):
                        analyzer_logger.info(f"  - CLSID {clsid}: 已注册")
                except FileNotFoundError:
                    analyzer_logger.warning(f"  - CLSID {clsid}: 未注册")
                except Exception as e:
                    analyzer_logger.warning(f"  - CLSID {clsid}: 检查失败 - {str(e)}")
                    
        except Exception as e:
            analyzer_logger.error(f"注册状态检查失败: {str(e)}")
    
    def _initialize_uia_with_strategies(self):
        """使用多种策略初始化UIA"""
        strategies = [
            ("CUIAutomation8_Direct", self._init_cuiautomation8_direct),
            ("CUIAutomation8_CoCreate", self._init_cuiautomation8_cocreate),
            ("CUIAutomation_Direct", self._init_cuiautomation_direct),
            ("CUIAutomation_CoCreate", self._init_cuiautomation_cocreate),
            ("UIAutomation_Library", self._init_uiautomation_library),
            ("Comtypes_Alternative", self._init_comtypes_alternative)
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                analyzer_logger.info(f"尝试策略: {strategy_name}")
                if strategy_func():
                    self.initialization_method = strategy_name
                    analyzer_logger.info(f"UIA初始化成功 - 使用策略: {strategy_name}")
                    return
                else:
                    analyzer_logger.warning(f"策略 {strategy_name} 失败")
            except Exception as e:
                analyzer_logger.error(f"策略 {strategy_name} 异常: {str(e)}")
        
        analyzer_logger.error("所有UIA初始化策略均失败")
        self.uia = None
        self.tree_walker = None
    
    def _init_cuiautomation8_direct(self):
        """策略1: 直接创建CUIAutomation8"""
        try:
            self.uia = CreateObject("CUIAutomation8.CUIAutomation")
            if self.uia:
                self.tree_walker = self.uia.RawViewWalker
                return True
        except Exception as e:
            analyzer_logger.debug(f"CUIAutomation8直接创建失败: {str(e)}")
        return False
    
    def _init_cuiautomation8_cocreate(self):
        """策略2: 使用CoCreateInstance创建CUIAutomation8"""
        try:
            import pythoncom
            clsid = pythoncom.CLSID("{E22AD333-B25F-460C-83D0-0581107395C9}")
            self.uia = pythoncom.CoCreateInstance(clsid, None, pythoncom.CLSCTX_INPROC_SERVER,
                                                pythoncom.IID_IDispatch)
            if self.uia:
                self.tree_walker = self.uia.RawViewWalker
                return True
        except Exception as e:
            analyzer_logger.debug(f"CUIAutomation8 CoCreateInstance失败: {str(e)}")
        return False
    
    def _init_cuiautomation_direct(self):
        """策略3: 直接创建CUIAutomation"""
        try:
            self.uia = CreateObject("CUIAutomation.CUIAutomation")
            if self.uia:
                self.tree_walker = self.uia.RawViewWalker
                return True
        except Exception as e:
            analyzer_logger.debug(f"CUIAutomation直接创建失败: {str(e)}")
        return False
    
    def _init_cuiautomation_cocreate(self):
        """策略4: 使用CoCreateInstance创建CUIAutomation"""
        try:
            import pythoncom
            clsid = pythoncom.CLSID("{FF48DBA4-60EF-4201-AA87-54103EEF594E}")
            self.uia = pythoncom.CoCreateInstance(clsid, None, pythoncom.CLSCTX_INPROC_SERVER,
                                                pythoncom.IID_IDispatch)
            if self.uia:
                self.tree_walker = self.uia.RawViewWalker
                return True
        except Exception as e:
            analyzer_logger.debug(f"CUIAutomation CoCreateInstance失败: {str(e)}")
        return False
    
    def _init_uiautomation_library(self):
        """策略5: 使用uiautomation库"""
        try:
            import uiautomation as auto
            # 测试基本功能
            desktop = auto.GetRootControl()
            if desktop:
                self.uia = auto
                self.initialization_method = "UIAutomation_Library"
                analyzer_logger.info("使用uiautomation库作为后备方案")
                return True
        except ImportError:
            analyzer_logger.debug("uiautomation库未安装")
        except Exception as e:
            analyzer_logger.debug(f"uiautomation库初始化失败: {str(e)}")
        return False
    
    def _init_comtypes_alternative(self):
        """策略6: 使用comtypes的替代方法"""
        try:
            import comtypes
            import comtypes.client
            
            # 尝试不同的线程模型
            comtypes.CoInitializeEx(comtypes.COINIT_APARTMENTTHREADED)
            
            self.uia = comtypes.client.CreateObject("CUIAutomation.CUIAutomation")
            if self.uia:
                self.tree_walker = self.uia.RawViewWalker
                return True
        except Exception as e:
            analyzer_logger.debug(f"comtypes替代方法失败: {str(e)}")
        return False
    
    def __del__(self):
        """析构函数，清理COM资源"""
        try:
            if self.com_initialized:
                import pythoncom
                pythoncom.CoUninitialize()
                analyzer_logger.debug("COM资源已清理")
        except Exception as e:
            analyzer_logger.debug(f"COM清理失败: {str(e)}")
    
    def is_available(self) -> bool:
        """检查UIA是否可用"""
        return self.uia is not None
    
    def get_initialization_info(self) -> Dict:
        """获取初始化信息"""
        return {
            'available': self.is_available(),
            'method': self.initialization_method,
            'com_initialized': self.com_initialized
        }
    
    def analyze_window_detailed(self, hwnd: int) -> Dict:
        """详细分析窗口的UIA结构"""
        if not self.uia:
            raise Exception("UIA未初始化成功")
        
        try:
            analyzer_logger.info(f"开始UIA详细分析窗口 {hwnd} (方法: {self.initialization_method})")
            
            # 根据初始化方法选择不同的分析路径
            if self.initialization_method == "UIAutomation_Library":
                return self._analyze_with_uiautomation_library(hwnd)
            else:
                return self._analyze_with_com_uia(hwnd)
            
        except Exception as e:
            analyzer_logger.exception(f"UIA窗口分析失败: {str(e)}")
            raise
    
    def _analyze_with_com_uia(self, hwnd: int) -> Dict:
        """使用COM UIA进行分析"""
        # 从窗口句柄获取UIA元素
        element = self.uia.ElementFromHandle(hwnd)
        if not element:
            raise Exception("无法从窗口句柄获取UIA元素")
        
        # 分析根元素
        root_info = self._analyze_element(element, depth=0)
        
        # 递归分析子元素
        children = self._get_all_children(element, max_depth=10)
        
        # 构建控件树
        control_tree = self._build_control_tree(element)
        
        # 分析布局信息
        layout_info = self._analyze_layout(children)
        
        # 分析交互元素
        interactive_elements = self._find_interactive_elements(children)
        
        # 分析文本内容
        text_elements = self._extract_text_content(children)
        
        result = {
            'analysis_type': 'UIA_COM_Detailed',
            'initialization_method': self.initialization_method,
            'window_hwnd': hwnd,
            'root_element': root_info,
            'total_elements': len(children),
            'control_tree': control_tree,
            'layout_analysis': layout_info,
            'interactive_elements': interactive_elements,
            'text_content': text_elements,
            'elements_by_type': self._group_by_control_type(children),
            'accessibility_info': self._get_accessibility_info(children),
            'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        analyzer_logger.info(f"COM UIA分析完成，发现 {len(children)} 个元素")
        return result
    
    def _analyze_with_uiautomation_library(self, hwnd: int) -> Dict:
        """使用uiautomation库进行分析"""
        try:
            # 使用uiautomation库的方法
            window_control = self.uia.ControlFromHandle(hwnd)
            if not window_control:
                raise Exception("无法从窗口句柄获取控件")
            
            # 获取所有子控件
            all_controls = []
            self._collect_controls_recursive(window_control, all_controls, max_depth=10)
            
            # 转换为标准格式
            children = []
            for control in all_controls:
                try:
                    element_info = self._analyze_uiautomation_control(control, len(children))
                    children.append(element_info)
                except Exception as e:
                    analyzer_logger.debug(f"分析控件失败: {str(e)}")
                    continue
            
            # 分析根元素
            root_info = self._analyze_uiautomation_control(window_control, 0)
            
            # 分析布局信息
            layout_info = self._analyze_layout(children)
            
            # 分析交互元素
            interactive_elements = self._find_interactive_elements(children)
            
            # 分析文本内容
            text_elements = self._extract_text_content(children)
            
            result = {
                'analysis_type': 'UIA_Library_Detailed',
                'initialization_method': self.initialization_method,
                'window_hwnd': hwnd,
                'root_element': root_info,
                'total_elements': len(children),
                'layout_analysis': layout_info,
                'interactive_elements': interactive_elements,
                'text_content': text_elements,
                'elements_by_type': self._group_by_control_type(children),
                'accessibility_info': self._get_accessibility_info(children),
                'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            analyzer_logger.info(f"UIAutomation库分析完成，发现 {len(children)} 个元素")
            return result
            
        except Exception as e:
            analyzer_logger.error(f"UIAutomation库分析失败: {str(e)}")
            raise
    
    def _collect_controls_recursive(self, control, all_controls: List, depth: int = 0, max_depth: int = 10):
        """递归收集所有控件"""
        if depth > max_depth:
            return
        
        try:
            children = control.GetChildren()
            for child in children:
                all_controls.append(child)
                self._collect_controls_recursive(child, all_controls, depth + 1, max_depth)
        except Exception as e:
            analyzer_logger.debug(f"收集子控件失败 (depth={depth}): {str(e)}")
    
    def _analyze_uiautomation_control(self, control, depth: int) -> Dict:
        """分析uiautomation库的控件"""
        try:
            # 获取基本属性
            name = getattr(control, 'Name', '') or ''
            control_type = getattr(control, 'ControlTypeName', '') or 'Unknown'
            class_name = getattr(control, 'ClassName', '') or ''
            automation_id = getattr(control, 'AutomationId', '') or ''
            
            # 获取位置信息
            try:
                rect = control.BoundingRectangle
                bounds = {
                    'x': int(rect.left),
                    'y': int(rect.top),
                    'width': int(rect.right - rect.left),
                    'height': int(rect.bottom - rect.top)
                }
            except:
                bounds = {'x': 0, 'y': 0, 'width': 0, 'height': 0}
            
            # 获取状态信息
            is_enabled = getattr(control, 'IsEnabled', True)
            is_visible = not getattr(control, 'IsOffscreen', True)
            
            # 获取文本内容
            text_content = name
            try:
                if hasattr(control, 'GetValuePattern'):
                    value_pattern = control.GetValuePattern()
                    if value_pattern:
                        text_content = value_pattern.Value or text_content
            except:
                pass
            
            element_info = {
                'depth': depth,
                'name': name,
                'control_type': 0,  # uiautomation库不提供数字类型
                'control_type_name': control_type,
                'class_name': class_name,
                'automation_id': automation_id,
                'bounds': bounds,
                'is_enabled': is_enabled,
                'is_visible': is_visible,
                'has_focus': False,  # 简化处理
                'text_content': text_content,
                'supported_patterns': [],  # 简化处理
                'is_interactive': control_type in ['Button', 'Edit', 'ComboBox', 'ListBox', 'CheckBox', 'RadioButton']
            }
            
            return element_info
            
        except Exception as e:
            analyzer_logger.debug(f"分析uiautomation控件时出错: {str(e)}")
            return {
                'depth': depth,
                'name': 'Unknown',
                'control_type': 0,
                'control_type_name': 'Unknown',
                'error': str(e)
            }
    
    def _analyze_element(self, element, depth=0) -> Dict:
        """分析单个UIA元素"""
        try:
            # 基本属性
            name = self._safe_get_property(element, "CurrentName")
            control_type = self._safe_get_property(element, "CurrentControlType")
            class_name = self._safe_get_property(element, "CurrentClassName")
            automation_id = self._safe_get_property(element, "CurrentAutomationId")
            
            # 位置和大小
            try:
                rect = element.CurrentBoundingRectangle
                bounds = {
                    'x': int(rect.left),
                    'y': int(rect.top),
                    'width': int(rect.right - rect.left),
                    'height': int(rect.bottom - rect.top)
                }
            except:
                bounds = {'x': 0, 'y': 0, 'width': 0, 'height': 0}
            
            # 状态信息
            is_enabled = self._safe_get_property(element, "CurrentIsEnabled")
            is_visible = self._safe_get_property(element, "CurrentIsOffscreen") == False
            has_keyboard_focus = self._safe_get_property(element, "CurrentHasKeyboardFocus")
            
            # 控件类型名称
            control_type_name = self._get_control_type_name(control_type)
            
            # 支持的模式
            supported_patterns = self._get_supported_patterns(element)
            
            # 文本内容
            text_content = self._get_element_text(element)
            
            element_info = {
                'depth': depth,
                'name': name,
                'control_type': control_type,
                'control_type_name': control_type_name,
                'class_name': class_name,
                'automation_id': automation_id,
                'bounds': bounds,
                'is_enabled': is_enabled,
                'is_visible': is_visible,
                'has_focus': has_keyboard_focus,
                'text_content': text_content,
                'supported_patterns': supported_patterns,
                'is_interactive': len([p for p in supported_patterns if p in 
                                     ['Invoke', 'SelectionItem', 'Toggle', 'RangeValue', 'Text']]) > 0
            }
            
            return element_info
            
        except Exception as e:
            analyzer_logger.debug(f"分析元素时出错: {str(e)}")
            return {
                'depth': depth,
                'name': 'Unknown',
                'control_type': 0,
                'control_type_name': 'Unknown',
                'error': str(e)
            }
    
    def _get_all_children(self, root_element, max_depth=10) -> List[Dict]:
        """递归获取所有子元素"""
        elements = []
        
        def traverse(element, depth):
            if depth > max_depth:
                return
            
            try:
                child = self.tree_walker.GetFirstChildElement(element)
                while child:
                    element_info = self._analyze_element(child, depth)
                    elements.append(element_info)
                    
                    # 递归遍历子元素
                    traverse(child, depth + 1)
                    
                    child = self.tree_walker.GetNextSiblingElement(child)
                    
            except Exception as e:
                analyzer_logger.debug(f"遍历子元素时出错 (depth={depth}): {str(e)}")
        
        traverse(root_element, 1)
        return elements
    
    def _build_control_tree(self, root_element) -> Dict:
        """构建控件树结构"""
        def build_tree_node(element, depth=0):
            if depth > 8:  # 限制深度避免无限递归
                return None
            
            node_info = self._analyze_element(element, depth)
            node_info['children'] = []
            
            try:
                child = self.tree_walker.GetFirstChildElement(element)
                while child:
                    child_node = build_tree_node(child, depth + 1)
                    if child_node:
                        node_info['children'].append(child_node)
                    child = self.tree_walker.GetNextSiblingElement(child)
            except:
                pass
            
            return node_info
        
        return build_tree_node(root_element)
    
    def _analyze_layout(self, elements: List[Dict]) -> Dict:
        """分析布局信息"""
        if not elements:
            return {}
        
        # 按深度分组
        by_depth = {}
        for elem in elements:
            depth = elem.get('depth', 0)
            if depth not in by_depth:
                by_depth[depth] = []
            by_depth[depth].append(elem)
        
        # 计算布局统计
        total_bounds = {'min_x': float('inf'), 'min_y': float('inf'), 
                       'max_x': 0, 'max_y': 0}
        
        visible_elements = []
        for elem in elements:
            if elem.get('is_visible') and elem.get('bounds'):
                bounds = elem['bounds']
                if bounds['width'] > 0 and bounds['height'] > 0:
                    visible_elements.append(elem)
                    total_bounds['min_x'] = min(total_bounds['min_x'], bounds['x'])
                    total_bounds['min_y'] = min(total_bounds['min_y'], bounds['y'])
                    total_bounds['max_x'] = max(total_bounds['max_x'], bounds['x'] + bounds['width'])
                    total_bounds['max_y'] = max(total_bounds['max_y'], bounds['y'] + bounds['height'])
        
        # 分析控件类型分布
        type_distribution = {}
        for elem in elements:
            ctrl_type = elem.get('control_type_name', 'Unknown')
            type_distribution[ctrl_type] = type_distribution.get(ctrl_type, 0) + 1
        
        return {
            'depth_levels': len(by_depth),
            'elements_by_depth': {str(k): len(v) for k, v in by_depth.items()},
            'visible_elements_count': len(visible_elements),
            'total_bounds': total_bounds if total_bounds['min_x'] != float('inf') else None,
            'control_type_distribution': type_distribution,
            'layout_density': len(visible_elements) / max(1, (total_bounds['max_x'] - total_bounds['min_x']) * 
                                                          (total_bounds['max_y'] - total_bounds['min_y'])) if total_bounds['min_x'] != float('inf') else 0
        }
    
    def _find_interactive_elements(self, elements: List[Dict]) -> List[Dict]:
        """查找可交互元素"""
        interactive = []
        
        for elem in elements:
            if elem.get('is_interactive') and elem.get('is_visible') and elem.get('is_enabled'):
                interactive_info = {
                    'name': elem.get('name', ''),
                    'type': elem.get('control_type_name', ''),
                    'automation_id': elem.get('automation_id', ''),
                    'bounds': elem.get('bounds', {}),
                    'patterns': elem.get('supported_patterns', []),
                    'text': elem.get('text_content', ''),
                    'depth': elem.get('depth', 0)
                }
                interactive.append(interactive_info)
        
        return sorted(interactive, key=lambda x: (x['depth'], x['bounds'].get('y', 0), x['bounds'].get('x', 0)))
    
    def _extract_text_content(self, elements: List[Dict]) -> List[Dict]:
        """提取文本内容"""
        text_elements = []
        
        for elem in elements:
            text = elem.get('text_content', '')
            name = elem.get('name', '')
            
            if text or name:
                text_info = {
                    'control_type': elem.get('control_type_name', ''),
                    'name': name,
                    'text': text,
                    'bounds': elem.get('bounds', {}),
                    'automation_id': elem.get('automation_id', ''),
                    'is_visible': elem.get('is_visible', False)
                }
                text_elements.append(text_info)
        
        return text_elements
    
    def _group_by_control_type(self, elements: List[Dict]) -> Dict:
        """按控件类型分组"""
        grouped = {}
        
        for elem in elements:
            ctrl_type = elem.get('control_type_name', 'Unknown')
            if ctrl_type not in grouped:
                grouped[ctrl_type] = []
            
            grouped[ctrl_type].append({
                'name': elem.get('name', ''),
                'automation_id': elem.get('automation_id', ''),
                'bounds': elem.get('bounds', {}),
                'is_visible': elem.get('is_visible', False),
                'is_enabled': elem.get('is_enabled', False),
                'text': elem.get('text_content', '')
            })
        
        return grouped
    
    def _get_accessibility_info(self, elements: List[Dict]) -> Dict:
        """获取可访问性信息"""
        total_elements = len(elements)
        accessible_elements = len([e for e in elements if e.get('name') or e.get('automation_id')])
        focusable_elements = len([e for e in elements if 'Invoke' in e.get('supported_patterns', []) or 
                                'SelectionItem' in e.get('supported_patterns', [])])
        
        return {
            'total_elements': total_elements,
            'accessible_elements': accessible_elements,
            'accessibility_ratio': accessible_elements / max(1, total_elements),
            'focusable_elements': focusable_elements,
            'keyboard_navigable_ratio': focusable_elements / max(1, total_elements)
        }
    
    def _safe_get_property(self, element, property_name) -> Any:
        """安全获取元素属性"""
        try:
            return getattr(element, property_name)
        except:
            return None
    
    def _get_control_type_name(self, control_type) -> str:
        """获取控件类型名称"""
        type_map = {
            50000: "Button",
            50001: "Calendar", 
            50002: "CheckBox",
            50003: "ComboBox",
            50004: "Edit",
            50005: "Hyperlink",
            50006: "Image",
            50007: "ListItem",
            50008: "List",
            50009: "Menu",
            50010: "MenuBar",
            50011: "MenuItem",
            50012: "ProgressBar",
            50013: "RadioButton",
            50014: "ScrollBar",
            50015: "Slider",
            50016: "Spinner",
            50017: "StatusBar",
            50018: "Tab",
            50019: "TabItem",
            50020: "Text",
            50021: "ToolBar",
            50022: "ToolTip",
            50023: "Tree",
            50024: "TreeItem",
            50025: "Custom",
            50026: "Group",
            50027: "Thumb",
            50028: "DataGrid",
            50029: "DataItem",
            50030: "Document",
            50031: "SplitButton",
            50032: "Window",
            50033: "Pane",
            50034: "Header",
            50035: "HeaderItem",
            50036: "Table",
            50037: "TitleBar",
            50038: "Separator"
        }
        return type_map.get(control_type, f"Unknown({control_type})")
    
    def _get_supported_patterns(self, element) -> List[str]:
        """获取元素支持的模式"""
        patterns = []
        pattern_map = {
            10000: "Invoke",
            10001: "Selection",
            10002: "Value", 
            10003: "RangeValue",
            10004: "Scroll",
            10005: "ExpandCollapse",
            10006: "Grid",
            10007: "GridItem",
            10008: "MultipleView",
            10009: "Window",
            10010: "SelectionItem",
            10011: "Dock",
            10012: "Table",
            10013: "TableItem",
            10014: "Text",
            10015: "Toggle",
            10016: "Transform"
        }
        
        for pattern_id, pattern_name in pattern_map.items():
            try:
                if element.GetCurrentPattern(pattern_id):
                    patterns.append(pattern_name)
            except:
                continue
        
        return patterns
    
    def _get_element_text(self, element) -> str:
        """获取元素的文本内容"""
        try:
            # 尝试多种方式获取文本
            text_sources = [
                lambda: element.CurrentName,
                lambda: element.CurrentValue,
                lambda: element.GetCurrentPattern(10014).DocumentRange.GetText(-1) if element.GetCurrentPattern(10014) else None,
                lambda: element.CurrentHelpText
            ]
            
            for get_text in text_sources:
                try:
                    text = get_text()
                    if text and text.strip():
                        return text.strip()
                except:
                    continue
            
            return ""
        except:
            return "" 