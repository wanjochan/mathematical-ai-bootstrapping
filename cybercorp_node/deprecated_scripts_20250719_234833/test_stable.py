"""Test CyberCorp Stable system - start server and client, then get VSCode content"""

import subprocess
import time
import sys
import os
import threading

def run_server():
    """Run server and send test commands"""
    print("Starting CyberCorp server...")
    server = subprocess.Popen(
        [sys.executable, "cybercorp_stable/server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Monitor server output
    def read_output():
        for line in server.stdout:
            print(f"[SERVER] {line.strip()}")
    
    output_thread = threading.Thread(target=read_output)
    output_thread.daemon = True
    output_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    # Send commands after client connects
    print("\nWaiting for client connection...")
    time.sleep(8)
    
    print("\nSending test commands...")
    
    # List clients
    print("\n1. Listing connected clients:")
    server.stdin.write("list\n")
    server.stdin.flush()
    time.sleep(2)
    
    # Get VSCode content
    print("\n2. Getting VSCode window content:")
    server.stdin.write("cmd client_0 vscode_get_content\n")
    server.stdin.flush()
    time.sleep(5)
    
    # Try VSCode control mode
    print("\n3. Entering VSCode control mode:")
    server.stdin.write("vscode client_0\n")
    server.stdin.flush()
    time.sleep(2)
    
    print("\n4. Getting content through VSCode mode:")
    server.stdin.write("content\n")
    server.stdin.flush()
    time.sleep(5)
    
    # Exit VSCode mode
    server.stdin.write("back\n")
    server.stdin.flush()
    time.sleep(1)
    
    # Keep running for a bit to see results
    time.sleep(5)
    
    # Exit
    print("\n5. Shutting down server...")
    server.stdin.write("exit\n")
    server.stdin.flush()
    time.sleep(2)
    
    server.terminate()

def run_client():
    """Run client in separate thread"""
    print("Starting CyberCorp client...")
    client = subprocess.Popen(
        [sys.executable, "cybercorp_stable/client.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Monitor client output
    def read_output():
        for line in client.stdout:
            print(f"[CLIENT] {line.strip()}")
    
    output_thread = threading.Thread(target=read_output)
    output_thread.daemon = True
    output_thread.start()
    
    # Let client run
    time.sleep(35)
    client.terminate()

def main():
    print("CyberCorp Stable Test - Get VSCode Content")
    print("=" * 60)
    print("This test will:")
    print("1. Start the CyberCorp server")
    print("2. Start the CyberCorp client")
    print("3. Get VSCode window content (including Roo Code dialog)")
    print("4. Display the extracted content")
    print()
    print("Make sure VSCode is open with some content visible.")
    print()
    
    # Start client in thread
    client_thread = threading.Thread(target=run_client)
    client_thread.start()
    
    # Wait a bit for client to initialize
    time.sleep(3)
    
    # Run server in main thread
    run_server()
    
    # Wait for client thread
    client_thread.join()
    
    print("\nTest completed!")
    print("\nIf you saw VSCode content above, the system is working correctly.")
    print("Look for lines marked [SERVER] that show the window content.")

if __name__ == "__main__":
    main()