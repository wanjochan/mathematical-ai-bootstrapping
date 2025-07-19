"""
CyberCorp Unified Test Suite
高度抽象的测试脚本，通过命令行参数控制测试用例

Usage:
    python cybercorp_test.py <command> [options]

Commands:
    status              - Check system status
    list                - List all connected clients
    control <username>  - Control a specific client
    command <username> <cmd> [params] - Send command to client
    monitor             - Monitor server in real-time
    test-hotreload      - Test hot reload functionality

Examples:
    python cybercorp_test.py status
    python cybercorp_test.py list
    python cybercorp_test.py control wjchk
    python cybercorp_test.py command wjchk get_processes
    python cybercorp_test.py command wjchk system_info
"""

import asyncio
import websockets
import json
import sys
import os
import time
import argparse
from datetime import datetime
from typing import Optional, Dict, Any

class CyberCorpTester:
    def __init__(self, port=9998):
        self.port = port
        self.server_url = f'ws://localhost:{port}'
        
    async def connect(self, capabilities: Dict[str, bool] = None):
        """Connect to server with specified capabilities"""
        if capabilities is None:
            capabilities = {'management': True, 'control': True}
            
        try:
            websocket = await websockets.connect(self.server_url)
            
            # Register
            await websocket.send(json.dumps({
                'type': 'register',
                'user_session': f"{os.environ.get('USERNAME', 'unknown')}_tester",
                'client_start_time': datetime.now().isoformat(),
                'capabilities': capabilities,
                'system_info': {
                    'platform': 'Windows',
                    'hostname': os.environ.get('COMPUTERNAME', 'unknown')
                }
            }))
            
            # Wait for welcome
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            
            return websocket, welcome_data.get('client_id')
            
        except Exception as e:
            print(f"Connection error: {e}")
            return None, None
    
    async def check_status(self):
        """Check server and client status"""
        print("CyberCorp System Status")
        print("=" * 60)
        
        # Check ports
        import socket
        ports = [8888, 9998, 9999]
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            status = "IN USE" if result == 0 else "Available"
            print(f"Port {port}: {status}")
        
        # Try to connect and get client list
        websocket, client_id = await self.connect()
        if websocket:
            await websocket.send(json.dumps({
                'type': 'request',
                'command': 'list_clients'
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            
            if data['type'] == 'client_list':
                print(f"\nConnected clients: {len(data['clients'])}")
                for client in data['clients']:
                    print(f"  - {client['user_session']} @ {client['hostname']} (ID: {client['id']})")
            
            await websocket.close()
    
    async def list_clients(self):
        """List all connected clients with details"""
        websocket, client_id = await self.connect()
        if not websocket:
            return
            
        await websocket.send(json.dumps({
            'type': 'request',
            'command': 'list_clients'
        }))
        
        response = await websocket.recv()
        data = json.loads(response)
        
        if data['type'] == 'client_list':
            print(f"\nConnected Clients ({len(data['clients'])})")
            print("=" * 80)
            
            for client in data['clients']:
                print(f"\nClient: {client['id']}")
                print(f"  User: {client.get('user_session', 'unknown')}")
                print(f"  Host: {client.get('hostname', 'unknown')}")
                print(f"  IP: {client.get('ip', 'unknown')}")
                print(f"  Connected: {client.get('connected_at', 'unknown')}")
                print(f"  Started: {client.get('client_start_time', 'unknown')}")
                print(f"  Capabilities: {json.dumps(client.get('capabilities', {}))}")
        
        await websocket.close()
    
    async def control_client(self, target_username: str, command: str = 'get_processes', params: Dict = None):
        """Send command to specific client"""
        websocket, controller_id = await self.connect()
        if not websocket:
            return
            
        # Get client list
        await websocket.send(json.dumps({
            'type': 'request',
            'command': 'list_clients'
        }))
        
        response = await websocket.recv()
        data = json.loads(response)
        
        target_client_id = None
        if data['type'] == 'client_list':
            for client in data['clients']:
                if client.get('user_session') == target_username:
                    target_client_id = client['id']
                    break
        
        if not target_client_id:
            print(f"Client '{target_username}' not found")
            await websocket.close()
            return
        
        print(f"Sending command '{command}' to {target_username} (ID: {target_client_id})")
        
        # Send command
        await websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': target_client_id,
            'command': {
                'type': 'command',
                'command': command,
                'params': params or {}
            }
        }))
        
        # Wait for acknowledgment
        ack = await websocket.recv()
        ack_data = json.loads(ack)
        if ack_data.get('type') == 'forward_ack':
            print("Command sent successfully")
        
        # Wait for result
        print("Waiting for response...")
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                result = json.loads(response)
                
                if result.get('type') == 'command_result' and result.get('from_client') == target_client_id:
                    print(f"\nResponse from {target_username}:")
                    print("-" * 60)
                    
                    if result.get('error'):
                        print(f"Error: {result['error']}")
                    else:
                        self._display_result(command, result.get('result'))
                    
                    break
                    
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                break
        
        await websocket.close()
    
    def _display_result(self, command: str, result: Any):
        """Display command result based on command type"""
        if command == 'get_processes' and isinstance(result, list):
            print(f"Total processes: {len(result)}")
            print("\nTop 10 processes by memory:")
            for i, proc in enumerate(result[:10], 1):
                print(f"{i}. {proc.get('name', 'unknown')} (PID: {proc.get('pid')}) - Memory: {proc.get('memory_mb', 0):.1f} MB")
        
        elif command == 'system_info' and isinstance(result, dict):
            info = result.get('system_info', {})
            print(f"Platform: {info.get('platform')} {info.get('platform_release')}")
            print(f"Architecture: {info.get('architecture')}")
            print(f"Hostname: {info.get('hostname')}")
            print(f"User: {info.get('user')}")
            print(f"CPU: {info.get('cpu_count')} cores, {info.get('cpu_percent')}% usage")
            mem = info.get('memory', {})
            print(f"Memory: {mem.get('available')}GB / {mem.get('total')}GB ({mem.get('percent')}% used)")
            disk = info.get('disk', {})
            print(f"Disk: {disk.get('free')}GB / {disk.get('total')}GB ({disk.get('percent')}% used)")
        
        else:
            # Generic display
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    async def monitor_server(self, duration: int = 60):
        """Monitor server activity in real-time"""
        print(f"Monitoring server for {duration} seconds...")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        websocket, client_id = await self.connect({'management': True, 'monitor': True})
        if not websocket:
            return
        
        start_time = time.time()
        try:
            while time.time() - start_time < duration:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"[{timestamp}] {data.get('type', 'unknown')}: {data}")
                except asyncio.TimeoutError:
                    pass
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
        
        await websocket.close()
    
    async def test_hotreload(self):
        """Test hot reload functionality"""
        print("Testing Hot Reload")
        print("=" * 60)
        
        print("1. Creating test plugin...")
        test_plugin = """
# Test plugin for hot reload
from server_hotreload import register_command

def handle_test_hotreload(client, params):
    return {
        'success': True,
        'message': 'Hot reload test successful!',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }

register_command('test_hotreload', handle_test_hotreload)
print("Test hotreload plugin loaded!")
"""
        
        plugin_path = os.path.join(os.path.dirname(__file__), 'plugins', 'test_hotreload.py')
        with open(plugin_path, 'w') as f:
            f.write(test_plugin)
        
        print(f"Created plugin: {plugin_path}")
        print("Waiting for hot reload...")
        await asyncio.sleep(2)
        
        print("\n2. Testing new command...")
        # Test with the first available client
        websocket, _ = await self.connect()
        if websocket:
            await websocket.send(json.dumps({
                'type': 'request',
                'command': 'list_clients'
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            
            if data['type'] == 'client_list' and data['clients']:
                target = data['clients'][0]
                print(f"Using client: {target['user_session']} (ID: {target['id']})")
                
                # Send test command
                await self.control_client(target['user_session'], 'test_hotreload')
            
            await websocket.close()
        
        print("\n3. Cleaning up...")
        os.remove(plugin_path)
        print("Test completed!")

async def main():
    parser = argparse.ArgumentParser(description='CyberCorp Unified Test Suite')
    parser.add_argument('command', choices=['status', 'list', 'control', 'command', 'monitor', 'test-hotreload'],
                       help='Test command to run')
    parser.add_argument('username', nargs='?', help='Target username for control/command')
    parser.add_argument('cmd', nargs='?', help='Command to send')
    parser.add_argument('--params', type=json.loads, help='Command parameters as JSON')
    parser.add_argument('--port', type=int, default=9998, help='Server port (default: 9998)')
    parser.add_argument('--duration', type=int, default=60, help='Monitor duration in seconds')
    
    args = parser.parse_args()
    
    tester = CyberCorpTester(port=args.port)
    
    if args.command == 'status':
        await tester.check_status()
    
    elif args.command == 'list':
        await tester.list_clients()
    
    elif args.command == 'control':
        if not args.username:
            print("Error: username required for control command")
            sys.exit(1)
        await tester.control_client(args.username)
    
    elif args.command == 'command':
        if not args.username or not args.cmd:
            print("Error: username and cmd required for command")
            sys.exit(1)
        await tester.control_client(args.username, args.cmd, args.params)
    
    elif args.command == 'monitor':
        await tester.monitor_server(args.duration)
    
    elif args.command == 'test-hotreload':
        await tester.test_hotreload()

if __name__ == "__main__":
    asyncio.run(main())