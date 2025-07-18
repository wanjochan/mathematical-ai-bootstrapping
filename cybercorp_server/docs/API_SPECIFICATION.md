# CyberCorp API Specification

## Overview
This document provides comprehensive API specifications for the CyberCorp client-server system, including REST endpoints, WebSocket protocols, and data formats.

## API Versioning
- **Current Version**: v1
- **Base URL**: `https://api.cybercorp.com/v1`
- **Version Header**: `X-API-Version: 1.0.0`
- **Deprecation Policy**: 6-month notice for breaking changes

## Authentication

### JWT Token
All API requests require a valid JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Token Refresh
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "refresh_token_here"
}
```

### Response
```json
{
  "access_token": "new_access_token",
  "refresh_token": "new_refresh_token",
  "expires_in": 3600
}
```

## REST API Endpoints

### Authentication Endpoints

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secure_password",
  "client_id": "desktop_client_123"
}
```

**Response:**
```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "expires_in": 3600,
  "token_type": "Bearer",
  "user": {
    "id": "user_123",
    "username": "user@example.com",
    "role": "admin"
  }
}
```

#### Logout
```http
POST /auth/logout
Authorization: Bearer <token>
```

### System Endpoints

#### Get System Information
```http
GET /system/info
```

**Response:**
```json
{
  "data": {
    "hostname": "DESKTOP-ABC123",
    "platform": "Windows 10 Pro",
    "architecture": "x64",
    "cpu_count": 8,
    "total_memory": 17179869184,
    "boot_time": "2024-01-01T08:00:00Z",
    "uptime": 86400,
    "python_version": "3.11.0",
    "client_version": "1.0.0"
  }
}
```

#### Get Current Metrics
```http
GET /system/metrics
```

**Query Parameters:**
- `format` (string): `json` or `prometheus` (default: json)
- `detailed` (boolean): Include detailed metrics (default: false)

**Response:**
```json
{
  "data": {
    "timestamp": "2024-01-01T12:00:00Z",
    "cpu": {
      "usage_percent": 45.2,
      "per_cpu": [40.1, 50.3, 35.7, 60.2],
      "frequency": 3200,
      "temperature": 65.5
    },
    "memory": {
      "total": 17179869184,
      "available": 6871947674,
      "used": 10307921510,
      "percent": 60.0
    },
    "disk": {
      "total": 499971072000,
      "used": 249985536000,
      "free": 249985536000,
      "percent": 50.0
    },
    "network": {
      "bytes_sent": 10485760,
      "bytes_recv": 20971520,
      "packets_sent": 1024,
      "packets_recv": 2048
    }
  }
}
```

#### Get Historical Data
```http
GET /system/history
```

**Query Parameters:**
- `start` (ISO8601): Start time
- `end` (ISO8601): End time
- `interval` (integer): Data aggregation interval in seconds
- `metrics` (array): Specific metrics to include

**Response:**
```json
{
  "data": {
    "metrics": [
      {
        "timestamp": "2024-01-01T11:00:00Z",
        "cpu_usage": 45.2,
        "memory_usage": 60.0,
        "disk_usage": 50.0
      },
      {
        "timestamp": "2024-01-01T11:01:00Z",
        "cpu_usage": 42.1,
        "memory_usage": 58.5,
        "disk_usage": 50.0
      }
    ],
    "pagination": {
      "total": 1440,
      "page": 1,
      "per_page": 100,
      "pages": 15
    }
  }
}
```

### Windows Endpoints

#### List Windows
```http
GET /windows
```

**Query Parameters:**
- `visible_only` (boolean): Show only visible windows (default: false)
- `active_only` (boolean): Show only active windows (default: false)
- `process_id` (integer): Filter by process ID
- `limit` (integer): Maximum results (default: 100, max: 1000)

**Response:**
```json
{
  "data": [
    {
      "id": "window_123456",
      "handle": 123456,
      "title": "Visual Studio Code",
      "class_name": "Chrome_WidgetWin_1",
      "process_id": 5678,
      "process_name": "Code.exe",
      "bounds": {
        "x": 100,
        "y": 100,
        "width": 1920,
        "height": 1080
      },
      "is_visible": true,
      "is_minimized": false,
      "is_maximized": false,
      "is_active": true,
      "opacity": 1.0,
      "z_order": 1
    }
  ],
  "pagination": {
    "total": 25,
    "page": 1,
    "per_page": 100
  }
}
```

