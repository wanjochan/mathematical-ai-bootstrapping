"""Monitor CyberCorp server status via admin connection"""

import asyncio
import websockets
import json
import os
from datetime import datetime

class ServerMonitor:
    def __init__(self):
        self.port = int(os.environ.get('CYBERCORP_PORT', '9998'))
        self.server_url = f'ws://localhost:{self.port}'
        
    async def connect_as_monitor(self):
        """Connect to server as a monitoring client"""
        print(f"Connecting to server at {self.server_url}...")
        
        try:
            async with websockets.connect(self.server_url) as websocket:
                print("Connected as monitor client")
                
                # Register as monitor
                await websocket.send(json.dumps({
                    'type': 'register',
                    'user_session': 'MONITOR',
                    'client_start_time': datetime.now().isoformat(),
                    'capabilities': {
                        'monitor': True
                    },
                    'system_info': {
                        'platform': 'Monitor',
                        'hostname': 'Monitor',
                        'python_version': '3.x'
                    },
                    'metadata': {
                        'role': 'monitor',
                        'purpose': 'server_status'
                    }
                }))
                
                # Wait for welcome message
                welcome = await websocket.recv()
                print(f"Server response: {welcome}")
                
                # Request server status (this would need server support)
                await websocket.send(json.dumps({
                    'type': 'request',
                    'command': 'get_client_list'
                }))
                
                # Keep connection alive for a bit
                await asyncio.sleep(5)
                
        except Exception as e:
            print(f"Error: {e}")

async def main():
    print("CyberCorp Server Monitor")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    monitor = ServerMonitor()
    await monitor.connect_as_monitor()

if __name__ == "__main__":
    asyncio.run(main())