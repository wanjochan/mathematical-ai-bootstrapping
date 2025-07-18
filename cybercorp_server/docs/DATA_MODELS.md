# CyberCorp Data Models Specification

## Overview
This document defines the data models for windows, processes, system metrics, and related entities used across the CyberCorp client-server system.

## System Models

### SystemInfo
Represents overall system information and capabilities.

```json
{
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
```

**Fields:**
- `hostname` (string): System hostname
- `platform` (string): Operating system name and version
- `architecture` (string): System architecture (x86, x64, ARM)
- `cpu_count` (integer): Number of CPU cores
- `total_memory` (integer): Total system memory in bytes
- `boot_time` (ISO8601): System boot timestamp
- `uptime` (integer): System uptime in seconds
- `python_version` (string): Python runtime version
- `client_version` (string): CyberCorp client version

### SystemMetrics
Real-time system performance metrics.

```json
{
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
    "percent": 60.0,
    "swap_total": 34359738368,
    "swap_used": 1073741824,
    "swap_percent": 3.1
  },
  "disk": {
    "total": 499971072000,
    "used": 249985536000,
    "free": 249985536000,
    "percent": 50.0,
    "partitions": [
      {
        "device": "C:\\",
        "mountpoint": "C:\\",
        "fstype": "NTFS",
        "total": 499971072000,
        "used": 249985536000,
        "free": 249985536000,
        "percent": 50.0
      }
    ]
  },
  "network": {
    "bytes_sent": 10485760,
    "bytes_recv": 20971520,
    "packets_sent": 1024,
    "packets_recv": 2048,
    "errin": 0,
    "errout": 0,
    "dropin": 0,
    "dropout": 0,
    "interfaces": [
      {
        "name": "Ethernet",
        "bytes_sent": 10485760,
        "bytes_recv": 20971520,
        "speed": 1000000000,
        "mtu": 1500
      }
    ]
  }
}
```

## Window Models

### WindowInfo
Represents a single window/application instance.

```json
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
  "z_order": 1,
  "styles": ["WS_OVERLAPPEDWINDOW", "WS_VISIBLE"],
  "ex_styles": ["WS_EX_WINDOWEDGE"],
  "thread_id": 1234,
  "module_path": "C:\\Program Files\\Microsoft VS Code\\Code.exe",
  "icon_path": "C:\\Program Files\\Microsoft VS Code\\resources\\app\\resources\\win32\\code.ico"
}
```

**Fields:**
- `id` (string): Unique window identifier
- `handle` (integer): Native window handle
- `title` (string): Window title text
- `class_name` (string): Window class name
- `process_id` (integer): Associated process ID
- `process_name` (string): Associated process executable name
- `bounds` (object): Window position and dimensions
- `is_visible` (boolean): Window visibility state
- `is_minimized` (boolean): Minimized state
- `is_maximized` (boolean): Maximized state
- `is_active` (boolean): Active/focused state
- `opacity` (float): Window transparency (0.0-1.0)
- `z_order` (integer): Z-order position
- `styles` (array): Window style flags
- `ex_styles` (array): Extended window style flags
- `thread_id` (integer): Associated thread ID
- `module_path` (string): Full path to executable
- `icon_path` (string): Path to window icon

### WindowStateChange
Represents a window state change event.

```json
{
  "window_id": "window_123456",
  "event_type": "focus",
  "previous_state": {
    "is_active": false,
    "bounds": {"x": 100, "y": 100, "width": 1920, "height": 1080}
  },
  "current_state": {
    "is_active": true,
    "bounds": {"x": 100, "y": 100, "width": 1920, "height": 1080}
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Process Models

### ProcessInfo
Represents a running process.

```json
{
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
    "shared": 45056000,
    "text": 4096,
    "lib": 0,
    "data": 1073741824,
    "dirty": 0
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
  ],
  "cwd": "C:\\dev\\project",
  "username": "user",
  "nice": 0,
  "ionice": {
    "ioclass": "IOPRIO_CLASS_NONE",
    "value": 0
  },
  "num_ctx_switches": {
    "voluntary": 1234,
    "involuntary": 567
  },
  "num_threads": 45,
  "cpu_affinity": [0, 1, 2, 3, 4, 5, 6, 7],
  "memory_maps": [
    {
      "path": "C:\\Windows\\System32\\ntdll.dll",
      "rss": 204800,
      "size": 2048000,
      "pss": 102400,
      "shared_clean": 102400,
      "shared_dirty": 0,
      "private_clean": 102400,
      "private_dirty": 0,
      "referenced": 204800,
      "anonymous": 0,
      "swap": 0
    }
  ]
}
```

### ProcessEvent
Represents a process lifecycle event.

```json
{
  "process_id": "process_5678",
  "event_type": "created",
  "process_info": { ... },
  "parent_pid": 1234,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## User Activity Models

### UserActivity
Represents user interaction events.

```json
{
  "id": "activity_789",
  "type": "mouse_click",
  "timestamp": "2024-01-01T12:00:00Z",
  "window_id": "window_123456",
  "process_id": "process_5678",
  "details": {
    "x": 500,
    "y": 300,
    "button": "left",
    "double_click": false
  }
}
```

## Configuration Models

### ClientConfig
Client-side configuration.

```json
{
  "server": {
    "host": "localhost",
    "port": 8080,
    "ssl": true,
    "timeout": 30
  },
  "monitoring": {
    "interval": 1000,
    "enabled_metrics": ["cpu", "memory", "disk", "network"],
    "window_tracking": true,
    "process_tracking": true,
    "user_activity_tracking": false
  },
  "ui": {
    "theme": "dark",
    "refresh_rate": 60,
    "notifications": true,
    "auto_refresh": true
  },
  "security": {
    "token_refresh_interval": 3600,
    "encryption_enabled": true,
    "certificate_validation": true
  }
}
```

### ServerConfig
Server-side configuration.

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "ssl_cert": "/path/to/cert.pem",
    "ssl_key": "/path/to/key.pem"
  },
  "security": {
    "jwt_secret": "secret_key",
    "jwt_expiry": 86400,
    "rate_limit": {
      "requests_per_minute": 100,
      "burst_limit": 200
    },
    "cors_origins": ["https://localhost:3000"]
  },
  "database": {
    "url": "postgresql://user:pass@localhost/cybercorp",
    "pool_size": 20,
    "max_overflow": 30
  },
  "monitoring": {
    "data_retention_days": 30,
    "aggregation_interval": 300,
    "cleanup_interval": 3600
  }
}
```

## Validation Rules

### System Metrics
- CPU usage: 0.0 - 100.0
- Memory usage: 0 - total_memory
- Disk usage: 0 - total_disk
- Temperature: -50.0 - 150.0

### Window Properties
- Position: x, y >= -32768 and <= 32767
- Size: width, height >= 0 and <= 32767
- Opacity: 0.0 - 1.0
- Z-order: 1 - 32767

### Process Properties
- PID: 1 - 2147483647
- CPU percent: 0.0 - 100.0 * cpu_count
- Memory percent: 0.0 - 100.0
- Nice value: -20 - 19 (Unix), 0 - 6 (Windows)

## Data Serialization

### JSON Schema
All models include JSON Schema for validation:
- Draft 7 compatible
- Additional properties: false
- Required fields explicitly marked

### Binary Formats
For high-frequency data:
- MessagePack for WebSocket messages
- Protocol Buffers for bulk data transfer
- Compression: gzip (level 6) for payloads > 1KB

### Time Handling
- All timestamps: ISO 8601 format with timezone
- UTC preferred for server-side storage
- Local timezone for client display
- Millisecond precision for events