import subprocess
import time
import sys
import os

def main():
    print("CyberCorp VSCode Window Structure Test")
    print("=" * 50)
    print()
    
    # Start server process
    print("1. Starting server...")
    server_env = os.environ.copy()
    server_env['PYTHONUNBUFFERED'] = '1'
    
    server = subprocess.Popen(
        [sys.executable, 'server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=0,
        env=server_env
    )
    
    # Wait for server to start
    time.sleep(3)
    print("   Server started on port 8080")
    
    # Start client process
    print("\n2. Starting client...")
    client = subprocess.Popen(
        [sys.executable, 'client.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=0,
        env=server_env
    )
    
    # Wait for client to connect
    time.sleep(3)
    print("   Client started and connected")
    
    # Send commands
    print("\n3. Testing commands...")
    
    print("\n   - Listing clients:")
    server.stdin.write("list\n")
    server.stdin.flush()
    time.sleep(1)
    
    print("\n   - Getting window structure (VSCode should be visible):")
    server.stdin.write("uia 0\n")
    server.stdin.flush()
    time.sleep(5)
    
    print("\n   - Getting process list:")
    server.stdin.write("process 0\n")
    server.stdin.flush()
    time.sleep(3)
    
    # Exit server
    print("\n4. Shutting down...")
    server.stdin.write("exit\n")
    server.stdin.flush()
    time.sleep(1)
    
    # Terminate processes
    client.terminate()
    server.terminate()
    
    # Get output
    print("\n5. Server output:")
    print("-" * 50)
    
    # Read any remaining output
    try:
        server_output = server.communicate(timeout=2)[0]
        if server_output:
            for line in server_output.split('\n'):
                if line.strip():
                    print(f"   {line}")
    except:
        pass
    
    print("\nTest completed!")

if __name__ == "__main__":
    # Change to the cybercorp_python directory
    os.chdir('cybercorp_python')
    main()