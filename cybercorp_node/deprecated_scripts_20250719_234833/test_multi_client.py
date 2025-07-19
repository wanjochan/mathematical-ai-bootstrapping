"""Test multiple client connections"""

import subprocess
import sys
import os
import time
import threading

def run_server():
    """Run server process"""
    print("[Starting Server on port 9998...]")
    env = os.environ.copy()
    env['CYBERCORP_PORT'] = '9998'
    
    proc = subprocess.Popen(
        [sys.executable, 'server.py'],
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Read output and auto-send list command
    client_count = 0
    while True:
        line = proc.stdout.readline()
        if line:
            print(f"[SERVER] {line.strip()}")
            
            # Auto list when client connects
            if "connected from" in line:
                client_count += 1
                time.sleep(1)
                print(f"\n[AUTO] Client connected! Total: {client_count}")
                proc.stdin.write("list\n")
                proc.stdin.flush()
                
        if proc.poll() is not None:
            break

def run_client(client_num):
    """Run client process"""
    time.sleep(3 + client_num * 2)  # Stagger client starts
    
    print(f"\n[Starting Client {client_num}...]")
    env = os.environ.copy()
    env['CYBERCORP_PORT'] = '9998'
    
    proc = subprocess.Popen(
        [sys.executable, 'client.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Monitor output
    for _ in range(50):
        line = proc.stdout.readline()
        if line:
            print(f"[CLIENT-{client_num}] {line.strip()}")
            if "Registered as user" in line:
                print(f"[CLIENT-{client_num}] Successfully connected!")
                break
    
    # Keep running
    time.sleep(60)
    proc.terminate()

def main():
    print("CyberCorp Multi-Client Test")
    print("=" * 60)
    print(f"Current User: {os.environ.get('USERNAME')}")
    print(f"Computer: {os.environ.get('COMPUTERNAME')}")
    print()
    print("This test will:")
    print("1. Start server on port 9998")
    print("2. Start client in current user")
    print("3. Wait for you to start another client in different user")
    print()
    
    # Start server
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Start first client
    client1_thread = threading.Thread(target=lambda: run_client(1))
    client1_thread.daemon = True
    client1_thread.start()
    
    print("\nTo start client in another user:")
    print("  cd cybercorp_node")
    print("  set CYBERCORP_PORT=9998")
    print("  python client.py")
    print()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()