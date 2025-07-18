"""Configuration service module for CyberCorp Server."""

from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import os
import json
import yaml
from pathlib import Path
import asyncio

from ..logging_config import get_logger
from ..config import get_settings

logger = get_logger(__name__)


class ConfigService:
    """Service for configuration management operations."""
    
    def __init__(self):
        """Initialize the configuration service."""
        self.settings = get_settings()
        self.config_dir = Path(self.settings.config_dir)
        self.config_cache = {}
        self.watchers = {}
        self.change_callbacks = []
    
    async def initialize(self):
        """Initialize the service."""
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load all configurations
        await self.load_all_configs()
        
        logger.info("Configuration service initialized")
    
    async def shutdown(self):
        """Shutdown the service."""
        # Stop all file watchers
        for config_name, watcher in self.watchers.items():
            watcher.cancel()
        
        logger.info("Configuration service shutting down")
    
    async def load_all_configs(self) -> Dict[str, Any]:
        """Load all configuration files."""
        try:
            # Clear cache
            self.config_cache = {}
            
            # Get all config files
            for file_path in self.config_dir.glob("*.json"):
                config_name = file_path.stem
                await self.load_config(config_name)
            
            for file_path in self.config_dir.glob("*.yaml"):
                config_name = file_path.stem
                await self.load_config(config_name)
            
            for file_path in self.config_dir.glob("*.yml"):
                config_name = file_path.stem
                await self.load_config(config_name)
            
            return self.config_cache
        except Exception as e:
            logger.error(f"Error loading all configs: {e}")
            raise
    
    async def load_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Load a specific configuration file."""
        try:
            # Check for JSON file
            json_path = self.config_dir / f"{config_name}.json"
            yaml_path = self.config_dir / f"{config_name}.yaml"
            yml_path = self.config_dir / f"{config_name}.yml"
            
            config_data = None
            config_path = None
            
            if json_path.exists():
                with open(json_path, "r") as f:
                    config_data = json.load(f)
                config_path = json_path
            elif yaml_path.exists():
                with open(yaml_path, "r") as f:
                    config_data = yaml.safe_load(f)
                config_path = yaml_path
            elif yml_path.exists():
                with open(yml_path, "r") as f:
                    config_data = yaml.safe_load(f)
                config_path = yml_path
            else:
                logger.warning(f"Config file for '{config_name}' not found")
                return None
            
            # Store in cache
            self.config_cache[config_name] = {
                "data": config_data,
                "path": str(config_path),
                "last_modified": datetime.fromtimestamp(config_path.stat().st_mtime).isoformat(),
                "format": config_path.suffix[1:]  # Remove the dot
            }
            
            # Start file watcher if not already watching
            if config_name not in self.watchers:
                self.watchers[config_name] = asyncio.create_task(
                    self._watch_config_file(config_name, config_path)
                )
            
            logger.info(f"Loaded config '{config_name}' from {config_path}")
            return config_data
        except Exception as e:
            logger.error(f"Error loading config '{config_name}': {e}")
            raise
    
    async def get_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Get a configuration from cache or load it if not cached."""
        try:
            # Check cache
            if config_name in self.config_cache:
                return self.config_cache[config_name]["data"]
            
            # Load config
            return await self.load_config(config_name)
        except Exception as e:
            logger.error(f"Error getting config '{config_name}': {e}")
            raise
    
    async def get_config_value(self, config_name: str, key_path: str, default_value: Any = None) -> Any:
        """Get a specific value from a configuration using dot notation for nested keys."""
        try:
            # Get config
            config = await self.get_config(config_name)
            if not config:
                return default_value
            
            # Split key path
            keys = key_path.split('.')
            
            # Navigate to the value
            value = config
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default_value
            
            return value
        except Exception as e:
            logger.error(f"Error getting config value '{config_name}.{key_path}': {e}")
            raise
    
    async def set_config(self, config_name: str, config_data: Dict[str, Any], format: str = "json") -> bool:
        """Set a configuration and save it to file."""
        try:
            # Determine file path
            if format.lower() not in ["json", "yaml", "yml"]:
                raise ValueError(f"Unsupported config format: {format}")
            
            if format.lower() == "yml":
                format = "yaml"
            
            config_path = self.config_dir / f"{config_name}.{format}"
            
            # Save to file
            with open(config_path, "w") as f:
                if format.lower() == "json":
                    json.dump(config_data, f, indent=2)
                else:  # yaml
                    yaml.dump(config_data, f, default_flow_style=False)
            
            # Update cache
            self.config_cache[config_name] = {
                "data": config_data,
                "path": str(config_path),
                "last_modified": datetime.utcnow().isoformat(),
                "format": format
            }
            
            # Start file watcher if not already watching
            if config_name not in self.watchers:
                self.watchers[config_name] = asyncio.create_task(
                    self._watch_config_file(config_name, config_path)
                )
            
            logger.info(f"Saved config '{config_name}' to {config_path}")
            
            # Notify change listeners
            await self._notify_config_changed(config_name, config_data)
            
            return True
        except Exception as e:
            logger.error(f"Error setting config '{config_name}': {e}")
            raise
    
    async def set_config_value(self, config_name: str, key_path: str, value: Any) -> bool:
        """Set a specific value in a configuration using dot notation for nested keys."""
        try:
            # Get config
            config = await self.get_config(config_name)
            if not config:
                config = {}
            
            # Split key path
            keys = key_path.split('.')
            
            # Navigate to the parent of the value
            current = config
            for i, key in enumerate(keys[:-1]):
                if key not in current or not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]
            
            # Set the value
            current[keys[-1]] = value
            
            # Get format from cache or default to json
            format = "json"
            if config_name in self.config_cache:
                format = self.config_cache[config_name]["format"]
            
            # Save config
            return await self.set_config(config_name, config, format)
        except Exception as e:
            logger.error(f"Error setting config value '{config_name}.{key_path}': {e}")
            raise
    
    async def delete_config(self, config_name: str) -> bool:
        """Delete a configuration file."""
        try:
            # Check if config exists in cache
            if config_name not in self.config_cache:
                return False
            
            # Get file path
            config_path = Path(self.config_cache[config_name]["path"])
            
            # Delete file
            if config_path.exists():
                os.remove(config_path)
            
            # Stop file watcher
            if config_name in self.watchers:
                self.watchers[config_name].cancel()
                del self.watchers[config_name]
            
            # Remove from cache
            del self.config_cache[config_name]
            
            logger.info(f"Deleted config '{config_name}'")
            
            # Notify change listeners
            await self._notify_config_changed(config_name, None)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting config '{config_name}': {e}")
            raise
    
    async def list_configs(self) -> List[Dict[str, Any]]:
        """List all available configurations."""
        try:
            configs = []
            for config_name, config_info in self.config_cache.items():
                configs.append({
                    "name": config_name,
                    "path": config_info["path"],
                    "format": config_info["format"],
                    "last_modified": config_info["last_modified"]
                })
            return configs
        except Exception as e:
            logger.error(f"Error listing configs: {e}")
            raise
    
    async def register_change_callback(self, callback) -> None:
        """Register a callback to be called when a configuration changes."""
        self.change_callbacks.append(callback)
    
    async def _notify_config_changed(self, config_name: str, config_data: Optional[Dict[str, Any]]) -> None:
        """Notify all registered callbacks about a configuration change."""
        for callback in self.change_callbacks:
            try:
                await callback(config_name, config_data)
            except Exception as e:
                logger.error(f"Error in config change callback: {e}")
    
    async def _watch_config_file(self, config_name: str, config_path: Path) -> None:
        """Watch a configuration file for changes."""
        try:
            last_modified = config_path.stat().st_mtime
            
            while True:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                if not config_path.exists():
                    # File was deleted
                    logger.info(f"Config file '{config_name}' was deleted")
                    if config_name in self.config_cache:
                        del self.config_cache[config_name]
                        await self._notify_config_changed(config_name, None)
                    break
                
                current_modified = config_path.stat().st_mtime
                if current_modified > last_modified:
                    # File was modified
                    logger.info(f"Config file '{config_name}' was modified")
                    last_modified = current_modified
                    
                    # Reload config
                    await self.load_config(config_name)
                    
                    # Notify change listeners
                    if config_name in self.config_cache:
                        await self._notify_config_changed(config_name, self.config_cache[config_name]["data"])
        except asyncio.CancelledError:
            # Watcher was cancelled
            logger.info(f"Config watcher for '{config_name}' stopped")
        except Exception as e:
            logger.error(f"Error watching config file '{config_name}': {e}")


# Singleton instance
config_service = ConfigService()