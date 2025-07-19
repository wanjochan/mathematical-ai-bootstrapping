"""Configuration management for CyberCorp Server."""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field, validator
from enum import Enum


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(default="sqlite:///cybercorp.db", description="Database URL")
    echo: bool = Field(default=False, description="Enable SQL query logging")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Maximum overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")


class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    reload: bool = Field(default=False, description="Enable auto-reload")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class SSLConfig(BaseModel):
    """SSL configuration."""
    enabled: bool = Field(default=False, description="Enable SSL")
    cert_file: Optional[str] = Field(None, description="SSL certificate file path")
    key_file: Optional[str] = Field(None, description="SSL private key file path")
    ca_file: Optional[str] = Field(None, description="SSL CA file path")


class AuthConfig(BaseModel):
    """Authentication configuration."""
    secret_key: str = Field(..., description="JWT secret key")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration")
    password_min_length: int = Field(default=8, description="Minimum password length")
    max_login_attempts: int = Field(default=5, description="Maximum login attempts")
    lockout_duration_minutes: int = Field(default=15, description="Account lockout duration")


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    enabled: bool = Field(default=True, description="Enable monitoring")
    interval: int = Field(default=1000, description="Monitoring interval in milliseconds")
    history_retention_days: int = Field(default=30, description="History retention period")
    alert_thresholds: Dict[str, float] = Field(
        default={
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
        },
        description="Alert thresholds"
    )
    enable_alerts: bool = Field(default=True, description="Enable alerting")


class WebSocketConfig(BaseModel):
    """WebSocket configuration."""
    enabled: bool = Field(default=True, description="Enable WebSocket server")
    max_connections: int = Field(default=100, description="Maximum concurrent connections")
    ping_interval: int = Field(default=20, description="Ping interval in seconds")
    ping_timeout: int = Field(default=10, description="Ping timeout in seconds")
    message_queue_size: int = Field(default=1000, description="Message queue size per connection")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    file_path: Optional[str] = Field(None, description="Log file path")
    max_file_size: int = Field(default=10485760, description="Maximum log file size in bytes")
    backup_count: int = Field(default=5, description="Number of backup log files")
    enable_console: bool = Field(default=True, description="Enable console logging")


class CORSConfig(BaseModel):
    """CORS configuration."""
    enabled: bool = Field(default=True, description="Enable CORS")
    allow_origins: List[str] = Field(default=["*"], description="Allowed origins")
    allow_methods: List[str] = Field(default=["*"], description="Allowed methods")
    allow_headers: List[str] = Field(default=["*"], description="Allowed headers")
    allow_credentials: bool = Field(default=True, description="Allow credentials")


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    enabled: bool = Field(default=True, description="Enable rate limiting")
    requests_per_minute: int = Field(default=100, description="Requests per minute limit")
    burst_size: int = Field(default=20, description="Burst size")
    auth_requests_per_minute: int = Field(default=5, description="Auth requests per minute")


class Config(BaseModel):
    """Main configuration model."""
    # Core settings
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Component configurations
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ssl: SSLConfig = Field(default_factory=SSLConfig)
    auth: AuthConfig = Field(..., description="Authentication configuration")

    # security is a core dependency, derived from auth settings
    @property
    def security(self) -> AuthConfig:
        return self.auth
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    websocket: WebSocketConfig = Field(default_factory=WebSocketConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    
    # Custom settings
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom configuration")
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed = ['development', 'testing', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'Environment must be one of: {allowed}')
        return v


class ConfigManager:
    """Configuration manager with hot reload support."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager."""
        self.config_path = config_path or self._get_default_config_path()
        self._config: Optional[Config] = None
        self._watchers: List[callable] = []
        
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        # Check environment variable first
        if config_path := os.getenv('CYBERCORP_CONFIG'):
            return config_path
            
        # Check common locations
        possible_paths = [
            'config.yaml',
            'config.yml',
            'config.json',
            'cybercorp_config.yaml',
            'cybercorp_config.yml',
            'cybercorp_config.json',
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
                
        # Default to config.yaml
        return 'config.yaml'
    
    def load_config(self) -> Config:
        """Load configuration from file."""
        if not Path(self.config_path).exists():
            # Create default configuration
            self._create_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.endswith('.json'):
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)
            
            # Merge with environment variables
            data = self._merge_env_vars(data)
            
            self._config = Config(**data)
            return self._config
            
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration from {self.config_path}: {e}")
    
    def _create_default_config(self):
        """Create default configuration file."""
        default_config = {
            'environment': 'development',
            'debug': True,
            'server': {
                'host': '0.0.0.0',
                'port': 8080,
                'reload': True,
                'debug': True,
            },
            'auth': {
                'secret_key': 'your-secret-key-change-this-in-production',
                'algorithm': 'HS256',
                'access_token_expire_minutes': 30,
                'refresh_token_expire_days': 7,
            },
            'monitoring': {
                'enabled': True,
                'interval': 1000,
            },
            'logging': {
                'level': 'INFO',
                'enable_console': True,
            }
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            if self.config_path.endswith('.json'):
                json.dump(default_config, f, indent=2)
            else:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
    
    def _merge_env_vars(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge environment variables into configuration."""
        env_mappings = {
            'CYBERCORP_HOST': ['server', 'host'],
            'CYBERCORP_PORT': ['server', 'port'],
            'CYBERCORP_DEBUG': ['debug'],
            'CYBERCORP_SECRET_KEY': ['auth', 'secret_key'],
            'CYBERCORP_DATABASE_URL': ['database', 'url'],
            'CYBERCORP_LOG_LEVEL': ['logging', 'level'],
        }
        
        for env_var, path in env_mappings.items():
            if value := os.getenv(env_var):
                # Navigate to the nested dictionary
                current = data
                for key in path[:-1]:
                    current = current.setdefault(key, {})
                
                # Convert value to appropriate type
                if path[-1] in ['port', 'workers']:
                    value = int(value)
                elif path[-1] in ['debug', 'reload', 'enabled']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                current[path[-1]] = value
        
        return data
    
    def get_config(self) -> Config:
        """Get current configuration."""
        if self._config is None:
            self.load_config()
        return self._config
    
    def reload_config(self) -> Config:
        """Reload configuration from file."""
        old_config = self._config
        new_config = self.load_config()
        
        # Notify watchers of configuration change
        for watcher in self._watchers:
            try:
                watcher(old_config, new_config)
            except Exception as e:
                print(f"Error in config watcher: {e}")
        
        return new_config
    
    def add_watcher(self, callback: callable):
        """Add configuration change watcher."""
        self._watchers.append(callback)
    
    def remove_watcher(self, callback: callable):
        """Remove configuration change watcher."""
        if callback in self._watchers:
            self._watchers.remove(callback)


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> Config:
    """Get current configuration."""
    return config_manager.get_config()


def reload_config() -> Config:
    """Reload configuration."""
    return config_manager.reload_config()