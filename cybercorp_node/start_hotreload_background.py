"""Start hot reload server in background"""

import subprocess
import sys
import os

# Start in new window
subprocess.Popen(
    ["cmd", "/c", "start", "CyberCorp Hot Reload Server", sys.executable, "server_hotreload.py"],
    cwd=os.path.dirname(__file__)
)

print("Hot reload server starting in new window...")
print("Features:")
print("- Automatic plugin reloading")
print("- Config file hot reload")
print("- Command forwarding")
print("- Client management")