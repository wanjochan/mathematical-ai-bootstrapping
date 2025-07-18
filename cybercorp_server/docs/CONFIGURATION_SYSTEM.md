# CyberCorp Configuration System

## Overview
The CyberCorp configuration system provides a flexible, environment-aware configuration management solution with hot reload capabilities for both server and client components.

## Architecture Principles
- **Environment-based**: Separate configurations for development, staging, and production
- **Hot Reload**: Configuration changes applied without restart
- **Validation**: Runtime configuration validation
- **Security**: Sensitive data encryption and secure storage
- **Versioning**: Configuration schema versioning and migration
- **Observability**: Configuration change tracking and audit logs

## Configuration Layers

### 1. Default Configuration
Base configuration with sensible defaults for all environments.

### 2. Environment Configuration
Environment-specific overrides (development, staging, production).

### 3. User Configuration
User-specific settings and preferences.

### 4. Runtime Configuration
Dynamic configuration updates via API or file watching.

## Configuration Schema

### Server Configuration Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "server": {
      "type": "object",
      "properties": {
        "host": {"type": "string", "default": "0.0.0.0"},
        "port": {"type": "integer", "default": 8080, "minimum": 1024, "maximum": 65535},
        "ssl": {
          "type": "object",
          "properties": {
            "enabled": {"type": "boolean", "default": true},
            "cert_path": {"type": "string"},
            "key_path": {"type": "string"},
            "ca_path": {"type": "string"}
          },
          "required": ["enabled"]
        },
        "workers": {"type": "integer", "default": 4, "minimum": 1, "maximum": 32},
        "timeout": {"type": "integer", "default": 30, "minimum": 5, "maximum": 300}
      },
      "required": ["host", "port", "ssl"]
    },
    "websocket": {
      "type": "object",
      "properties": {
        "enabled": {"type": "boolean", "default": true},
        "max_connections": {"type": "integer", "default": 1000, "minimum": 1, "maximum": 10000},
        "ping_interval": {"type": "integer", "default": 30, "minimum": 10, "maximum": 300},
        "pong_timeout": {"type": "integer", "default": 10, "minimum": 5, "maximum": 60},
        "compression": {"type": "boolean", "default": true},
        "max_message_size": {"type": "integer", "default": 1048576, "minimum": 1024, "maximum": 10485760}
      },
      "required": ["enabled"]
    },
    "database": {
      "type": "object",
      "properties": {
        "url": {"type": "string", "format": "uri"},
        "pool_size": {"type": "integer", "default": 20, "minimum": 5, "maximum": 100},
        "max_overflow": {"type": "integer", "default": 30, "minimum": 0, "maximum": 200},
        "pool_timeout": {"type": "integer", "default": 30, "minimum": 5, "maximum": 300},
        "pool_recycle": {"type": "integer", "default": 3600, "minimum": 300, "maximum": 86400}
      },
      "required": ["url"]
    },
    "security": {
      "type": "object",
      "properties": {
        "jwt": {
          "type": "object",
          "properties": {
            "secret_key": {"type": "string"},
            "algorithm": {"type": "string", "default": "HS256"},
            "access_token_expire_minutes": {"type": "integer", "default": 60, "minimum": 15, "maximum": 1440},
            "refresh_token_expire_days": {"type": "integer", "default": 7, "minimum": 1, "maximum": 30}
          },
          "required": ["secret_key"]
        },
        "rate_limiting": {
          "type": "object",
          "properties": {
            "enabled": {"type": "boolean", "default": true},
            "default_limit": {"type": "string", "default": "100/minute"},
            "storage_url": {"type": "string", "format": "uri"}
          },
          "required": ["enabled"]
        },
        "cors": {
          "type": "object",
          "properties": {
            "enabled": {"type": "boolean", "default": true},
            "allowed_origins": {"type": "array", "items": {"type": "string"}},
            "allowed_methods": {"type": "array", "items": {"type": "string"}},
            "allowed_headers": {"type": "array", "items": {"type": "string"}}
          },
          "required": ["enabled"]
        }
      },
      "required": ["jwt"]
    },
    "monitoring": {
      "type": "object",
      "properties": {
        "enabled": {"type": "boolean", "default": true},
        "interval": {"type": "integer", "default": 1000, "minimum": 100, "maximum": 10000},
        "data_retention_days": {"type": "integer", "default": 30, "minimum": 1, "maximum": 365},
        "aggregation_interval": {"type": "integer", "default": 300, "minimum": 60, "maximum": 3600},
        "cleanup_interval": {"type": "integer", "default": 3600, "minimum": 300, "maximum": 86400}
      },
      "required": ["enabled"]
    },
    "logging": {
      "type": "object",
      "properties": {
        "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "default": "INFO"},
        "format": {"type": "string", "default": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        "file_path": {"type": "string"},
        "max_file_size": {"type": "integer", "default": 10485760, "minimum": 1048576, "maximum": 104857600},
        "backup_count": {"type": "integer", "default": 5, "minimum": 1, "maximum": 50},
        "console": {"type": "boolean", "default": true}
      },
      "required": ["level"]
    }
  },
  "required": ["server", "websocket", "database", "security", "monitoring", "logging"]
}
```

### Client Configuration Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "server": {
      "type": "object",
      "properties": {
        "host": {"type": "string", "default": "localhost"},
        "port": {"type": "integer", "default": 8080, "minimum": 1, "maximum": 65535},
        "ssl": {"type": "boolean", "default": true},
        "timeout": {"type": "integer", "default": 30, "minimum": 5, "maximum": 300},
        "retry_attempts": {"type": "integer", "default": 3, "minimum": 0, "maximum": 10},
        "retry_delay": {"type": "integer", "default": 1, "minimum": 0, "maximum": 60}
      },
      "required": ["host", "port", "ssl"]
    },
    "monitoring": {
      "type": "object",
      "properties": {
        "enabled": {"type": "boolean", "default": true},
        "interval": {"type": "integer", "default": 1000, "minimum": 100, "maximum": 10000},
        "enabled_metrics": {
          "type": "array",
          "items": {"type": "string", "enum": ["cpu", "memory", "disk", "network", "processes", "windows"]},
          "default": ["cpu", "memory", "disk", "network"]
        },
        "window_tracking": {"type": "boolean", "default": true},
        "process_tracking": {"type": "boolean", "default": true},
        "user_activity_tracking": {"type": "boolean", "default": false},
        "screenshot_interval": {"type": "integer", "default": 0, "minimum": 0, "maximum": 3600}
      },
      "required": ["enabled"]
    },
    "ui": {
      "type": "object",
      "properties": {
        "theme": {"type": "string", "enum": ["light", "dark", "auto"], "default": "dark"},
        "refresh_rate": {"type": "integer", "default": 60, "minimum": 1, "maximum": 1440},
        "notifications": {"type": "boolean", "default": true},
        "auto_refresh": {"type": "boolean", "default": true},
        "window": {
          "type": "object",
          "properties": {
            "width": {"type": "integer", "default": 1200, "minimum": 800, "maximum": 3840},
            "height": {"type": "integer", "default": 800, "minimum": 600, "maximum": 2160},
            "x": {"type": "integer", "default": 100},
            "y": {"type": "integer", "default": 100},
            "always_on_top": {"type": "boolean", "default": false},
            "minimize_to_tray": {"type": "boolean", "default": true}
          }
        }
      },
      "required": ["theme", "refresh_rate"]
    },
    "security": {
      "type": "object",
      "properties": {
        "token_storage": {"type": "string", "enum": ["secure_storage", "file", "memory"], "default": "secure_storage"},
        "auto_refresh": {"type": "boolean", "default": true},
        "refresh_before_expiry": {"type": "integer", "default": 300, "minimum": 60, "maximum": 3600},
        "certificate_validation": {"type": "boolean", "default": true},
        "certificate_pinning": {"type": "boolean", "default": false},
        "encryption": {
          "type": "object",
          "properties": {
            "local_storage": {"type": "boolean", "default": true},
            "cache_encryption": {"type": "boolean", "default": true},
            "sensitive_data": {"type": "boolean", "default": true}
          }
        }
      },
      "required": ["token_storage", "auto_refresh"]
    },
    "logging": {
      "type": "object",
      "properties": {
        "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "default": "INFO"},
        "file_path": {"type": "string", "default": "cybercorp_client.log"},
        "max_file_size": {"type": "integer", "default": 5242880, "minimum": 1048576, "maximum": 52428800},
        "backup_count": {"type": "integer", "default": 3, "minimum": 1, "maximum": 20},
        "console": {"type": "boolean", "default": false}
      },
      "required": ["level"]
    }
  },
  "required": ["server", "monitoring", "ui", "security", "logging"]
}
```