#### Get Window Details
```http
GET /windows/{window_id}
```

**Response:**
```json
{
  "data": {
    "id": "window_123456",
    "handle": 123456,
    "title": "Visual Studio Code",
    "class_name": "Chrome_WidgetWin_1",
    "process_id": 5678,
    "process_name": "Code.exe",
    "bounds": {
      "x": 100,
      "y": 100,
      "width": 1920,
      "height": 1080
    },
    "is_visible": true,
    "is_minimized": false,
    "is_maximized": false,
    "is_active": true,
    "opacity": 1.0,
    "z_order": 1,
    "styles": ["WS_OVERLAPPEDWINDOW", "WS_VISIBLE"],
    "ex_styles": ["WS_EX_WINDOWEDGE"],
    "thread_id": 1234,
    "module_path": "C:\\Program Files\\Microsoft VS Code\\Code.exe",
    "icon_path": "C:\\Program Files\\Microsoft VS Code\\resources\\app\\resources\\win32\\code.ico"
  }
}
```

#### Control Window
```http
POST /windows/{window_id}/control
Content-Type: application/json

{
  "action": "focus",
  "parameters": {}
}
```

**Supported Actions:**
- `focus`: Focus the window
- `minimize`: Minimize the window
- `maximize`: Maximize the window
- `restore`: Restore the window
- `close`: Close the window
- `move`: Move window (requires x, y parameters)
- `resize`: Resize window (requires width, height parameters)

**Response:**
```json
{
  "success": true,
  "message": "Window focused successfully"
}
```

### Process Endpoints

#### List Processes
```http
GET /processes
```

**Query Parameters:**
- `status` (string): Filter by status (running, sleeping, stopped)
- `sort_by` (string): Sort field (cpu, memory, name)
- `sort_order` (string): Sort order (asc, desc)
- `limit` (integer): Maximum results (default: 100, max: 1000)

**Response:**
```json
{
  "data": [
    {
      "id": "process_5678",
      "pid": 5678,
      "name": "Code.exe",
      "exe": "C:\\Program Files\\Microsoft VS Code\\Code.exe",
      "cmdline": ["Code.exe", "--folder-uri", "file:///c%3A/dev/project"],
      "status": "running",
      "cpu_percent": 15.2,
      "memory_percent": 5.8,
      "create_time": "2024-01-01T08:30:00Z"
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "per_page": 100
  }
}
```

#### Get Process Details
```http
GET /processes/{process_id}
```

**Response:**
```json
{
  "data": {
    "id": "process_5678",
    "pid": 5678,
    "name": "Code.exe",
    "exe": "C:\\Program Files\\Microsoft VS Code\\Code.exe",
    "cmdline": ["Code.exe", "--folder-uri", "file:///c%3A/dev/project"],
    "status": "running",
    "create_time": "2024-01-01T08:30:00Z",
    "cpu_percent": 15.2,
    "memory_percent": 5.8,
    "memory_info": {
      "rss": 891289600,
      "vms": 2206203904,
      "shared": 45056000
    },
    "threads": 45,
    "open_files": [
      "C:\\dev\\project\\main.py",
      "C:\\dev\\project\\config.json"
    ],
    "connections": [
      {
        "fd": 1234,
        "family": "AF_INET",
        "type": "SOCK_STREAM",
        "laddr": ["127.0.0.1", 8080],
        "raddr": ["127.0.0.1", 12345],
        "status": "ESTABLISHED"
      }
    ]
  }
}
```

#### Control Process
```http
POST /processes/{process_id}/control
Content-Type: application/json

{
  "action": "terminate",
  "force": false
}
```

**Supported Actions:**
- `terminate`: Terminate the process
- `suspend`: Suspend the process
- `resume`: Resume the process
- `kill`: Force kill the process

**Response:**
```json
{
  "success": true,
  "message": "Process terminated successfully"
}
```

### Metrics Endpoints

#### Get CPU Metrics
```http
GET /metrics/cpu
```

**Query Parameters:**
- `start` (ISO8601): Start time
- `end` (ISO8601): End time
- `per_cpu` (boolean): Include per-CPU data (default: false)

**Response:**
```json
{
  "data": {
    "current": {
      "usage_percent": 45.2,
      "per_cpu": [40.1, 50.3, 35.7, 60.2],
      "frequency": 3200
    },
    "history": [
      {
        "timestamp": "2024-01-01T11:00:00Z",
        "usage_percent": 42.1,
        "per_cpu": [38.5, 45.2, 40.1, 55.3]
      }
    ]
  }
}
```

