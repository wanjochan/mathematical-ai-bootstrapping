"""Restart the CyberCorp server to load new code"""

import psutil
import subprocess
import time
import sys

def find_server_process():
    """Find the running server process"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = ' '.join(proc.info['cmdline'])
                if 'server.py' in cmdline and 'cybercorp' in cmdline.lower():
                    return proc
        except:
            pass
    return None

def main():
    print("CyberCorp Server Restart")
    print("=" * 50)
    
    # Find server process
    server_proc = find_server_process()
    
    if server_proc:
        print(f"Found server process: PID {server_proc.pid}")
        print("Terminating server...")
        
        try:
            server_proc.terminate()
            server_proc.wait(timeout=5)
            print("Server terminated successfully")
        except:
            print("Force killing server...")
            server_proc.kill()
            
        time.sleep(2)
    else:
        print("No running server found")
    
    # Start new server
    print("\nStarting new server with updated code...")
    print("Please run: python server.py")
    print("\nNote: Clients will automatically reconnect")

if __name__ == "__main__":
    main()