## Configuration Management

### Configuration Sources (Priority Order)
1. **Environment Variables** (CYBERCORP_*)
2. **Command Line Arguments**
3. **User Configuration File** (~/.cybercorp/config.json)
4. **Environment Configuration File** (config/development.json)
5. **Default Configuration** (config/default.json)

### Environment Variables
```bash
# Server
CYBERCORP_SERVER_HOST=0.0.0.0
CYBERCORP_SERVER_PORT=8080
CYBERCORP_SERVER_SSL_ENABLED=true

# Database
CYBERCORP_DATABASE_URL=postgresql://user:pass@localhost/cybercorp

# Security
CYBERCORP_JWT_SECRET=your-secret-key
CYBERCORP_RATE_LIMIT_ENABLED=true

# Client
CYBERCORP_CLIENT_SERVER_HOST=localhost
CYBERCORP_CLIENT_SERVER_PORT=8080
CYBERCORP_CLIENT_THEME=dark
```

### Configuration Files Structure
```
config/
├── default.json              # Base defaults
├── development.json          # Development overrides
├── staging.json              # Staging overrides
├── production.json           # Production overrides
├── security.json             # Security settings
├── server.json               # Server-specific
├── client.json               # Client-specific
└── user/                     # User-specific configs
    ├── alice.json
    └── bob.json
```

