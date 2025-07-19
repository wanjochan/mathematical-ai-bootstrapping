"""Run CyberCorp server in background for testing"""

import subprocess
import time
import sys
import os
import threading

def monitor_server(proc):
    """Monitor server output"""
    for line in proc.stdout:
        print(f"[SERVER] {line.strip()}")

def main():
    print("Starting CyberCorp Server in background...")
    
    # Start server process
    server_proc = subprocess.Popen(
        [sys.executable, 'cybercorp_node/server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Monitor output in thread
    monitor_thread = threading.Thread(target=monitor_server, args=(server_proc,))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    print("Server started. It will run for 5 minutes for testing.")
    print("You can now connect clients from other sessions.")
    print()
    
    # Keep alive for 5 minutes
    try:
        time.sleep(300)  # 5 minutes
    except KeyboardInterrupt:
        print("\nStopping server...")
    
    # Stop server
    server_proc.stdin.write("exit\n")
    server_proc.stdin.flush()
    time.sleep(2)
    server_proc.terminate()
    
    print("Server stopped.")

if __name__ == "__main__":
    main()