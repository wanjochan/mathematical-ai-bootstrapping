"""
Enhanced logging system with file persistence, rotation, and remote viewing
"""

import os
import sys
import logging
import logging.handlers
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import deque
import gzip
import shutil

class LogManager:
    """Manages logging with persistence, rotation, and remote access"""
    
    def __init__(self, log_dir: str = None, app_name: str = "CyberCorpClient"):
        """
        Initialize log manager
        
        Args:
            log_dir: Directory for log files
            app_name: Application name for log files
        """
        self.log_dir = log_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        self.app_name = app_name
        
        # Create log directory
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        
        # Log file paths
        self.log_file = os.path.join(self.log_dir, f'{app_name}.log')
        self.error_log_file = os.path.join(self.log_dir, f'{app_name}_error.log')
        
        # In-memory log buffer for remote viewing
        self.log_buffer = deque(maxlen=1000)  # Keep last 1000 log entries
        self.error_buffer = deque(maxlen=200)  # Keep last 200 error entries
        
        # Setup handlers
        self.handlers = {}
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup logging handlers"""
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        self.handlers['console'] = console_handler
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        self.handlers['file'] = file_handler
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
        self.handlers['error'] = error_handler
        
        # Memory handler for remote viewing
        memory_handler = MemoryHandler(self.log_buffer, self.error_buffer)
        memory_handler.setLevel(logging.DEBUG)
        memory_handler.setFormatter(file_formatter)
        root_logger.addHandler(memory_handler)
        self.handlers['memory'] = memory_handler
        
    def rotate_logs(self):
        """Manually trigger log rotation"""
        for name, handler in self.handlers.items():
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.doRollover()
                logging.info(f"Rotated log: {handler.baseFilename}")
    
    def compress_old_logs(self):
        """Compress old log files"""
        log_pattern = f"{self.app_name}.log.*"
        log_files = list(Path(self.log_dir).glob(log_pattern))
        
        for log_file in log_files:
            if not str(log_file).endswith('.gz'):
                # Compress the file
                with open(log_file, 'rb') as f_in:
                    with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove original file
                os.remove(log_file)
                logging.info(f"Compressed log file: {log_file}")
    
    def get_recent_logs(self, count: int = 100, level: str = None) -> List[Dict[str, Any]]:
        """
        Get recent log entries
        
        Args:
            count: Number of entries to retrieve
            level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        entries = list(self.log_buffer)
        
        if level:
            level_value = getattr(logging, level.upper(), None)
            if level_value:
                entries = [e for e in entries if e['level'] >= level_value]
        
        return entries[-count:]
    
    def get_error_logs(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get recent error log entries"""
        return list(self.error_buffer)[-count:]
    
    def search_logs(self, pattern: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search logs for pattern"""
        results = []
        pattern_lower = pattern.lower()
        
        for entry in self.log_buffer:
            if pattern_lower in entry.get('message', '').lower():
                results.append(entry)
                if len(results) >= max_results:
                    break
        
        return results
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        stats = {
            'total_entries': len(self.log_buffer),
            'error_entries': len(self.error_buffer),
            'log_files': {},
            'level_counts': {}
        }
        
        # Count by level
        for entry in self.log_buffer:
            level = entry.get('level_name', 'UNKNOWN')
            stats['level_counts'][level] = stats['level_counts'].get(level, 0) + 1
        
        # Get file sizes
        for name, path in [('main', self.log_file), ('error', self.error_log_file)]:
            if os.path.exists(path):
                stats['log_files'][name] = {
                    'path': path,
                    'size': os.path.getsize(path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
                }
        
        return stats
    
    def export_logs(self, start_time: datetime = None, end_time: datetime = None,
                   output_file: str = None) -> str:
        """
        Export logs to file
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            output_file: Output file path
        
        Returns:
            Path to exported file
        """
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.log_dir, f'export_{timestamp}.json')
        
        entries = list(self.log_buffer)
        
        # Filter by time if specified
        if start_time or end_time:
            filtered = []
            for entry in entries:
                entry_time = entry.get('timestamp')
                if entry_time:
                    if start_time and entry_time < start_time:
                        continue
                    if end_time and entry_time > end_time:
                        continue
                    filtered.append(entry)
            entries = filtered
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'export_time': datetime.now().isoformat(),
                'entries': entries,
                'count': len(entries)
            }, f, indent=2, default=str)
        
        return output_file
    
    def set_log_level(self, logger_name: str = None, level: str = 'INFO'):
        """
        Set log level for specific logger or root
        
        Args:
            logger_name: Logger name (None for root)
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
        level_value = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(level_value)
        
        logging.info(f"Set log level for {logger_name or 'root'} to {level}")


class MemoryHandler(logging.Handler):
    """Custom handler that stores logs in memory"""
    
    def __init__(self, log_buffer: deque, error_buffer: deque):
        super().__init__()
        self.log_buffer = log_buffer
        self.error_buffer = error_buffer
    
    def emit(self, record):
        """Store log record in memory"""
        try:
            entry = {
                'timestamp': datetime.fromtimestamp(record.created),
                'level': record.levelno,
                'level_name': record.levelname,
                'logger': record.name,
                'message': self.format(record),
                'function': record.funcName,
                'line': record.lineno,
                'thread': record.thread,
                'thread_name': record.threadName
            }
            
            # Add to main buffer
            self.log_buffer.append(entry)
            
            # Add to error buffer if error or critical
            if record.levelno >= logging.ERROR:
                self.error_buffer.append(entry)
                
        except Exception:
            self.handleError(record)


# Global log manager instance
_log_manager = None

def get_log_manager() -> LogManager:
    """Get or create global log manager instance"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager()
    return _log_manager

def setup_logging(log_dir: str = None, app_name: str = "CyberCorpClient"):
    """Setup logging for the application"""
    global _log_manager
    _log_manager = LogManager(log_dir, app_name)
    return _log_manager