"""Test server and client connection in current user session"""

import subprocess
import time
import threading
import sys

def run_server():
    """Run server in thread"""
    proc = subprocess.Popen(
        [sys.executable, 'cybercorp_node/server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Read output
    while True:
        line = proc.stdout.readline()
        if line:
            print(f"[SERVER] {line.strip()}")
        if proc.poll() is not None:
            break
    
def run_client():
    """Run client after delay"""
    time.sleep(3)  # Wait for server to start
    
    proc = subprocess.Popen(
        [sys.executable, 'cybercorp_node/client.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Read output
    while True:
        line = proc.stdout.readline()
        if line:
            print(f"[CLIENT] {line.strip()}")
        if proc.poll() is not None:
            break

def main():
    print("Testing CyberCorp connection in current user session")
    print("=" * 60)
    
    # Start server in thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Start client in thread
    client_thread = threading.Thread(target=run_client)
    client_thread.daemon = True
    client_thread.start()
    
    # Keep running
    print("\nServer and client are starting...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")

if __name__ == "__main__":
    main()