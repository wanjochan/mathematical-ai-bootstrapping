# CyberCorp Node - Advanced Remote Control System

CyberCorp Node is a sophisticated remote control system designed for Windows environments, providing robust client-server architecture for remote computer control and automation.

## Features

### Core Capabilities
- **Remote Control**: Full control of Windows applications through WebSocket connection
- **VSCode Integration**: Specialized support for Visual Studio Code automation
- **Screenshot Capture**: Real-time screen capture with base64 encoding
- **Window Management**: Enumerate, activate, and control windows
- **Process Monitoring**: Track and manage system processes
- **UI Automation**: Deep UI element inspection and interaction

### Advanced Features
- **Hot Reload**: Dynamic code updates without restart
- **Health Monitoring**: Real-time system health tracking
- **Enhanced Logging**: Comprehensive logging with rotation and remote viewing
- **Fault Tolerance**: Automatic reconnection, timeout handling, and crash recovery
- **Unified Response Format**: Consistent API responses for easy integration

### Security & Reliability
- **Command Timeout**: Configurable timeout for all commands
- **Exponential Backoff**: Smart reconnection strategy
- **Process Watchdog**: Automatic restart on crash
- **Resource Monitoring**: CPU, memory, and network usage tracking

## Architecture

```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│   Control CLI   │ ◄─────────────────► │  CyberCorp      │
│   (admin.py)    │                     │  Server         │
└─────────────────┘                     │  (server.py)    │
                                        └────────┬────────┘
                                                 │
                                        WebSocket│
                                                 │
                                        ┌────────▼────────┐
                                        │  CyberCorp      │
                                        │  Client         │
                                        │  (client.py)    │
                                        └─────────────────┘
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd cybercorp_node
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure settings** (optional):
   Edit `config.ini` to customize:
   - Server host/port
   - Reconnection intervals
   - Heartbeat settings
   - Feature toggles

## Usage

### 1. Start the Server
```bash
python server.py --port 9998
```

### 2. Start the Client
On the target machine:
```bash
python client.py
```

The client will automatically connect to the server and register itself.

### 3. Control via Admin CLI
```bash
python admin.py --host localhost --port 9998
```

## Command Reference

### Window Operations
- `get_windows` - List all visible windows
- `activate_window` - Bring VSCode to foreground
- `get_window_content` - Extract window UI structure
- `get_window_uia_structure` - Deep UI automation tree

### Input Control
- `send_keys` - Send keyboard input
- `send_mouse_click` - Click at coordinates
- `mouse_drag` - Drag mouse between points
- `vscode_type_text` - Type text in VSCode
- `vscode_send_command` - Execute VSCode command

### System Information
- `get_system_info` - System details
- `get_processes` - Running processes
- `take_screenshot` - Capture screen
- `get_screen_size` - Display dimensions

### Health & Monitoring
- `health_status` - Get health metrics
- `get_logs` - Retrieve logs
- `set_log_level` - Change log verbosity
- `get_log_stats` - Log statistics

### Hot Reload
- `hot_reload` - Manage hot reload features
  - `action: status` - Get reload stats
  - `action: reload_module` - Reload specific module
  - `action: reload_config` - Reload configuration

### System Control
- `restart_client` - Remotely restart the client
  - `delay` - Seconds before restart (default: 3)
  - `use_watchdog` - Use watchdog for clean restart (default: true)
  - `reason` - Reason for restart

## Response Format

All commands return a unified response format:

```json
{
  "success": true,
  "timestamp": "2024-01-01T12:00:00",
  "error": null,
  "data": {
    // Command-specific data
  },
  "message": "Optional descriptive message",
  "metadata": {
    "command": "command_name",
    "execution_time": 0.123
  }
}
```

Error responses:
```json
{
  "success": false,
  "timestamp": "2024-01-01T12:00:00",
  "error": {
    "message": "Error description",
    "type": "ErrorType",
    "code": "ERROR_CODE",
    "details": {}
  },
  "data": null
}
```

## Configuration

### config.ini
```ini
[server]
host = 0.0.0.0
port = 9998
heartbeat_interval = 30
command_timeout = 60

[client]
server_host = localhost
server_port = 9998
reconnect_interval = 5
heartbeat_interval = 30
enable_hot_reload = true
enable_health_monitor = true
```

### Environment Variables
- `CYBERCORP_SERVER` - Override server URL
- `USERNAME` - Client identification

## Testing

Run the test suite:

```bash
# Test hot reload functionality
python test_hot_reload.py

# Test health monitoring
python test_health_monitor.py

# Test window input
python test_window_input.py

# Test response format
python test_response_format.py

# Test log management
python test_log_manager.py

# Test performance optimizations
python test_performance.py

# Test client restart
python test_restart.py
```

## Development

### Project Structure
```
cybercorp_node/
├── client.py              # Main client application
├── server.py              # WebSocket server
├── admin.py               # Admin control interface
├── client_watchdog.py     # Process monitor
├── config.ini             # Configuration file
├── utils/                 # Utility modules
│   ├── win32_backend.py   # Windows API integration
│   ├── ocr_backend.py     # OCR functionality
│   ├── window_cache.py    # Window caching
│   ├── hot_reload_manager.py  # Hot reload system
│   ├── health_monitor.py  # Health monitoring
│   ├── log_manager.py     # Enhanced logging
│   └── response_formatter.py  # Response formatting
└── test_*.py             # Test scripts
```

### Adding New Commands

1. Add command handler in `client.py`:
```python
elif command == 'your_command':
    return await loop.run_in_executor(None, self._handle_your_command, params)
```

2. Implement the handler:
```python
def _handle_your_command(self, params: dict):
    try:
        # Your implementation
        return format_success(data=result)
    except Exception as e:
        return format_error(e, error_code='YOUR_ERROR_CODE')
```

3. Update admin.py if needed for testing

## Troubleshooting

### Client Won't Connect
1. Check server is running
2. Verify firewall settings
3. Check config.ini settings
4. Review client logs in `logs/` directory

### Commands Timing Out
1. Increase timeout in command params
2. Check client health status
3. Review system resource usage

### Window Activation Issues
- Ensure target application is running
- Check Windows focus assist settings
- Run client with administrator privileges if needed

## Security Considerations

- Always use in trusted networks
- Consider adding authentication mechanisms
- Review and limit command permissions
- Monitor logs for suspicious activity

## License

[Your License Here]

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Review test scripts for examples
- Submit issues on GitHub