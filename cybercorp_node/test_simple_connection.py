"""Simple connection test for debugging"""

import asyncio
import websockets
import json
import os

async def test_server():
    """Simple test server"""
    print("Starting test server on port 9998...")
    
    async def handler(websocket, path):
        print(f"Client connected: {websocket.remote_address}")
        
        # Send welcome
        await websocket.send(json.dumps({
            'type': 'welcome',
            'message': 'Test server connected'
        }))
        
        # Handle messages
        async for message in websocket:
            print(f"Received: {message}")
            
            # Echo back
            await websocket.send(json.dumps({
                'type': 'echo',
                'data': json.loads(message)
            }))
    
    async with websockets.serve(handler, 'localhost', 9998, compression=None):
        print("Server is running on ws://localhost:9998")
        await asyncio.Future()  # Run forever

async def test_client():
    """Simple test client"""
    print("\nStarting test client...")
    
    uri = "ws://localhost:9998"
    async with websockets.connect(uri, compression=None) as websocket:
        print(f"Connected to {uri}")
        
        # Receive welcome
        welcome = await websocket.recv()
        print(f"Welcome: {welcome}")
        
        # Send test message
        test_msg = {'type': 'test', 'user': os.environ.get('USERNAME')}
        await websocket.send(json.dumps(test_msg))
        print(f"Sent: {test_msg}")
        
        # Receive echo
        echo = await websocket.recv()
        print(f"Echo: {echo}")
        
        print("\nConnection test successful!")

async def main():
    """Run both server and client"""
    print("WebSocket Connection Test")
    print("=" * 50)
    
    # Start server
    server_task = asyncio.create_task(test_server())
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Test client
    try:
        await test_client()
    except Exception as e:
        print(f"Client error: {e}")
    
    # Cancel server
    server_task.cancel()

if __name__ == "__main__":
    # Test mode selection
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'server':
            asyncio.run(test_server())
        elif sys.argv[1] == 'client':
            asyncio.run(test_client())
    else:
        # Run both
        asyncio.run(main())