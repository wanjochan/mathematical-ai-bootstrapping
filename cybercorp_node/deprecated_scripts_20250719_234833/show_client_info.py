"""Display comprehensive information about a controlled client"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from cybercorp_test import CyberCorpTester

async def show_client_info(username):
    """Show all available information from a client"""
    
    print(f"CyberCorp Client Information Report: {username}")
    print("=" * 80)
    
    tester = CyberCorpTester()
    
    # Get system info
    print("\n[1] System Information")
    print("-" * 60)
    await tester.control_client(username, 'get_system_info')
    
    # Get screen info
    print("\n[2] Screen Information")
    print("-" * 60)
    await tester.control_client(username, 'get_screen_size')
    
    # Get process info
    print("\n[3] Top Processes")
    print("-" * 60)
    await tester.control_client(username, 'get_processes')
    
    # Get window info
    print("\n[4] Open Windows")
    print("-" * 60)
    await tester.control_client(username, 'get_windows')
    
    print("\n[5] Available Capabilities")
    print("-" * 60)
    
    # List capabilities
    websocket, _ = await tester.connect()
    if websocket:
        await websocket.send(json.dumps({
            'type': 'request',
            'command': 'list_clients'
        }))
        
        response = await websocket.recv()
        import json
        data = json.loads(response)
        
        if data['type'] == 'client_list':
            for client in data['clients']:
                if client.get('user_session') == username:
                    print(f"Capabilities: {json.dumps(client.get('capabilities', {}), indent=2)}")
                    break
        
        await websocket.close()
    
    print("\n" + "=" * 80)
    print("Report completed!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python show_client_info.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    asyncio.run(show_client_info(username))