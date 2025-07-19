import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CyberCorpServer:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.clients = {}
        self.client_id_counter = 0
        
    async def handle_client(self, websocket, path):
        client_id = self.client_id_counter
        self.client_id_counter += 1
        
        client_info = {
            'id': client_id,
            'ws': websocket,
            'ip': websocket.remote_address[0],
            'connected_at': datetime.now(),
            'status': 'connected'
        }
        
        self.clients[client_id] = client_info
        logging.info(f"Client {client_id} connected from {client_info['ip']}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                'type': 'welcome',
                'client_id': client_id,
                'message': 'Connected to CyberCorp Server'
            }))
            
            # Handle messages
            async for message in websocket:
                await self.handle_message(client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"Client {client_id} disconnected")
        except Exception as e:
            logging.error(f"Client {client_id} error: {e}")
        finally:
            del self.clients[client_id]
            
    async def handle_message(self, client_id: int, message: str):
        try:
            data = json.loads(message)
            logging.info(f"Received from client {client_id}: {data}")
            
            if data['type'] == 'response':
                self.handle_response(client_id, data)
            elif data['type'] == 'heartbeat':
                self.clients[client_id]['last_heartbeat'] = datetime.now()
                
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON from client {client_id}: {e}")
            
    def handle_response(self, client_id: int, data: Dict[str, Any]):
        response_type = data.get('response_type', 'unknown')
        response_data = data.get('data', {})
        
        if response_type == 'uia_structure':
            logging.info(f"UIA structure from client {client_id}:")
            print(response_data.get('structure', 'No structure data'))
        elif response_type == 'processes':
            processes = response_data.get('processes', [])
            logging.info(f"Process list from client {client_id}: {len(processes)} processes")
            for proc in processes[:5]:  # Show top 5
                print(f"  - {proc['name']} (PID: {proc['id']}, Memory: {proc['memory']}MB)")
                
    async def send_command(self, client_id: int, command: str, data: Dict[str, Any] = None):
        if client_id in self.clients:
            client = self.clients[client_id]
            message = {
                'type': 'command',
                'command': command,
                'data': data or {},
                'timestamp': datetime.now().isoformat()
            }
            try:
                await client['ws'].send(json.dumps(message))
                logging.info(f"Sent command '{command}' to client {client_id}")
                return True
            except Exception as e:
                logging.error(f"Failed to send command to client {client_id}: {e}")
                return False
        else:
            logging.error(f"Client {client_id} not found")
            return False
            
    async def broadcast_command(self, command: str, data: Dict[str, Any] = None):
        tasks = []
        for client_id in list(self.clients.keys()):
            task = self.send_command(client_id, command, data)
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        logging.info(f"Broadcast command '{command}' to {sum(results)} clients")
        
    def list_clients(self):
        client_list = []
        for client_id, info in self.clients.items():
            client_list.append({
                'id': client_id,
                'ip': info['ip'],
                'connected_at': info['connected_at'].isoformat(),
                'last_heartbeat': info.get('last_heartbeat', info['connected_at']).isoformat()
            })
        return client_list
        
    async def command_handler(self):
        """Handle console commands"""
        while True:
            try:
                command = await asyncio.get_event_loop().run_in_executor(None, input)
                parts = command.strip().split()
                
                if not parts:
                    continue
                    
                cmd = parts[0].lower()
                
                if cmd == 'list':
                    clients = self.list_clients()
                    print(f"Connected clients ({len(clients)}):")
                    for client in clients:
                        print(f"  - Client {client['id']} from {client['ip']}")
                        
                elif cmd == 'uia':
                    if len(parts) > 1:
                        client_id = int(parts[1])
                        await self.send_command(client_id, 'get_uia_structure')
                    else:
                        await self.broadcast_command('get_uia_structure')
                        
                elif cmd == 'process':
                    if len(parts) > 1:
                        client_id = int(parts[1])
                        await self.send_command(client_id, 'get_processes')
                    else:
                        await self.broadcast_command('get_processes')
                        
                elif cmd == 'help':
                    print("Commands:")
                    print("  list - List connected clients")
                    print("  uia [client_id] - Get UIA structure")
                    print("  process [client_id] - Get process list")
                    print("  exit - Exit server")
                    
                elif cmd == 'exit':
                    break
                    
                else:
                    print(f"Unknown command: {cmd}. Type 'help' for available commands.")
                    
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                logging.error(f"Command handler error: {e}")
                
    async def start(self):
        logging.info(f"Starting CyberCorp Server on {self.host}:{self.port}")
        
        # Start WebSocket server
        server = await websockets.serve(self.handle_client, self.host, self.port)
        
        # Start command handler
        command_task = asyncio.create_task(self.command_handler())
        
        print("CyberCorp Server is running. Type 'help' for commands.")
        
        try:
            await command_task
        except KeyboardInterrupt:
            pass
        finally:
            server.close()
            await server.wait_closed()
            logging.info("Server stopped")

if __name__ == "__main__":
    server = CyberCorpServer()
    asyncio.run(server.start())