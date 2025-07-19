"""Test hot reload server functionality"""

import subprocess
import sys
import os
import time
import threading

def run_server():
    """Run hot reload server"""
    print("Starting Hot Reload Server on port 9998")
    print("=" * 60)
    
    env = os.environ.copy()
    env['CYBERCORP_PORT'] = '9998'
    
    proc = subprocess.Popen(
        [sys.executable, 'server_hotreload.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Monitor output
    while True:
        line = proc.stdout.readline()
        if line:
            print(f"[SERVER] {line.strip()}")
        if proc.poll() is not None:
            break
    
    return proc

def main():
    print("CyberCorp Hot Reload Server Test")
    print("=" * 60)
    print("Features:")
    print("- Hot reload plugins from plugins/ directory")
    print("- Hot reload configuration from server_config.json")
    print("- Plugin-based command system")
    print()
    
    # Install watchdog if needed
    print("Installing dependencies...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'watchdog'], capture_output=True)
    
    # Start server
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Instructions
    print("\nServer starting...")
    print("\nYou can now:")
    print("1. Start clients with: set CYBERCORP_PORT=9998 && python client.py")
    print("2. Modify plugins/*.py files to see hot reload")
    print("3. Edit server_config.json to update configuration")
    print()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()