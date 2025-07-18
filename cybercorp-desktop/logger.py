#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志模块
提供统一的日志功能
"""

import logging
import os
import time
from datetime import datetime


class Logger:
    def __init__(self, name="WindowManager", log_level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            self.setup_logger()
    
    def setup_logger(self):
        """设置日志器"""
        # 创建logs目录
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器
        log_filename = os.path.join(logs_dir, f"window_manager_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def critical(self, message):
        self.logger.critical(message)
    
    def exception(self, message):
        self.logger.exception(message)


# 创建全局日志器实例
app_logger = Logger("WindowManagerApp")
window_logger = Logger("WindowManager")
analyzer_logger = Logger("WindowAnalyzer") 