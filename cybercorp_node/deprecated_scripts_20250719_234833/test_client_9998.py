"""Test client connection to port 9998"""

import os
os.environ['CYBERCORP_PORT'] = '9998'

# Import and run client
from client import CyberCorpClient
import asyncio

print("Starting client on port 9998...")
client = CyberCorpClient()
asyncio.run(client.run())