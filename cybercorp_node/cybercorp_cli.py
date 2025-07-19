"""CyberCorp Node Unified CLI Tool

A unified command-line interface for all CyberCorp Node operations.
Replaces multiple test scripts with a single, extensible tool.
"""

import asyncio
import argparse
import json
import sys
from typing import Optional, Dict, Any

from utils import (
    CyberCorpClient,
    ClientManager,
    CommandForwarder,
    DataPersistence,
    VSCodeUIAnalyzer,
    VSCodeAutomation,
    ResponseHandler
)


class CyberCorpCLI:
    """Main CLI class for CyberCorp Node operations"""
    
    def __init__(self):
        self.client = None
        self.client_manager = None
        self.forwarder = None
        self.persistence = DataPersistence()
        self.response_handler = ResponseHandler()
        
    async def connect(self, port: int = 9998, client_type: str = "cli"):
        """Connect to CyberCorp server"""
        self.client = CyberCorpClient(client_type=client_type, port=port)
        await self.client.connect()
        self.client_manager = ClientManager(self.client)
        self.forwarder = CommandForwarder(self.client)
        
    async def disconnect(self):
        """Disconnect from server"""
        if self.client:
            await self.client.disconnect()
            
    # Command implementations
    
    async def cmd_status(self, args):
        """Check server status"""
        try:
            print(f"Connecting to server on port {args.port}...")
            await self.connect(port=args.port)
            
            # Get client count
            client_count = await self.client_manager.get_client_count()
            print(f"✓ Server is running")
            print(f"✓ Connected clients: {client_count}")
            
            if args.verbose:
                clients = await self.client_manager.list_clients()
                for client in clients:
                    print(f"\n{self.client_manager.format_client_info(client)}")
                    
        except Exception as e:
            print(f"✗ Server connection failed: {e}")
            return 1
        finally:
            await self.disconnect()
            
        return 0
        
    async def cmd_list(self, args):
        """List all connected clients"""
        try:
            await self.connect(port=args.port)
            clients = await self.client_manager.list_clients()
            
            if not clients:
                print("No clients connected")
                return 0
                
            print(f"Connected clients ({len(clients)}):")
            print("-" * 60)
            
            for client in clients:
                print(f"\nID: {client['id']}")
                print(f"  Session: {client['user_session']}")
                print(f"  Status: {client.get('status', 'unknown')}")
                print(f"  Connected: {client.get('connected_at', 'unknown')}")
                
                if args.capabilities:
                    caps = client.get('capabilities', {})
                    if caps:
                        print("  Capabilities:")
                        for cap, enabled in caps.items():
                            if enabled:
                                print(f"    - {cap}")
                                
            if args.save:
                filepath = self.persistence.save_json(clients, "client_list")
                print(f"\nSaved to: {filepath}")
                
        except Exception as e:
            print(f"Error: {e}")
            return 1
        finally:
            await self.disconnect()
            
        return 0
        
    async def cmd_command(self, args):
        """Send command to specific client"""
        try:
            await self.connect(port=args.port)
            
            # Find target client
            target_client = await self.client_manager.find_client_by_username(args.target)
            if not target_client:
                print(f"Client '{args.target}' not found")
                return 1
                
            client_id = target_client['id']
            print(f"Found client: {client_id}")
            
            # Parse parameters
            params = None
            if args.params:
                try:
                    params = json.loads(args.params)
                except json.JSONDecodeError:
                    print(f"Invalid JSON parameters: {args.params}")
                    return 1
                    
            # Send command
            print(f"Sending command '{args.command}' to {args.target}...")
            
            try:
                result = await self.forwarder.forward_command(
                    client_id, args.command, params, timeout=args.timeout
                )
                
                # Display result
                if args.json:
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                else:
                    print("Result:", result)
                    
                # Save if requested
                if args.save:
                    filepath = self.persistence.save_json(result, f"cmd_{args.command}")
                    print(f"\nSaved to: {filepath}")
                    
            except asyncio.TimeoutError:
                print(f"Command timed out after {args.timeout} seconds")
                return 1
                
        except Exception as e:
            print(f"Error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
        finally:
            await self.disconnect()
            
        return 0
        
    async def cmd_control(self, args):
        """Interactive control mode for VSCode"""
        try:
            await self.connect(port=args.port)
            
            # Find target client
            target_client = await self.client_manager.find_client_by_username(args.target)
            if not target_client:
                print(f"Client '{args.target}' not found")
                return 1
                
            client_id = target_client['id']
            automation = VSCodeAutomation(self.forwarder)
            
            print(f"Connected to {args.target} (ID: {client_id})")
            print("Interactive control mode. Commands:")
            print("  content    - Get VSCode content")
            print("  type TEXT  - Type text")
            print("  keys KEYS  - Send keys (e.g., ctrl+s)")
            print("  input NAME TEXT - Background input")
            print("  click NAME - Background click")
            print("  screenshot - Take screenshot")
            print("  quit       - Exit control mode")
            print("-" * 40)
            
            while True:
                try:
                    cmd = input("> ").strip()
                    if not cmd:
                        continue
                        
                    parts = cmd.split(None, 2)
                    command = parts[0].lower()
                    
                    if command == "quit":
                        break
                        
                    elif command == "content":
                        result = await automation.get_content(client_id)
                        if args.save:
                            filepath = self.persistence.save_json(result, "vscode_content")
                            print(f"Saved to: {filepath}")
                        else:
                            summary = VSCodeUIAnalyzer().get_ui_summary(result)
                            print(json.dumps(summary, indent=2))
                            
                    elif command == "type" and len(parts) >= 2:
                        text = ' '.join(parts[1:])
                        result = await automation.type_text(client_id, text)
                        print("Done" if result.get('success') else f"Failed: {result.get('error')}")
                        
                    elif command == "keys" and len(parts) >= 2:
                        keys = parts[1]
                        result = await automation.send_keys(client_id, keys)
                        print("Done" if result.get('success') else f"Failed: {result.get('error')}")
                        
                    elif command == "input" and len(parts) >= 3:
                        element_name = parts[1]
                        text = parts[2]
                        result = await automation.background_input(client_id, element_name, text)
                        print("Done" if result.get('success') else f"Failed: {result.get('error')}")
                        
                    elif command == "click" and len(parts) >= 2:
                        element_name = ' '.join(parts[1:])
                        result = await automation.background_click(client_id, element_name)
                        print("Done" if result.get('success') else f"Failed: {result.get('error')}")
                        
                    elif command == "screenshot":
                        result = await automation.take_screenshot(client_id)
                        if result.get('success'):
                            print(f"Screenshot saved: {result.get('path')}")
                        else:
                            print(f"Failed: {result.get('error')}")
                            
                    else:
                        print("Unknown command")
                        
                except KeyboardInterrupt:
                    print("\nUse 'quit' to exit")
                except Exception as e:
                    print(f"Error: {e}")
                    
        except Exception as e:
            print(f"Error: {e}")
            return 1
        finally:
            await self.disconnect()
            
        return 0
        
    async def cmd_roo(self, args):
        """Roo Code specific operations"""
        try:
            await self.connect(port=args.port)
            
            # Find target client
            target_client = await self.client_manager.find_client_by_username(args.target)
            if not target_client:
                print(f"Client '{args.target}' not found")
                return 1
                
            client_id = target_client['id']
            automation = VSCodeAutomation(self.forwarder)
            
            if args.action == "send":
                print(f"Sending message to Roo Code: {args.message}")
                result = await automation.send_to_roo_code(
                    client_id, args.message, use_background=not args.foreground
                )
                
                if result['success']:
                    print("✓ Message sent successfully")
                else:
                    print(f"✗ Failed: {result.get('error')}")
                    
            elif args.action == "check":
                print("Checking Roo Code state...")
                state = await automation.get_roo_code_state(client_id)
                
                if state['has_roo_code']:
                    print("✓ Roo Code is active")
                    if state['conversation']:
                        print(f"\nConversation preview:")
                        print(state['conversation'][:500] + "...")
                else:
                    print("✗ Roo Code not found")
                    
                if args.save:
                    filepath = self.persistence.save_json(state, "roo_state")
                    print(f"\nSaved to: {filepath}")
                    
        except Exception as e:
            print(f"Error: {e}")
            return 1
        finally:
            await self.disconnect()
            
        return 0
        
    async def cmd_batch(self, args):
        """Execute batch commands from file"""
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                commands = json.load(f)
                
            await self.connect(port=args.port)
            
            # Find target client
            target_client = await self.client_manager.find_client_by_username(args.target)
            if not target_client:
                print(f"Client '{args.target}' not found")
                return 1
                
            client_id = target_client['id']
            
            # Execute commands
            print(f"Executing {len(commands)} commands...")
            
            command_list = [(cmd['command'], cmd.get('params')) for cmd in commands]
            results = await self.forwarder.batch_forward(
                client_id, command_list, stop_on_error=args.stop_on_error
            )
            
            # Display results
            success_count = sum(1 for r in results if r['success'])
            print(f"\nCompleted: {success_count}/{len(results)} successful")
            
            if args.verbose:
                for i, result in enumerate(results):
                    print(f"\n[{i+1}] {result['command']}: ", end="")
                    if result['success']:
                        print("✓ Success")
                    else:
                        print(f"✗ Failed - {result['error']}")
                        
            if args.save:
                filepath = self.persistence.save_json(results, "batch_results")
                print(f"\nSaved results to: {filepath}")
                
        except Exception as e:
            print(f"Error: {e}")
            return 1
        finally:
            await self.disconnect()
            
        return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="CyberCorp Node Unified CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-p', '--port', type=int, default=9998,
                       help='Server port (default: 9998)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check server status')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List connected clients')
    list_parser.add_argument('-c', '--capabilities', action='store_true',
                           help='Show client capabilities')
    list_parser.add_argument('-s', '--save', action='store_true',
                           help='Save output to file')
    
    # Command execution
    cmd_parser = subparsers.add_parser('command', help='Send command to client')
    cmd_parser.add_argument('target', help='Target client username')
    cmd_parser.add_argument('command', help='Command to execute')
    cmd_parser.add_argument('--params', help='JSON parameters')
    cmd_parser.add_argument('-t', '--timeout', type=float, default=5.0,
                          help='Command timeout (default: 5.0)')
    cmd_parser.add_argument('-j', '--json', action='store_true',
                          help='Output as JSON')
    cmd_parser.add_argument('-s', '--save', action='store_true',
                          help='Save output to file')
    
    # Interactive control
    control_parser = subparsers.add_parser('control', help='Interactive control mode')
    control_parser.add_argument('target', help='Target client username')
    control_parser.add_argument('-s', '--save', action='store_true',
                              help='Save outputs to files')
    
    # Roo Code operations
    roo_parser = subparsers.add_parser('roo', help='Roo Code operations')
    roo_parser.add_argument('target', help='Target client username')
    roo_parser.add_argument('action', choices=['send', 'check'],
                          help='Action to perform')
    roo_parser.add_argument('-m', '--message', help='Message to send (for send action)')
    roo_parser.add_argument('-f', '--foreground', action='store_true',
                          help='Use foreground operations')
    roo_parser.add_argument('-s', '--save', action='store_true',
                          help='Save output to file')
    
    # Batch operations
    batch_parser = subparsers.add_parser('batch', help='Execute batch commands')
    batch_parser.add_argument('target', help='Target client username')
    batch_parser.add_argument('file', help='JSON file with commands')
    batch_parser.add_argument('--stop-on-error', action='store_true',
                            help='Stop execution on first error')
    batch_parser.add_argument('-s', '--save', action='store_true',
                            help='Save results to file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    # Execute command
    cli = CyberCorpCLI()
    
    command_map = {
        'status': cli.cmd_status,
        'list': cli.cmd_list,
        'command': cli.cmd_command,
        'control': cli.cmd_control,
        'roo': cli.cmd_roo,
        'batch': cli.cmd_batch
    }
    
    handler = command_map.get(args.command)
    if handler:
        try:
            return asyncio.run(handler(args))
        except KeyboardInterrupt:
            print("\nInterrupted")
            return 1
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())