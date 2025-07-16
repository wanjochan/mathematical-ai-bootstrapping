# CyberCorp Seed Server

FastAPI-based seed server for CyberCorp system development, providing web API and WebSocket capabilities with hot-reload support.

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **WebSocket Support**: Real-time bidirectional communication
- **Hot Reload**: Automatic server restart during development
- **System Monitoring**: Health checks and system information endpoints
- **Structured Logging**: Comprehensive logging to console and files
- **CORS Support**: Cross-Origin Resource Sharing for web clients
- **Configuration Management**: Environment-based configuration

## Quick Start

### Installation

1. Install dependencies:
```bash
cd seed
pip install -r requirements.txt
```

2. Copy environment configuration:
```bash
cp .env.example .env
```

3. Run the server:
```bash
# Development mode with hot reload
python -m seed.main

# Or using uvicorn directly
uvicorn seed.main:app --reload --host localhost --port 8000
```

### API Endpoints

- `GET /` - Root endpoint with server information
- `GET /api/v1/health` - Health check with system metrics
- `GET /api/v1/status` - Server status and configuration
- `GET /api/v1/info` - Detailed system information
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

### WebSocket Endpoints

- `WS /ws/connect` - Main WebSocket connection for real-time communication
- `WS /ws/test` - Test WebSocket endpoint for development

## WebSocket Message Types

### Client to Server

```json
{
  "type": "ping",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

```json
{
  "type": "broadcast",
  "message": "Hello everyone!"
}
```

```json
{
  "type": "echo",
  "message": "Test message"
}
```

```json
{
  "type": "status"
}
```

### Server to Client

```json
{
  "type": "welcome",
  "message": "Connected to CyberCorp Seed Server",
  "timestamp": "2025-01-27T10:00:00Z",
  "connection_id": 123456789
}
```

```json
{
  "type": "pong",
  "timestamp": "2025-01-27T10:00:00Z",
  "original_timestamp": "2025-01-27T10:00:00Z"
}
```

## Configuration

The server uses environment variables for configuration. Copy `.env.example` to `.env` and modify as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | localhost | Server host address |
| `PORT` | 8000 | Server port |
| `ENVIRONMENT` | development | Environment mode (development/production) |
| `LOG_LEVEL` | INFO | Logging level |
| `CORS_ORIGINS` | http://localhost:3000,http://localhost:8080 | Allowed CORS origins |

## Development

### Project Structure

```
seed/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application entry point
├── config.py                # Configuration management
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── .env.example            # Environment variables example
├── routers/                # API route handlers
│   ├── __init__.py
│   ├── api.py              # REST API endpoints
│   └── websocket.py        # WebSocket endpoints
└── core/                   # Core utilities
    ├── __init__.py
    ├── websocket_manager.py # WebSocket connection management
    └── logging_config.py   # Logging configuration
```

### Hot Reload

In development mode, the server automatically reloads when code changes are detected. This is enabled by default when `ENVIRONMENT=development`.

### Logging

Logs are written to both console and files in the `logs/` directory. Log files are rotated daily with the format `seed_server_YYYYMMDD.log`.

## Testing

### Manual Testing

1. **Health Check**:
```bash
curl http://localhost:8000/api/v1/health
```

2. **WebSocket Connection**:
Use a WebSocket client or browser console:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/connect');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
ws.send(JSON.stringify({type: 'ping', timestamp: new Date().toISOString()}));
```

## Extending the Server

This seed server is designed to be extended for the full CyberCorp system. Future extensions may include:

- AI employee management endpoints
- Model configuration APIs
- Task scheduling and monitoring
- Integration with AI development tools
- Advanced WebSocket message routing

## License

Part of the CyberCorp project - Mathematical AI Bootstrapping system. 