import asyncio
import subprocess
import time
import sys

async def run_test():
    print("CyberCorp VSCode Window Structure Test")
    print("=" * 50)
    
    # Start server
    print("\n1. Starting server...")
    server = subprocess.Popen([sys.executable, "server.py"], 
                             cwd="cybercorp_python",
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             text=True,
                             bufsize=1)
    
    # Wait for server to start
    time.sleep(2)
    
    # Start client
    print("2. Starting client...")
    client = subprocess.Popen([sys.executable, "client.py"],
                             cwd="cybercorp_python",
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             text=True)
    
    # Wait for client to connect
    time.sleep(3)
    
    print("\n3. Sending commands...")
    
    # List clients
    print("\n- Listing connected clients:")
    server.stdin.write("list\n")
    server.stdin.flush()
    time.sleep(1)
    
    # Get UIA structure
    print("\n- Getting VSCode window structure:")
    print("  (Make sure VSCode is open)")
    server.stdin.write("uia 0\n")
    server.stdin.flush()
    time.sleep(3)
    
    # Get processes
    print("\n- Getting process list:")
    server.stdin.write("process 0\n")
    server.stdin.flush()
    time.sleep(2)
    
    # Cleanup
    print("\n4. Cleaning up...")
    server.stdin.write("exit\n")
    server.stdin.flush()
    time.sleep(1)
    
    client.terminate()
    server.terminate()
    
    # Print server output
    print("\n5. Server output:")
    stdout, stderr = server.communicate(timeout=2)
    if stdout:
        print(stdout)
    if stderr:
        print("Errors:", stderr)
    
    print("\nTest completed!")

if __name__ == "__main__":
    print("This test will capture VSCode window structure using Python.")
    print("Please ensure VSCode is open before continuing.")
    input("Press Enter to start the test...")
    
    asyncio.run(run_test())