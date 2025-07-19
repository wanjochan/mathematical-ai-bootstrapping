"""Notify client to restart for new features"""

import asyncio
import websockets
import json

async def notify_restart():
    """Send restart notification to clients"""
    
    server_url = 'ws://localhost:9998'
    
    try:
        websocket = await websockets.connect(server_url)
        
        # Register as admin
        await websocket.send(json.dumps({
            'type': 'register',
            'user_session': 'admin_notifier',
            'capabilities': {'admin': True}
        }))
        
        await websocket.recv()
        
        # Get client list
        await websocket.send(json.dumps({
            'type': 'request',
            'command': 'list_clients'
        }))
        
        response = await websocket.recv()
        data = json.loads(response)
        
        print("Connected clients:")
        for client in data.get('clients', []):
            print(f"  - {client['user_session']} (ID: {client['id']})")
        
        print("\n[NOTICE] Clients need to restart to load new background operation features")
        print("New features added:")
        print("  - background_input: Send input without window activation")
        print("  - background_click: Click elements without window activation")
        
        await websocket.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(notify_restart())