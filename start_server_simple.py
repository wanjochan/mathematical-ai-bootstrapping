"""Simple server starter for port 9998"""

import subprocess
import sys
import os
import time

os.environ['CYBERCORP_PORT'] = '9998'

print("Starting CyberCorp Server")
print("=" * 50)
print(f"Port: 9998")
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"User: {os.environ.get('USERNAME')}")
print()
print("Waiting for clients to connect...")
print("You can start clients with:")
print("  set CYBERCORP_PORT=9998")
print("  python client.py")
print()

# Start server
proc = subprocess.Popen(
    [sys.executable, 'cybercorp_node/server.py'],
    stdin=sys.stdin,
    stdout=sys.stdout,
    stderr=sys.stderr
)

try:
    proc.wait()
except KeyboardInterrupt:
    print("\nShutting down...")
    proc.terminate()