#### Get Memory Metrics
```http
GET /metrics/memory
```

**Response:**
```json
{
  "data": {
    "current": {
      "total": 17179869184,
      "available": 6871947674,
      "used": 10307921510,
      "percent": 60.0,
      "swap_total": 34359738368,
      "swap_used": 1073741824,
      "swap_percent": 3.1
    }
  }
}
```

### Configuration Endpoints

#### Get Configuration
```http
GET /config
```

**Response:**
```json
{
  "data": {
    "server": {
      "host": "0.0.0.0",
      "port": 8080,
      "ssl": {
        "enabled": true
      }
    },
    "monitoring": {
      "enabled": true,
      "interval": 1000
    }
  }
}
```

#### Update Configuration
```http
PUT /config
Content-Type: application/json

{
  "monitoring": {
    "interval": 2000
  }
}
```

#### Reload Configuration
```http
POST /config/reload
```

## WebSocket API

### Connection URL
```
wss://api.cybercorp.com/v1/ws
```

### Authentication
WebSocket connection requires JWT token in query parameter:
```
wss://api.cybercorp.com/v1/ws?token=<jwt_token>
```

### Message Format
```json
{
  "type": "message_type",
  "id": "unique_message_id",
  "timestamp": "2024-01-01T12:00:00Z",
  "payload": {}
}
```

### Client → Server Messages

#### Subscribe to Topics
```json
{
  "type": "subscribe",
  "id": "sub_123",
  "payload": {
    "topics": ["system.metrics", "system.windows", "system.processes"]
  }
}
```

#### Unsubscribe from Topics
```json
{
  "type": "unsubscribe",
  "id": "unsub_456",
  "payload": {
    "topics": ["system.windows"]
  }
}
```

#### Send Command
```json
{
  "type": "command",
  "id": "cmd_789",
  "payload": {
    "target": "window",
    "action": "focus",
    "parameters": {
      "window_id": "window_123456"
    }
  }
}
```

### Server → Client Messages

#### Data Update
```json
{
  "type": "data_update",
  "id": "update_123",
  "payload": {
    "topic": "system.metrics",
    "data": {
      "cpu": 45.2,
      "memory": 60.0,
      "disk": 50.0
    }
  }
}
```

#### Event Notification
```json
{
  "type": "event_notification",
  "id": "event_456",
  "payload": {
    "event_type": "window_created",
    "data": {
      "window_id": "window_789012",
      "title": "New Window",
      "process_id": 1234
    }
  }
}
```

#### Command Response
```json
{
  "type": "command_response",
  "id": "cmd_789",
  "payload": {
    "success": true,
    "message": "Window focused successfully",
    "data": {
      "window_id": "window_123456"
    }
  }
}
```

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "specific_field",
      "reason": "validation_failed"
    }
  }
}
```

### Error Codes
- `INVALID_TOKEN`: Authentication token is invalid or expired
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions
- `RESOURCE_NOT_FOUND`: Requested resource does not exist
- `VALIDATION_ERROR`: Request data validation failed
- `RATE_LIMIT_EXCEEDED`: API rate limit exceeded
- `INTERNAL_ERROR`: Internal server error

## Rate Limiting

### Limits
- **Authentication**: 5 requests per minute
- **API General**: 100 requests per minute
- **WebSocket**: 1000 messages per minute
- **File Uploads**: 10 MB per minute

### Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
X-RateLimit-RetryAfter: 60
```

## Pagination

### Query Parameters
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (default: 100, max: 1000)
- `cursor` (string): Cursor for next page

### Response Format
```json
{
  "data": [...],
  "pagination": {
    "total": 1000,
    "page": 1,
    "per_page": 100,
    "pages": 10,
    "has_next": true,
    "has_prev": false,
    "next_cursor": "eyJpZCI6MTAwLCJ0aW1lc3RhbXAiOiIyMDI0LTAxLTAxVDEyOjAwOjAwWiJ9"
  }
}
```

## Webhooks

### Webhook Registration
```http
POST /webhooks
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["system.metrics", "window.created", "process.terminated"],
  "secret": "webhook_secret"
}
```

### Webhook Payload
```json
{
  "event": "system.metrics",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "cpu": 45.2,
    "memory": 60.0
  }
}