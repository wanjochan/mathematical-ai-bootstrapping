"""
File monitoring utility for hot-reload functionality
Monitors Python files for changes and triggers reload events
"""

import os
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, Set, Callable, Optional, List
import hashlib

logger = logging.getLogger('FileMonitor')

class FileMonitor:
    """Monitors files for changes and triggers callbacks"""
    
    def __init__(self, poll_interval: float = 1.0):
        """
        Initialize file monitor
        
        Args:
            poll_interval: How often to check for changes (seconds)
        """
        self.poll_interval = poll_interval
        self.watched_files: Dict[str, str] = {}  # path -> hash
        self.watched_dirs: Dict[str, float] = {}  # path -> mtime
        self.callbacks: List[Callable] = []
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
    def add_file(self, file_path: str):
        """Add a file to monitor"""
        path = Path(file_path).resolve()
        if path.exists() and path.is_file():
            self.watched_files[str(path)] = self._get_file_hash(path)
            logger.info(f"Added file to monitor: {path}")
        else:
            logger.warning(f"File not found: {file_path}")
    
    def add_directory(self, dir_path: str, pattern: str = "*.py"):
        """Add a directory to monitor for Python files"""
        path = Path(dir_path).resolve()
        if path.exists() and path.is_dir():
            self.watched_dirs[str(path)] = path.stat().st_mtime
            # Add all matching files in directory
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    self.add_file(str(file_path))
            logger.info(f"Added directory to monitor: {path}")
        else:
            logger.warning(f"Directory not found: {dir_path}")
    
    def remove_file(self, file_path: str):
        """Remove a file from monitoring"""
        path = str(Path(file_path).resolve())
        if path in self.watched_files:
            del self.watched_files[path]
            logger.info(f"Removed file from monitor: {path}")
    
    def add_callback(self, callback: Callable[[str, str], None]):
        """
        Add a callback for file changes
        
        Callback signature: callback(file_path: str, change_type: str)
        change_type: 'modified', 'created', 'deleted'
        """
        self.callbacks.append(callback)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for change detection"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return ""
    
    async def _check_changes(self):
        """Check for file changes"""
        changes = []
        
        # Check watched files
        for file_path, old_hash in list(self.watched_files.items()):
            path = Path(file_path)
            
            if not path.exists():
                # File deleted
                changes.append((file_path, 'deleted'))
                del self.watched_files[file_path]
            else:
                # Check if modified
                new_hash = self._get_file_hash(path)
                if new_hash != old_hash:
                    changes.append((file_path, 'modified'))
                    self.watched_files[file_path] = new_hash
        
        # Check watched directories for new files
        for dir_path in list(self.watched_dirs.keys()):
            path = Path(dir_path)
            
            if not path.exists():
                # Directory deleted
                del self.watched_dirs[dir_path]
                # Remove all files from this directory
                for file_path in list(self.watched_files.keys()):
                    if file_path.startswith(dir_path):
                        del self.watched_files[file_path]
                        changes.append((file_path, 'deleted'))
            else:
                # Check for new Python files
                current_mtime = path.stat().st_mtime
                if current_mtime > self.watched_dirs[dir_path]:
                    self.watched_dirs[dir_path] = current_mtime
                    
                    # Look for new files
                    for file_path in path.glob("*.py"):
                        str_path = str(file_path)
                        if str_path not in self.watched_files and file_path.is_file():
                            self.watched_files[str_path] = self._get_file_hash(file_path)
                            changes.append((str_path, 'created'))
        
        # Trigger callbacks for changes
        for file_path, change_type in changes:
            logger.info(f"File {change_type}: {file_path}")
            for callback in self.callbacks:
                try:
                    await asyncio.create_task(
                        self._run_callback(callback, file_path, change_type)
                    )
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
    
    async def _run_callback(self, callback: Callable, file_path: str, change_type: str):
        """Run callback, handling both sync and async functions"""
        if asyncio.iscoroutinefunction(callback):
            await callback(file_path, change_type)
        else:
            callback(file_path, change_type)
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("File monitor started")
        
        while self.running:
            try:
                await self._check_changes()
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
            
            await asyncio.sleep(self.poll_interval)
        
        logger.info("File monitor stopped")
    
    async def start(self):
        """Start monitoring"""
        if self.running:
            logger.warning("Monitor already running")
            return
        
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Starting file monitor")
    
    async def stop(self):
        """Stop monitoring"""
        self.running = False
        
        if self.monitor_task:
            await self.monitor_task
            self.monitor_task = None
        
        logger.info("File monitor stopped")
    
    def get_watched_files(self) -> List[str]:
        """Get list of currently watched files"""
        return list(self.watched_files.keys())
    
    def get_stats(self) -> dict:
        """Get monitoring statistics"""
        return {
            'watched_files': len(self.watched_files),
            'watched_dirs': len(self.watched_dirs),
            'callbacks': len(self.callbacks),
            'running': self.running
        }