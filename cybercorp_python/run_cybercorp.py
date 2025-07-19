"""Run CyberCorp server and client, then send commands to extract Roo Code content"""

import subprocess
import time
import sys
import os
import threading

def run_server():
    """Run server and send commands after client connects"""
    proc = subprocess.Popen(
        [sys.executable, 'server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=0
    )
    
    # Wait for server to start
    time.sleep(2)
    
    # Wait for client to connect
    time.sleep(5)
    
    print("\n=== Sending command to get window structures (including background windows) ===")
    proc.stdin.write("uia 0\n")
    proc.stdin.flush()
    
    # Wait for response
    time.sleep(8)
    
    print("\n=== Getting process list ===")
    proc.stdin.write("process 0\n")
    proc.stdin.flush()
    
    time.sleep(3)
    
    # Keep server running to see output
    time.sleep(5)
    
    proc.stdin.write("exit\n")
    proc.stdin.flush()
    
    # Get all output
    output, _ = proc.communicate(timeout=2)
    print("\n=== Server Output ===")
    print(output)

def run_client():
    """Run client in separate thread"""
    proc = subprocess.Popen(
        [sys.executable, 'client.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Let it run for the duration
    time.sleep(25)
    proc.terminate()

def main():
    print("CyberCorp System - Extract Roo Code Content from Background Windows")
    print("=" * 70)
    print("This will:")
    print("1. Start the CyberCorp server (control center)")
    print("2. Start the CyberCorp client (controlled node)")
    print("3. Send command to extract window content (including background VSCode)")
    print("4. Display the extracted Roo Code dialog content")
    print()
    
    # Change to cybercorp_python directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Start client in thread
    client_thread = threading.Thread(target=run_client)
    client_thread.start()
    
    # Run server in main thread
    run_server()
    
    # Wait for client thread
    client_thread.join()
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()