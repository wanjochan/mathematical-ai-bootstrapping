"""Update running server by restarting it with new code"""

import psutil
import subprocess
import time
import os
import sys

def find_server_process():
    """Find the CyberCorp server process on port 9998"""
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr.port == 9998 and conn.status == 'LISTEN':
            try:
                proc = psutil.Process(conn.pid)
                return proc
            except:
                pass
    return None

def main():
    print("CyberCorp Server Update")
    print("=" * 50)
    
    # Find server
    server_proc = find_server_process()
    
    if not server_proc:
        print("No server found on port 9998")
        print("\nStarting new server...")
        subprocess.Popen([sys.executable, "server.py"], 
                        cwd=os.path.dirname(os.path.abspath(__file__)))
        print("Server started with updated code!")
        return
    
    print(f"Found server process: PID {server_proc.pid}")
    print("Stopping current server...")
    
    try:
        server_proc.terminate()
        server_proc.wait(timeout=5)
        print("Server stopped gracefully")
    except:
        print("Force stopping server...")
        server_proc.kill()
    
    time.sleep(2)
    
    print("\nStarting updated server...")
    subprocess.Popen([sys.executable, "server.py"], 
                     cwd=os.path.dirname(os.path.abspath(__file__)))
    
    print("\nServer updated! Clients will reconnect automatically.")
    print("New features available:")
    print("- list_clients command support")
    print("- config.ini port configuration")

if __name__ == "__main__":
    main()