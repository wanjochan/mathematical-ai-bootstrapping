"""
Configuration manager with hot-reload support
Monitors config files and applies changes without restart
"""

import os
import json
import yaml
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
import configparser
from datetime import datetime

logger = logging.getLogger('ConfigManager')

class ConfigManager:
    """Manages configuration with hot-reload support"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize config manager
        
        Args:
            config_dir: Directory containing config files
        """
        self.config_dir = config_dir or os.path.dirname(os.path.dirname(__file__))
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.config_files: Dict[str, str] = {}  # name -> path
        self.callbacks: Dict[str, List[Callable]] = {}  # config_name -> callbacks
        self.file_hashes: Dict[str, str] = {}  # path -> hash
        
    def add_config_file(self, name: str, file_path: str):
        """Add a configuration file to manage"""
        path = Path(file_path).resolve()
        
        if not path.exists():
            logger.warning(f"Config file not found: {file_path}")
            return
        
        self.config_files[name] = str(path)
        self.load_config(name)
        logger.info(f"Added config file '{name}': {path}")
    
    def load_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Load configuration from file"""
        if name not in self.config_files:
            logger.error(f"Unknown config: {name}")
            return None
        
        file_path = self.config_files[name]
        
        try:
            # Detect file type and load accordingly
            if file_path.endswith('.json'):
                config = self._load_json(file_path)
            elif file_path.endswith(('.yaml', '.yml')):
                config = self._load_yaml(file_path)
            elif file_path.endswith(('.ini', '.cfg')):
                config = self._load_ini(file_path)
            else:
                logger.error(f"Unsupported config format: {file_path}")
                return None
            
            # Store config and hash
            self.configs[name] = config
            self.file_hashes[file_path] = self._get_file_hash(file_path)
            
            logger.info(f"Loaded config '{name}' from {file_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config '{name}': {e}")
            return None
    
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Load JSON config file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load YAML config file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_ini(self, file_path: str) -> Dict[str, Any]:
        """Load INI config file"""
        parser = configparser.ConfigParser()
        parser.read(file_path, encoding='utf-8')
        
        # Convert to dict
        config = {}
        for section in parser.sections():
            config[section] = dict(parser.items(section))
        
        return config
    
    def get(self, name: str, key: str = None, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            name: Config name
            key: Optional key path (e.g., 'server.host')
            default: Default value if not found
        """
        if name not in self.configs:
            return default
        
        config = self.configs[name]
        
        if key is None:
            return config
        
        # Navigate nested keys
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, name: str, key: str, value: Any):
        """
        Set configuration value (in memory only)
        
        Args:
            name: Config name
            key: Key path (e.g., 'server.host')
            value: New value
        """
        if name not in self.configs:
            self.configs[name] = {}
        
        config = self.configs[name]
        keys = key.split('.')
        
        # Navigate to parent
        parent = config
        for k in keys[:-1]:
            if k not in parent:
                parent[k] = {}
            parent = parent[k]
        
        # Set value
        parent[keys[-1]] = value
        
        # Trigger callbacks
        self._trigger_callbacks(name, key, value)
    
    def save_config(self, name: str) -> bool:
        """Save configuration back to file"""
        if name not in self.config_files or name not in self.configs:
            logger.error(f"Cannot save unknown config: {name}")
            return False
        
        file_path = self.config_files[name]
        config = self.configs[name]
        
        try:
            # Backup existing file
            backup_path = f"{file_path}.backup"
            if os.path.exists(file_path):
                import shutil
                shutil.copy2(file_path, backup_path)
            
            # Save based on format
            if file_path.endswith('.json'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
            elif file_path.endswith(('.yaml', '.yml')):
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False)
            elif file_path.endswith(('.ini', '.cfg')):
                self._save_ini(file_path, config)
            
            logger.info(f"Saved config '{name}' to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config '{name}': {e}")
            return False
    
    def _save_ini(self, file_path: str, config: Dict[str, Any]):
        """Save INI config file"""
        parser = configparser.ConfigParser()
        
        for section, values in config.items():
            parser.add_section(section)
            for key, value in values.items():
                parser.set(section, key, str(value))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            parser.write(f)
    
    def add_change_callback(self, name: str, callback: Callable[[str, Any], None]):
        """
        Add callback for config changes
        
        Callback signature: callback(key: str, value: Any)
        """
        if name not in self.callbacks:
            self.callbacks[name] = []
        
        self.callbacks[name].append(callback)
    
    def _trigger_callbacks(self, name: str, key: str, value: Any):
        """Trigger callbacks for config change"""
        if name in self.callbacks:
            for callback in self.callbacks[name]:
                try:
                    callback(key, value)
                except Exception as e:
                    logger.error(f"Error in config callback: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Get file modification time as simple hash"""
        try:
            return str(os.path.getmtime(file_path))
        except:
            return ""
    
    async def check_reload(self) -> List[str]:
        """Check and reload changed config files"""
        reloaded = []
        
        for name, file_path in self.config_files.items():
            try:
                current_hash = self._get_file_hash(file_path)
                
                if file_path in self.file_hashes and current_hash != self.file_hashes[file_path]:
                    # File changed, reload
                    old_config = self.configs.get(name, {}).copy()
                    
                    if self.load_config(name):
                        reloaded.append(name)
                        
                        # Find changes and trigger callbacks
                        new_config = self.configs[name]
                        self._detect_changes(name, old_config, new_config)
                        
            except Exception as e:
                logger.error(f"Error checking config '{name}': {e}")
        
        return reloaded
    
    def _detect_changes(self, name: str, old_config: dict, new_config: dict, prefix: str = ""):
        """Detect changes between configs and trigger callbacks"""
        all_keys = set(old_config.keys()) | set(new_config.keys())
        
        for key in all_keys:
            full_key = f"{prefix}.{key}" if prefix else key
            old_value = old_config.get(key)
            new_value = new_config.get(key)
            
            if old_value != new_value:
                if isinstance(new_value, dict) and isinstance(old_value, dict):
                    # Recurse into nested dicts
                    self._detect_changes(name, old_value, new_value, full_key)
                else:
                    # Value changed
                    self._trigger_callbacks(name, full_key, new_value)
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded configurations"""
        return self.configs.copy()
    
    def reload_all(self) -> List[str]:
        """Reload all config files"""
        reloaded = []
        
        for name in self.config_files:
            if self.load_config(name):
                reloaded.append(name)
        
        return reloaded