"""
Start a test client with latest code
"""

import asyncio
import logging
from client import CyberCorpClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    client = CyberCorpClient()
    await client.run()

if __name__ == '__main__':
    print("Starting test client with latest code...")
    print("This client will have the find_cursor_windows command")
    asyncio.run(main())