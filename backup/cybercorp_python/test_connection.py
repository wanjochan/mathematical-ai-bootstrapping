"""Test basic connection between server and client"""

import asyncio
import websockets
import json
import threading
import time

async def test_server():
    """Simple test server"""
    async def handler(websocket, path):
        print(f"Client connected from {websocket.remote_address}")
        
        # Send welcome
        await websocket.send(json.dumps({
            'type': 'welcome',
            'client_id': 1
        }))
        
        # Wait for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
            
            # Send test command
            if data['type'] == 'heartbeat':
                await websocket.send(json.dumps({
                    'type': 'command',
                    'command': 'get_uia_structure'
                }))
    
    print("Starting test server on port 8080...")
    async with websockets.serve(handler, 'localhost', 8080):
        await asyncio.sleep(30)  # Run for 30 seconds

async def test_client():
    """Simple test client"""
    print("Connecting to server...")
    
    try:
        async with websockets.connect('ws://localhost:8080') as websocket:
            print("Connected!")
            
            # Receive welcome
            message = await websocket.recv()
            print(f"Got: {json.loads(message)}")
            
            # Send heartbeat
            await websocket.send(json.dumps({'type': 'heartbeat'}))
            
            # Wait for command
            message = await websocket.recv()
            command = json.loads(message)
            print(f"Got command: {command}")
            
            # Send response
            await websocket.send(json.dumps({
                'type': 'response',
                'response_type': 'test',
                'data': {'message': 'Connection successful!'}
            }))
            
            await asyncio.sleep(5)
            
    except Exception as e:
        print(f"Client error: {e}")

def run_server_thread():
    asyncio.run(test_server())

def run_client_thread():
    time.sleep(2)  # Let server start
    asyncio.run(test_client())

if __name__ == "__main__":
    print("Testing CyberCorp connection...")
    
    # Run server in thread
    server_thread = threading.Thread(target=run_server_thread)
    server_thread.start()
    
    # Run client in thread
    client_thread = threading.Thread(target=run_client_thread)
    client_thread.start()
    
    # Wait for both
    server_thread.join()
    client_thread.join()
    
    print("\nConnection test completed!")