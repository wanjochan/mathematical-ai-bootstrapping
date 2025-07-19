"""Test CyberCorp server and client connection with new port"""

import subprocess
import time
import threading
import sys
import os

# Set environment to use port 9999
os.environ['CYBERCORP_PORT'] = '9999'

def run_server():
    """Run server in thread"""
    print("[TEST] Starting server on port 9999...")
    proc = subprocess.Popen(
        [sys.executable, 'cybercorp_node/server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
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

def run_client(delay=3):
    """Run client after delay"""
    time.sleep(delay)
    print(f"[TEST] Starting client {delay}...")
    
    proc = subprocess.Popen(
        [sys.executable, 'cybercorp_node/client.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Monitor output
    while True:
        line = proc.stdout.readline()
        if line:
            print(f"[CLIENT-{delay}] {line.strip()}")
        if proc.poll() is not None:
            break

def send_server_commands():
    """Send test commands to server"""
    time.sleep(8)  # Wait for clients to connect
    
    print("\n[TEST] Testing server commands...")
    
    # This would need to be done through the server's stdin
    # For now, just print instructions
    print("\n[TEST] Server is running. You can now type commands:")
    print("  list - Show all connected clients with details")
    print("  info client_0 - Show specific client info")
    print("  cmd client_0 vscode_get_content - Get VSCode content")
    print("  exit - Stop server")

def main():
    print("CyberCorp Connection Test - Port 9999")
    print("=" * 60)
    print("This will start:")
    print("1. Server on port 9999")
    print("2. Client from current user")
    print("3. You can then start another client from different user")
    print()
    
    # Start server in thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Start first client (current user)
    client1_thread = threading.Thread(target=lambda: run_client(3))
    client1_thread.daemon = True
    client1_thread.start()
    
    # Show instructions
    instructions_thread = threading.Thread(target=send_server_commands)
    instructions_thread.daemon = True
    instructions_thread.start()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[TEST] Stopping...")

if __name__ == "__main__":
    main()