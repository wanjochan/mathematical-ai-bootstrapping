"""Test server with list_clients support on port 9997"""

import os
import sys

# Set test port
os.environ['CYBERCORP_PORT'] = '9997'

# Import and run server
from server import CyberCorpServer
import asyncio

print("Starting test server on port 9997 with list_clients support...")
server = CyberCorpServer(port=9997)
asyncio.run(server.start())