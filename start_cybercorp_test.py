"""Start CyberCorp server and client for testing"""

import subprocess
import sys
import time
import threading
import os

# Set port to 9999
os.environ['CYBERCORP_PORT'] = '9999'

def run_server():
    """Run server with interactive console"""
    print("[Starting Server on port 9999...]")
    server = subprocess.Popen(
        [sys.executable, 'cybercorp_node/server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Read initial output
    for _ in range(10):
        line = server.stdout.readline()
        if line:
            print(f"[SERVER] {line.strip()}")
            if "Server listening" in line:
                break
    
    # Wait a bit then send list command periodically
    time.sleep(10)
    print("\n[Sending 'list' command to server...]")
    server.stdin.write("list\n")
    server.stdin.flush()
    
    # Read response
    for _ in range(20):
        line = server.stdout.readline()
        if line:
            print(f"[SERVER] {line.strip()}")
    
    # Wait and send list again
    time.sleep(30)
    print("\n[Sending 'list' command again to check for second client...]")
    server.stdin.write("list\n")
    server.stdin.flush()
    
    # Read response
    for _ in range(30):
        line = server.stdout.readline()
        if line:
            print(f"[SERVER] {line.strip()}")
    
    # Keep server running
    time.sleep(60)
    
    # Shutdown
    server.stdin.write("exit\n")
    server.stdin.flush()
    server.terminate()

def run_client():
    """Run client in current user"""
    time.sleep(5)  # Wait for server to start
    print("\n[Starting Client in current user...]")
    print(f"[CLIENT] Current user: {os.environ.get('USERNAME')}")
    
    client = subprocess.Popen(
        [sys.executable, 'cybercorp_node/client.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Monitor output
    for _ in range(100):
        line = client.stdout.readline()
        if line:
            print(f"[CLIENT] {line.strip()}")
            if "Registered as user" in line:
                print("[CLIENT] Successfully connected!")
                break
    
    # Keep running
    time.sleep(90)
    client.terminate()

def main():
    print("CyberCorp Multi-Client Test")
    print("=" * 60)
    print(f"Current User: {os.environ.get('USERNAME')}")
    print(f"Computer: {os.environ.get('COMPUTERNAME')}")
    print()
    print("1. Starting server on port 9999")
    print("2. Starting client in current user")
    print("3. Waiting for you to start client in another user")
    print()
    
    # Start server
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    
    # Start client
    client_thread = threading.Thread(target=run_client)
    client_thread.start()
    
    # Wait for threads
    server_thread.join()
    client_thread.join()
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()