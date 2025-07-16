"""
Configuration management for CyberCorp Seed Server
"""

import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Server configuration
    host: str = "localhost"
    port: int = 8000
    
    # Environment
    environment: str = "development"  # development, production
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:8080"]
    
    # WebSocket
    websocket_ping_interval: int = 30  # seconds
    websocket_ping_timeout: int = 10   # seconds
    
    # Application
    app_name: str = "CyberCorp Seed Server"
    app_version: str = "0.1.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create global settings instance
settings = Settings() 