## Hot Reload Architecture

### File Watching
- **Watch Paths**: config/, ~/.cybercorp/
- **File Types**: .json, .yaml, .toml
- **Debounce**: 500ms to prevent rapid reloads
- **Validation**: Schema validation before applying changes

### Reload Process
1. **Detection**: File change detected
2. **Validation**: New configuration validated against schema
3. **Backup**: Current configuration backed up
4. **Apply**: New configuration applied atomically
5. **Notify**: Components notified of changes
6. **Rollback**: Automatic rollback on validation failure

### Reloadable Components
- **Server Settings**: Port, SSL, workers
- **Database Settings**: Pool size, timeout
- **Security Settings**: Rate limits, CORS
- **Monitoring Settings**: Intervals, retention
- **Logging Settings**: Level, format
- **Client Settings**: Server connection, UI preferences

### Configuration Events
```json
{
  "event": "config_changed",
  "timestamp": "2024-01-01T12:00:00Z",
  "changes": {
    "server.port": {"old": 8080, "new": 8081},
    "monitoring.interval": {"old": 1000, "new": 500}
  },
  "source": "file_watch",
  "validation": {"success": true, "errors": []}
}
```

## Configuration API

### Server Endpoints
- `GET /api/v1/config` - Get current configuration
- `PUT /api/v1/config` - Update configuration
- `POST /api/v1/config/reload` - Trigger configuration reload
- `GET /api/v1/config/schema` - Get configuration schema

### Client Methods
- `client.config.get(key)` - Get configuration value
- `client.config.set(key, value)` - Set configuration value
- `client.config.reload()` - Reload configuration from files
- `client.config.watch(key, callback)` - Watch for changes

## Validation and Migration

### Schema Validation
- **Runtime Validation**: All configuration validated at startup
- **Hot Reload Validation**: Changes validated before application
- **Error Handling**: Detailed error messages with suggestions
- **Logging**: Configuration change audit trail

### Configuration Migration
- **Version Detection**: Automatic schema version detection
- **Migration Scripts**: Automated migration between versions
- **Backward Compatibility**: Graceful handling of old configurations
- **Deprecation Warnings**: Advance notice of breaking changes

### Example Migration
```json
{
  "version": "1.0.0",
  "migrations": [
    {
      "from": "0.9.0",
      "to": "1.0.0",
      "changes": [
        {
          "type": "rename",
          "from": "server.ssl_enabled",
          "to": "server.ssl.enabled"
        },
        {
          "type": "default",
          "key": "monitoring.user_activity_tracking",
          "value": false
        }
      ]
    }
  ]
}