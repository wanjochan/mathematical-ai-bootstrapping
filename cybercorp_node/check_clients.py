import asyncio
import websockets
import json

async def check():
    ws = await websockets.connect('ws://localhost:9998')
    await ws.send(json.dumps({'type': 'register', 'user_session': 'checker', 'client_start_time': '2024', 'capabilities': {}}))
    await ws.recv()
    await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
    response = await ws.recv()
    data = json.loads(response)
    print(f"Total clients: {len(data.get('clients', []))}")
    for client in data.get('clients', []):
        print(f"- {client.get('user_session')} (ID: {client['id']})")
    await ws.close()

asyncio.run(check())