"""Quick test of CyberCorp Stable - simplified version"""

import asyncio
import subprocess
import sys
import time
import os

# First, let's test with a simple direct approach
def test_direct():
    print("Testing direct VSCode content extraction...")
    
    # Import client components
    sys.path.insert(0, 'cybercorp_stable')
    from client import VSCodeController
    
    controller = VSCodeController()
    
    # Find VSCode
    if controller.find_vscode_window():
        print("[OK] Found VSCode window")
        
        # Get content
        content = controller.get_window_content()
        if content:
            print(f"[OK] Window title: {content['window_title']}")
            print(f"[OK] Is active: {content['is_active']}")
            print(f"[OK] Content areas found: {len(content['content_areas'])}")
            
            # Look for Roo Code content
            roo_code_found = False
            for area in content['content_areas']:
                if 'Roo Code' in area.get('name', '') or any('Roo Code' in t for t in area.get('texts', [])):
                    roo_code_found = True
                    print("\n[OK] Found Roo Code dialog!")
                    print(f"  Type: {area['type']}")
                    print(f"  Name: {area['name']}")
                    if area['texts']:
                        print("  Content samples:")
                        for text in area['texts'][:5]:
                            if len(text) > 100:
                                print(f"    - {text[:100]}...")
                            else:
                                print(f"    - {text}")
            
            if not roo_code_found:
                print("\n! Roo Code dialog not found in content areas")
                print("  Make sure the Roo Code panel is open in VSCode")
        else:
            print("[FAIL] Could not get window content")
    else:
        print("[FAIL] VSCode window not found")

def test_server_client():
    print("\n\nTesting server-client system...")
    print("Starting on port 9999 to avoid conflicts...")
    
    # Modify client to use port 9999
    client_code = '''
import sys
sys.path.insert(0, 'cybercorp_stable')
from client import CyberCorpClient
import asyncio

client = CyberCorpClient('ws://localhost:9999')
asyncio.run(client.run())
'''
    
    # Start server on port 9999
    server_proc = subprocess.Popen(
        [sys.executable, '-c', '''
import sys
sys.path.insert(0, 'cybercorp_stable')
from server import CyberCorpServer
import asyncio

server = CyberCorpServer(port=9999)
asyncio.run(server.start())
'''],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    time.sleep(2)
    
    # Start client
    client_proc = subprocess.Popen(
        [sys.executable, '-c', client_code],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    time.sleep(3)
    
    # Send test command
    server_proc.stdin.write("list\n")
    server_proc.stdin.flush()
    time.sleep(1)
    
    # Check if processes are running
    if server_proc.poll() is None:
        print("[OK] Server is running")
    else:
        print("[FAIL] Server crashed")
        
    if client_proc.poll() is None:
        print("[OK] Client is running")
    else:
        print("[FAIL] Client crashed")
    
    # Cleanup
    server_proc.stdin.write("exit\n")
    server_proc.stdin.flush()
    time.sleep(1)
    
    server_proc.terminate()
    client_proc.terminate()

def main():
    print("CyberCorp Stable - Quick Test")
    print("=" * 50)
    
    # Test 1: Direct VSCode content extraction
    test_direct()
    
    # Test 2: Server-client system
    test_server_client()
    
    print("\n\nTest completed!")

if __name__ == "__main__":
    main()