"""Start CyberCorp server and client, then extract Roo Code content"""

import subprocess
import sys
import time
import os

def main():
    print("CyberCorp System - Extract Roo Code Dialog Content")
    print("=" * 60)
    
    # Kill any existing processes on port 8080
    print("Cleaning up old processes...")
    subprocess.run("powershell \"Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like '*server.py*'} | Stop-Process -Force\"", shell=True, capture_output=True)
    time.sleep(1)
    
    # Start server
    print("\n1. Starting CyberCorp server...")
    server_proc = subprocess.Popen(
        [sys.executable, "cybercorp_python/server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Start client
    print("2. Starting CyberCorp client...")
    client_proc = subprocess.Popen(
        [sys.executable, "cybercorp_python/client.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for client to connect
    print("3. Waiting for client connection...")
    time.sleep(5)
    
    # Send commands
    print("\n4. Sending commands through control center...")
    
    print("   - Listing connected clients:")
    server_proc.stdin.write("list\n")
    server_proc.stdin.flush()
    time.sleep(2)
    
    print("   - Extracting window structures (including background VSCode with Roo Code):")
    server_proc.stdin.write("uia 0\n")
    server_proc.stdin.flush()
    time.sleep(10)  # Give more time for UIA extraction
    
    print("   - Getting process information:")
    server_proc.stdin.write("process 0\n")
    server_proc.stdin.flush()
    time.sleep(5)
    
    # Exit server
    print("\n5. Shutting down...")
    server_proc.stdin.write("exit\n")
    server_proc.stdin.flush()
    time.sleep(2)
    
    # Terminate processes
    client_proc.terminate()
    server_proc.terminate()
    
    # Get server output
    print("\n6. Server Output:")
    print("-" * 60)
    
    try:
        output, _ = server_proc.communicate(timeout=2)
        lines = output.split('\n')
        
        # Look for UIA structure response
        in_uia_response = False
        for line in lines:
            if 'UIA structure from client' in line:
                in_uia_response = True
                print("\n=== UIA STRUCTURE RESPONSE ===")
            elif 'Process list from client' in line:
                in_uia_response = False
                print("\n=== PROCESS LIST ===")
            
            if in_uia_response and ('roo_code_content' in line or 'Task:' in line or 'Roo Code' in line):
                print(f">>> {line}")
            elif line.strip():
                print(line)
                
    except subprocess.TimeoutExpired:
        pass
    
    print("\n7. Checking for saved results...")
    
    # Check if any output files were created
    output_files = ['vscode_dialog_scan.json', 'roo_code_conversation.json', 'vscode_window_structure.json']
    for file in output_files:
        if os.path.exists(file):
            print(f"   Found: {file}")
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'roo_code' in content.lower() or 'task:' in content.lower():
                    print(f"   Contains Roo Code content!")
    
    print("\nTest completed!")
    print("\nIf you didn't see the Roo Code content, please ensure:")
    print("- VSCode is running (can be in background)")
    print("- The Roo Code dialog panel is open in VSCode")
    print("- The client has necessary permissions")

if __name__ == "__main__":
    main()