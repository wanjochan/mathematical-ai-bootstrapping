#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窗口管理模块
负责获取当前用户会话的所有窗口信息
"""

import win32gui
import win32con
import win32process
import psutil
from typing import List, Dict, Optional
from logger import window_logger


class WindowManager:
    def __init__(self):
        self.windows = []
    
    def get_all_windows(self) -> List[Dict]:
        """获取所有可见窗口"""
        window_logger.info("开始枚举所有窗口")
        self.windows = []
        
        try:
            win32gui.EnumWindows(self._enum_window_callback, None)
            window_logger.debug(f"枚举到 {len(self.windows)} 个原始窗口")
            
            # 过滤出有意义的窗口
            filtered_windows = []
            for window in self.windows:
                if self._is_valid_window(window['hwnd']):
                    filtered_windows.append(window)
            
            window_logger.info(f"过滤后有 {len(filtered_windows)} 个有效窗口")
            return filtered_windows
            
        except Exception as e:
            window_logger.exception(f"枚举窗口失败: {str(e)}")
            return []
    
    def _enum_window_callback(self, hwnd, extra):
        """窗口枚举回调函数"""
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:  # 只获取有标题的窗口
                try:
                    # 获取窗口的进程信息
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process_name = ""
                    try:
                        process = psutil.Process(pid)
                        process_name = process.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_name = "Unknown"
                    
                    window_info = {
                        'hwnd': hwnd,
                        'title': title,
                        'pid': pid,
                        'process_name': process_name
                    }
                    self.windows.append(window_info)
                except Exception:
                    # 忽略获取进程信息失败的情况
                    window_info = {
                        'hwnd': hwnd,
                        'title': title,
                        'pid': 0,
                        'process_name': "Unknown"
                    }
                    self.windows.append(window_info)
    
    def _is_valid_window(self, hwnd: int) -> bool:
        """判断是否为有效的用户窗口"""
        try:
            # 检查窗口是否可见
            if not win32gui.IsWindowVisible(hwnd):
                return False
            
            # 检查窗口是否有标题
            title = win32gui.GetWindowText(hwnd)
            if not title or len(title.strip()) == 0:
                return False
            
            # 检查窗口样式，排除工具窗口等
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            
            # 排除工具窗口
            if ex_style & win32con.WS_EX_TOOLWINDOW:
                return False
            
            # 必须有标题栏
            if not (style & win32con.WS_CAPTION):
                return False
            
            # 获取窗口矩形，排除太小的窗口
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            if width < 50 or height < 50:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_window_info(self, hwnd: int) -> Dict:
        """获取指定窗口的详细信息"""
        try:
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            visible = win32gui.IsWindowVisible(hwnd)
            enabled = win32gui.IsWindowEnabled(hwnd)
            
            # 获取进程信息
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process_name = ""
            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = "Unknown"
            
            # 获取窗口状态
            placement = win32gui.GetWindowPlacement(hwnd)
            state = "正常"
            if placement[1] == win32con.SW_SHOWMINIMIZED:
                state = "最小化"
            elif placement[1] == win32con.SW_SHOWMAXIMIZED:
                state = "最大化"
            
            return {
                'hwnd': hwnd,
                'title': title,
                'class_name': class_name,
                'rect': rect,
                'visible': visible,
                'enabled': enabled,
                'pid': pid,
                'process_name': process_name,
                'state': state
            }
            
        except Exception as e:
            raise Exception(f"获取窗口信息失败: {str(e)}")
    
    def get_child_windows(self, parent_hwnd: int) -> List[Dict]:
        """获取指定窗口的子窗口"""
        child_windows = []
        
        def enum_child_callback(hwnd, extra):
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            visible = win32gui.IsWindowVisible(hwnd)
            
            child_windows.append({
                'hwnd': hwnd,
                'title': title if title else f"[{class_name}]",
                'class_name': class_name,
                'rect': rect,
                'visible': visible
            })
        
        try:
            win32gui.EnumChildWindows(parent_hwnd, enum_child_callback, None)
        except Exception:
            pass
        
        return child_windows
    
    def find_windows_by_title(self, title_pattern: str) -> List[Dict]:
        """根据标题模式查找窗口"""
        matching_windows = []
        all_windows = self.get_all_windows()
        
        for window in all_windows:
            if title_pattern.lower() in window['title'].lower():
                matching_windows.append(window)
        
        return matching_windows
    
    def find_windows_by_class(self, class_name: str) -> List[Dict]:
        """根据类名查找窗口"""
        matching_windows = []
        all_windows = self.get_all_windows()
        
        for window in all_windows:
            try:
                window_class = win32gui.GetClassName(window['hwnd'])
                if class_name.lower() in window_class.lower():
                    window['class_name'] = window_class
                    matching_windows.append(window)
            except Exception:
                continue
        
        return matching_windows 