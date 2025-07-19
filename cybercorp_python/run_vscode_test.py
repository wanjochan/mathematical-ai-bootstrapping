import asyncio
import threading
import time
import json

# Import server and client
from server import CyberCorpServer
from client import CyberCorpClient

def run_server(server):
    """Run server in a separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def server_with_commands():
        # Start server
        server_task = asyncio.create_task(server.start())
        
        # Wait a bit then send commands
        await asyncio.sleep(5)
        
        print("\n=== Sending command to get VSCode window structure ===")
        await server.send_command(0, 'get_uia_structure')
        
        await asyncio.sleep(3)
        
        print("\n=== Sending command to get process list ===")
        await server.send_command(0, 'get_processes')
        
        await asyncio.sleep(3)
        
        # Cancel server task
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
    
    loop.run_until_complete(server_with_commands())

def run_client():
    """Run client in a separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    client = CyberCorpClient()
    
    async def client_with_timeout():
        client_task = asyncio.create_task(client.connect())
        await asyncio.sleep(15)  # Run for 15 seconds
        client_task.cancel()
        try:
            await client_task
        except asyncio.CancelledError:
            pass
    
    loop.run_until_complete(client_with_timeout())

def main():
    print("CyberCorp VSCode Window Detection Test")
    print("=" * 50)
    print("This will:")
    print("1. Start a WebSocket server on port 8080")
    print("2. Connect a client that can read window information")
    print("3. Capture VSCode window structure if it's open")
    print("4. Show running processes")
    print()
    print("Starting test... (make sure VSCode is open)")
    print()
    
    # Create server
    server = CyberCorpServer()
    
    # Start server in thread
    server_thread = threading.Thread(target=run_server, args=(server,))
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    # Start client in thread
    client_thread = threading.Thread(target=run_client)
    client_thread.start()
    
    # Wait for threads to complete
    server_thread.join()
    client_thread.join()
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()