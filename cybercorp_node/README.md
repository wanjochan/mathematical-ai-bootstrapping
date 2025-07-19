# CyberCorp Stable - Cross-User Session Control System

A robust system for controlling VSCode and development environments across different Windows user sessions.

## Features

- **Stable WebSocket Connection**: Auto-reconnect, heartbeat monitoring
- **Cross-User Session Support**: Control VSCode in another user's session
- **VSCode Integration**: Read content, send keystrokes, execute commands
- **UI Automation**: Access window content even when in background
- **Remote Control**: Mouse, keyboard, and screenshot capabilities
- **Command Queue**: Reliable command execution with status feedback

## Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│   Control Machine   │         │   Target Machine    │
│                     │         │  (Different User)   │
│  ┌───────────────┐  │         │  ┌───────────────┐  │
│  │ CyberCorp     │  │ Network │  │ CyberCorp     │  │
│  │ Server        │◄─┼─────────┼──┤ Client        │  │
│  │ (Port 8888)   │  │   WS    │  │               │  │
│  └───────────────┘  │         │  └───────┬───────┘  │
│                     │         │          │           │
│  ┌───────────────┐  │         │  ┌───────▼───────┐  │
│  │ Console       │  │         │  │ VSCode        │  │
│  │ Interface     │  │         │  │ (Controlled)  │  │
│  └───────────────┘  │         │  └───────────────┘  │
└─────────────────────┘         └─────────────────────┘
```

## Installation

1. **Run as Administrator**:
   ```batch
   setup_service.bat
   ```

2. **Manual Installation**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Start the Control Server

On your control machine:
```batch
python server.py
```

Or use the installed service:
```batch
C:\CyberCorp\start_server.bat
```

### 2. Start the Client in Target Session

**Option A: Direct Login**
Log into the target user account and run:
```batch
python client.py
```

**Option B: Remote Start (PowerShell)**
From administrator account:
```powershell
.\start_remote_session.ps1 -Username "TargetUser" -Password "Password" -ServerIP "192.168.1.100"
```

### 3. Control VSCode

In the server console:

```
server> list
Connected clients (1):
  client_0: 192.168.1.101 (session: TargetUser)

server> vscode client_0
=== VSCode Control Mode ===

vscode> content
[Gets current VSCode window content including Roo Code dialog]

vscode> type Hello from remote!
[Types text in VSCode]

vscode> cmd workbench.action.files.save
[Saves current file]
```

## Available Commands

### Server Commands
- `list` - List connected clients
- `info <client_id>` - Show client details
- `cmd <client_id> <command>` - Send command
- `vscode <client_id>` - Enter VSCode control mode
- `help` - Show help
- `exit` - Stop server

### VSCode Control Commands
- `content` - Get VSCode window content
- `type <text>` - Type text in editor
- `cmd <command>` - Execute VSCode command
- `back` - Return to main menu

### Available Client Commands
- `get_windows` - List all windows
- `get_window_content` - Get VSCode content
- `activate_window` - Bring VSCode to front
- `send_keys` - Send keystrokes
- `send_mouse_click` - Click at coordinates
- `take_screenshot` - Capture screen
- `get_processes` - List processes
- `vscode_get_content` - Get VSCode content
- `vscode_type_text` - Type in VSCode
- `vscode_send_command` - Execute VSCode command

## Security Considerations

1. **Firewall**: Opens port 8888 for WebSocket communication
2. **Authentication**: Currently no authentication - use on trusted networks only
3. **Permissions**: Client needs UI automation permissions
4. **User Sessions**: Requires appropriate permissions for cross-session control

## Troubleshooting

### Client Won't Connect
- Check firewall settings
- Verify server is running on port 8888
- Ensure network connectivity

### VSCode Not Found
- Make sure VSCode is running in target session
- Client must run in same session as VSCode
- Check UI automation permissions

### Commands Not Working
- VSCode window must exist (can be minimized)
- Some commands require window activation
- Check client logs for errors

## Development

### Adding New Commands

1. Add command type to server.py:
```python
class CommandType(Enum):
    MY_COMMAND = "my_command"
```

2. Implement handler in client.py:
```python
elif command == 'my_command':
    result = self._my_command_handler(params)
```

### Logging

Logs are displayed in console. For file logging, modify:
```python
logging.basicConfig(
    filename='cybercorp.log',
    level=logging.INFO
)
```

## Future Enhancements

- [ ] SSL/TLS encryption
- [ ] Authentication system
- [ ] Multiple VSCode instance support
- [ ] Recording and playback
- [ ] Web-based control panel
- [ ] Linux/Mac support