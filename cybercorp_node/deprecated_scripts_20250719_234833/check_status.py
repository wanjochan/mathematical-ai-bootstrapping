"""Check CyberCorp system status"""

import subprocess
import socket
import psutil
import os

def check_port(port):
    """Check if port is in use"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except:
        return False

def find_process_by_port(port):
    """Find process using specific port"""
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr.port == port and conn.status == 'LISTEN':
            try:
                proc = psutil.Process(conn.pid)
                return {
                    'pid': conn.pid,
                    'name': proc.name(),
                    'cmdline': ' '.join(proc.cmdline())
                }
            except:
                pass
    return None

def main():
    print("CyberCorp System Status Check")
    print("=" * 50)
    print(f"Current User: {os.environ.get('USERNAME')}")
    print(f"Computer: {os.environ.get('COMPUTERNAME')}")
    print()
    
    # Check ports
    ports = [8888, 9998, 9999]
    for port in ports:
        if check_port(port):
            print(f"Port {port}: IN USE")
            proc = find_process_by_port(port)
            if proc:
                print(f"  Process: {proc['name']} (PID: {proc['pid']})")
                if 'python' in proc['cmdline'].lower():
                    if 'server' in proc['cmdline']:
                        print(f"  Type: CyberCorp Server")
                    elif 'client' in proc['cmdline']:
                        print(f"  Type: CyberCorp Client")
        else:
            print(f"Port {port}: Available")
    
    print()
    
    # Check for running python processes
    print("Python processes:")
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = ' '.join(proc.info['cmdline'])
                if 'cybercorp' in cmdline.lower():
                    print(f"  PID {proc.info['pid']}: {cmdline[:80]}...")
        except:
            pass

if __name__ == "__main__":
    main()