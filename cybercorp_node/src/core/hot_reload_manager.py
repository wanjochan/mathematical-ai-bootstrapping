"""
Hot reload manager that integrates file monitoring, module reloading, and config updates
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Set, Optional, Callable, Any

from .file_monitor import FileMonitor
from .module_reloader import ModuleReloader
from .config_manager import ConfigManager

logger = logging.getLogger('HotReloadManager')

class HotReloadManager:
    """Manages hot reload functionality for the client"""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize hot reload manager
        
        Args:
            base_dir: Base directory for the application
        """
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(__file__))
        self.file_monitor = FileMonitor(poll_interval=2.0)
        self.module_reloader = ModuleReloader()
        self.config_manager = ConfigManager(base_dir)
        
        self.running = False
        self.reload_callbacks: list[Callable] = []
        
        # Setup components
        self._setup_file_monitor()
        self._setup_module_reloader()
        self._setup_config_manager()
        
    def _setup_file_monitor(self):
        """Setup file monitoring"""
        # Monitor Python files in utils directory
        utils_dir = os.path.join(self.base_dir, 'utils')
        self.file_monitor.add_directory(utils_dir, "*.py")
        
        # Add callback for file changes
        self.file_monitor.add_callback(self._on_file_change)
        
    def _setup_module_reloader(self):
        """Setup module reloader with reloadable modules"""
        # Mark utils modules as reloadable
        reloadable_patterns = [
            'utils.remote_control',
            'utils.window_cache',
            'utils.win32_backend',
            'utils.ocr_backend',
            'utils.data_persistence',
            # Don't reload self to avoid issues
            # 'utils.file_monitor',
            # 'utils.module_reloader',
            # 'utils.config_manager',
        ]
        
        for pattern in reloadable_patterns:
            self.module_reloader.add_reloadable_module(pattern)
    
    def _setup_config_manager(self):
        """Setup configuration management"""
        # Add config files
        config_path = os.path.join(self.base_dir, 'config.ini')
        if os.path.exists(config_path):
            self.config_manager.add_config_file('main', config_path)
            
        # Add callback for config changes
        self.config_manager.add_change_callback('main', self._on_config_change)
    
    async def _on_file_change(self, file_path: str, change_type: str):
        """Handle file change events"""
        logger.info(f"File {change_type}: {file_path}")
        
        if change_type == 'modified' and file_path.endswith('.py'):
            # Reload Python module
            success = self.module_reloader.reload_from_path(file_path)
            
            if success:
                logger.info(f"Successfully reloaded module from: {file_path}")
                await self._trigger_reload_callbacks('module', file_path)
            else:
                logger.error(f"Failed to reload module from: {file_path}")
                
        elif change_type == 'modified' and any(file_path.endswith(ext) for ext in ['.ini', '.cfg', '.json', '.yaml', '.yml']):
            # Reload config file
            reloaded = await self.config_manager.check_reload()
            
            if reloaded:
                logger.info(f"Reloaded configs: {reloaded}")
                await self._trigger_reload_callbacks('config', reloaded)
    
    def _on_config_change(self, key: str, value: Any):
        """Handle configuration change"""
        logger.info(f"Config changed: {key} = {value}")
        
        # Apply specific config changes
        if key == 'client.heartbeat_interval':
            # Update heartbeat interval dynamically
            logger.info(f"Updating heartbeat interval to: {value}")
        elif key == 'client.reconnect_interval':
            # Update reconnect interval
            logger.info(f"Updating reconnect interval to: {value}")
    
    def add_reload_callback(self, callback: Callable):
        """
        Add callback for reload events
        
        Callback signature: callback(reload_type: str, data: Any)
        """
        self.reload_callbacks.append(callback)
    
    async def _trigger_reload_callbacks(self, reload_type: str, data: Any):
        """Trigger reload callbacks"""
        for callback in self.reload_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(reload_type, data)
                else:
                    callback(reload_type, data)
            except Exception as e:
                logger.error(f"Error in reload callback: {e}")
    
    async def start(self):
        """Start hot reload monitoring"""
        if self.running:
            logger.warning("Hot reload manager already running")
            return
        
        self.running = True
        logger.info("Starting hot reload manager")
        
        # Start file monitor
        await self.file_monitor.start()
        
        # Initial config load
        self.config_manager.reload_all()
        
    async def stop(self):
        """Stop hot reload monitoring"""
        self.running = False
        
        # Stop file monitor
        await self.file_monitor.stop()
        
        logger.info("Hot reload manager stopped")
    
    def reload_module(self, module_name: str) -> bool:
        """Manually reload a module"""
        return self.module_reloader.reload_module(module_name)
    
    def reload_config(self, config_name: str = None) -> list:
        """Manually reload configuration"""
        if config_name:
            if self.config_manager.load_config(config_name):
                return [config_name]
            return []
        else:
            return self.config_manager.reload_all()
    
    def get_config(self, name: str, key: str = None, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config_manager.get(name, key, default)
    
    def set_config(self, name: str, key: str, value: Any):
        """Set configuration value (in memory)"""
        self.config_manager.set(name, key, value)
    
    def get_stats(self) -> dict:
        """Get hot reload statistics"""
        return {
            'running': self.running,
            'file_monitor': self.file_monitor.get_stats(),
            'reloadable_modules': self.module_reloader.get_reloadable_modules(),
            'loaded_configs': list(self.config_manager.configs.keys())
        }


# Example usage in client
async def integrate_hot_reload(client):
    """
    Example of integrating hot reload into the client
    
    Usage in client.py:
        # In __init__:
        self.hot_reload = HotReloadManager()
        
        # In connect method after successful connection:
        await self.hot_reload.start()
        
        # Add reload callback:
        self.hot_reload.add_reload_callback(self._on_hot_reload)
        
        # In shutdown:
        await self.hot_reload.stop()
    """
    # Create hot reload manager
    hot_reload = HotReloadManager()
    
    # Add callback for handling reloads
    async def on_reload(reload_type: str, data: Any):
        if reload_type == 'module':
            logger.info(f"Module reloaded: {data}")
            # Reinitialize any module-specific resources
        elif reload_type == 'config':
            logger.info(f"Config reloaded: {data}")
            # Apply new configuration
            
    hot_reload.add_reload_callback(on_reload)
    
    # Start monitoring
    await hot_reload.start()
    
    return hot_reload