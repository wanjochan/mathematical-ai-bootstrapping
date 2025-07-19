# CyberCorp Batch Files Documentation

## Current Configuration
All components now use `config.ini` for configuration. The server port is locked to **9998**.

## Primary Batch Files (Use These)

### `start_server_clean.bat`
- Starts the CyberCorp control server
- Reads configuration from `config.ini`
- Default port: 9998
- Usage: Double-click or run from command line

### `start_client_clean.bat`  
- Starts the CyberCorp client (受控端)
- Connects to server using `config.ini` settings
- Shows current user and computer name
- Usage: Run in each user session that needs control

## Legacy Batch Files (For Reference Only)

### `start_server.bat` / `start_client.bat`
- Original batch files, may use old port settings
- Kept for backward compatibility

### `start_server_port9999.bat` / `start_client_port9999.bat`
- Explicitly use port 9999 (old port)
- Override config.ini settings

### `start_server_unified.bat` / `start_client_unified.bat`
- Attempt to unify port configuration
- May still have inconsistencies

## Configuration

All settings are now in `config.ini`:
```ini
[server]
port = 9998

[client]
server_port = 9998
```

## Multi-User Setup

1. **On Control Computer (中控端)**:
   ```
   start_server_clean.bat
   ```

2. **On Each Controlled Computer/User (受控端)**:
   ```
   start_client_clean.bat
   ```

3. **Check Connected Clients**:
   - In server console, type: `list`
   - Or run: `python test_list_clients.py`

## Troubleshooting

If port 9998 is busy:
1. Check running processes: `python check_status.py`
2. Kill old processes if needed
3. Restart server

For connection issues:
1. Verify `config.ini` exists and has correct settings
2. Check firewall allows port 9998
3. Ensure all components use same port