"""Start CyberCorp server in background"""

import subprocess
import sys
import os
import time

# Start server in a new console window
server_path = os.path.join(os.path.dirname(__file__), "server.py")
subprocess.Popen(
    ["cmd", "/c", "start", "CyberCorp Server", sys.executable, server_path],
    cwd=os.path.dirname(__file__)
)

print("Server starting in new window...")
time.sleep(2)

# Check if it started
import psutil
for conn in psutil.net_connections(kind='inet'):
    if conn.laddr.port == 9998 and conn.status == 'LISTEN':
        print(f"✓ Server started successfully on port 9998 (PID: {conn.pid})")
        break
else:
    print("⚠ Server may not have started properly")