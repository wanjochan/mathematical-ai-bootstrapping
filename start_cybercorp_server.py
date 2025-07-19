"""Start CyberCorp server and keep it running"""

import subprocess
import sys
import os

def start_server():
    print("Starting CyberCorp Control Server...")
    print("=" * 50)
    print("Server will run on port 8888")
    print("Press Ctrl+C to stop")
    print()
    
    # Change to cybercorp_node directory
    os.chdir('cybercorp_node')
    
    # Start server
    try:
        subprocess.run([sys.executable, 'server.py'])
    except KeyboardInterrupt:
        print("\nServer stopped by user")

if __name__ == "__main__":
    start_server()