"""CyberCorp Server - Headless version (no console)"""

import asyncio
import sys
import os

# Import the server
sys.path.insert(0, os.path.dirname(__file__))
from server import CyberCorpServer

class HeadlessServer(CyberCorpServer):
    """Server without console interface"""
    
    async def _console_interface(self):
        """Override console interface to just wait"""
        print("\n=== CyberCorp Control Server (Headless) ===")
        print(f"Server running on port {self.port}")
        print("Clients can connect and send commands")
        print("Press Ctrl+C to stop")
        print()
        
        # Just keep the server running
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            print("\nServer shutting down...")

if __name__ == "__main__":
    server = HeadlessServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nServer stopped.")