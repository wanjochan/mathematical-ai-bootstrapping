# CyberCorp Communication Protocol Specification

## Overview
This document defines the communication protocol between CyberCorp clients and server, utilizing WebSocket for real-time updates and REST for standard operations.

## Protocol Stack
- **Transport Layer**: TCP over TLS 1.3
- **Application Layer**: WebSocket (RFC 6455) + REST (HTTP/2)
- **Message Format**: JSON with schema validation
- **Authentication**: JWT (JSON Web Tokens)
- **Compression**: gzip for large payloads

## WebSocket Protocol

### Connection URL
```
wss://server:port/ws/v1
```

### Message Structure
```json
{
  "type": "message_type",
  "id": "unique_message_id",
  "timestamp": "2024-01-01T00:00:00Z",
  "payload": { ... },
  "auth": {
    "token": "jwt_token",
    "client_id": "client_identifier"
  }
}
```

### Message Types

#### Client → Server
- `subscribe`: Subscribe to system events
- `unsubscribe`: Unsubscribe from system events
- `command`: Execute system command
- `ping`: Connection heartbeat

#### Server → Client
- `data_update`: Real-time system data
- `event_notification`: System events
- `command_response`: Command execution result
- `pong`: Connection heartbeat response
- `error`: Error notifications

### Subscription Topics
- `system.metrics`: CPU, memory, disk usage
- `system.windows`: Window state changes
- `system.processes`: Process lifecycle events
- `system.network`: Network activity
- `user.activity`: User interaction events

### Example WebSocket Flow
```json
// Client subscription
{
  "type": "subscribe",
  "id": "sub_123",
  "payload": {
    "topics": ["system.metrics", "system.windows"]
  }
}

// Server data update
{
  "type": "data_update",
  "id": "update_456",
  "payload": {
    "topic": "system.metrics",
    "data": {
      "cpu": 45.2,
      "memory": 67.8,
      "disk": 23.1
    }
  }
}
```

## REST API Specification

### Base URL
```
https://server:port/api/v1
```

### Authentication
- **Header**: `Authorization: Bearer <jwt_token>`
- **Token Expiry**: 24 hours
- **Refresh**: POST `/auth/refresh`

### Endpoints

#### System Information
- `GET /system/info` - Get system overview
- `GET /system/metrics` - Get current metrics
- `GET /system/history` - Get historical data

#### Windows Management
- `GET /windows` - List all windows
- `GET /windows/{id}` - Get window details
- `POST /windows/{id}/focus` - Focus window
- `POST /windows/{id}/close` - Close window
- `POST /windows/{id}/minimize` - Minimize window
- `POST /windows/{id}/maximize` - Maximize window

#### Process Management
- `GET /processes` - List all processes
- `GET /processes/{id}` - Get process details
- `POST /processes/{id}/terminate` - Terminate process
- `POST /processes/{id}/suspend` - Suspend process
- `POST /processes/{id}/resume` - Resume process

#### Metrics & Analytics
- `GET /metrics/cpu` - CPU usage data
- `GET /metrics/memory` - Memory usage data
- `GET /metrics/disk` - Disk usage data
- `GET /metrics/network` - Network usage data
- `GET /analytics/summary` - System summary

### Response Format
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0"
  }
}
```

### Error Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { ... }
  }
}
```

## Rate Limiting
- **WebSocket**: 100 messages per minute per client
- **REST API**: 
  - GET: 100 requests per minute
  - POST/PUT/DELETE: 50 requests per minute

## Security Considerations
- All communications encrypted with TLS 1.3
- JWT tokens with 24-hour expiry
- Rate limiting per IP and user
- Input validation and sanitization
- CORS protection for web clients
- WebSocket origin validation