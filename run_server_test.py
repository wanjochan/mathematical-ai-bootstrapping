"""Run CyberCorp server and monitor connections"""

import subprocess
import sys
import time
import threading
import os

os.environ['CYBERCORP_PORT'] = '9998'

def monitor_server(proc):
    """Monitor server output"""
    while True:
        line = proc.stdout.readline()
        if line:
            print(f"[SERVER] {line.strip()}")
            
            # Auto-send list command when client connects
            if "Client" in line and "connected from" in line:
                time.sleep(2)
                print("\n[AUTO] Sending 'list' command...")
                proc.stdin.write("list\n")
                proc.stdin.flush()
        
        if proc.poll() is not None:
            break

def run_server():
    print("Starting CyberCorp Server on port 9998")
    print("=" * 60)
    print(f"Server Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"User: {os.environ.get('USERNAME')}")
    print(f"Host: {os.environ.get('COMPUTERNAME')}")
    print()
    
    # Start server
    server = subprocess.Popen(
        [sys.executable, 'cybercorp_node/server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Monitor in thread
    monitor_thread = threading.Thread(target=monitor_server, args=(server,))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Interactive loop
    print("\nServer is starting... Commands:")
    print("  list - Show connected clients")
    print("  test - Send test command to all clients")
    print("  exit - Stop server")
    print()
    
    time.sleep(3)
    
    try:
        while True:
            # Periodically send list command
            time.sleep(15)
            print(f"\n[AUTO CHECK at {time.strftime('%H:%M:%S')}]")
            server.stdin.write("list\n")
            server.stdin.flush()
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.stdin.write("exit\n")
        server.stdin.flush()
        time.sleep(1)
        server.terminate()

if __name__ == "__main__":
    run_server()