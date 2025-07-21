"""
CyberCorp Client Watchdog - Monitors and restarts the client on crash
"""

import asyncio
import subprocess
import sys
import os
import time
import logging
import json
from datetime import datetime
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ClientWatchdog')

class ClientWatchdog:
    def __init__(self, client_script: str = "client.py", max_restarts: int = 10, 
                 restart_window: int = 3600, restart_delay: int = 5):
        """
        Initialize the watchdog
        
        Args:
            client_script: Path to the client script
            max_restarts: Maximum restarts within the restart window
            restart_window: Time window in seconds for counting restarts
            restart_delay: Delay in seconds before restarting
        """
        self.client_script = client_script
        self.max_restarts = max_restarts
        self.restart_window = restart_window
        self.restart_delay = restart_delay
        self.restart_times = []
        self.process: Optional[subprocess.Popen] = None
        self.running = True
        
    def cleanup_old_restarts(self):
        """Remove restart times outside the window"""
        current_time = time.time()
        self.restart_times = [
            t for t in self.restart_times 
            if current_time - t < self.restart_window
        ]
    
    def can_restart(self) -> bool:
        """Check if we can restart the client"""
        self.cleanup_old_restarts()
        return len(self.restart_times) < self.max_restarts
    
    def record_restart(self):
        """Record a restart time"""
        self.restart_times.append(time.time())
        logger.info(f"Restart recorded. Total restarts in window: {len(self.restart_times)}")
    
    async def start_client(self):
        """Start the client process"""
        try:
            logger.info(f"Starting client: {self.client_script}")
            
            # Use the same Python interpreter as the watchdog
            self.process = subprocess.Popen(
                [sys.executable, self.client_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            logger.info(f"Client started with PID: {self.process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start client: {e}")
            return False
    
    async def monitor_client(self):
        """Monitor the client process and output"""
        if not self.process:
            return
            
        try:
            # Read and log client output
            while self.process.poll() is None and self.running:
                if self.process.stdout:
                    line = self.process.stdout.readline()
                    if line:
                        # Log client output with prefix
                        logger.info(f"[CLIENT] {line.strip()}")
                await asyncio.sleep(0.1)
            
            # Process has exited
            exit_code = self.process.returncode
            
            if exit_code is not None:
                if exit_code == 0:
                    logger.info("Client exited normally")
                else:
                    logger.error(f"Client crashed with exit code: {exit_code}")
                    
        except Exception as e:
            logger.error(f"Error monitoring client: {e}")
    
    async def run(self):
        """Main watchdog loop"""
        logger.info("Client Watchdog started")
        
        while self.running:
            if not self.can_restart():
                logger.error(f"Maximum restarts ({self.max_restarts}) reached in {self.restart_window}s window")
                logger.error("Watchdog stopping to prevent restart loop")
                break
            
            # Start the client
            if await self.start_client():
                self.record_restart()
                
                # Monitor the client
                await self.monitor_client()
                
                # Client has exited
                if self.running and self.process.returncode != 0:
                    logger.info(f"Restarting client in {self.restart_delay} seconds...")
                    await asyncio.sleep(self.restart_delay)
                else:
                    # Normal exit or watchdog stopped
                    break
            else:
                logger.error("Failed to start client. Retrying...")
                await asyncio.sleep(self.restart_delay)
        
        logger.info("Watchdog stopped")
    
    def stop(self):
        """Stop the watchdog and client"""
        logger.info("Stopping watchdog...")
        self.running = False
        
        if self.process and self.process.poll() is None:
            logger.info("Terminating client process...")
            try:
                self.process.terminate()
                time.sleep(2)
                if self.process.poll() is None:
                    logger.warning("Force killing client process...")
                    self.process.kill()
            except Exception as e:
                logger.error(f"Error stopping client: {e}")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CyberCorp Client Watchdog')
    parser.add_argument('--client', default='client.py', help='Path to client script')
    parser.add_argument('--max-restarts', type=int, default=10, 
                       help='Maximum restarts within window')
    parser.add_argument('--restart-window', type=int, default=3600,
                       help='Time window for counting restarts (seconds)')
    parser.add_argument('--restart-delay', type=int, default=5,
                       help='Delay before restart (seconds)')
    
    args = parser.parse_args()
    
    # Check if client script exists
    if not os.path.exists(args.client):
        logger.error(f"Client script not found: {args.client}")
        sys.exit(1)
    
    watchdog = ClientWatchdog(
        client_script=args.client,
        max_restarts=args.max_restarts,
        restart_window=args.restart_window,
        restart_delay=args.restart_delay
    )
    
    try:
        await watchdog.run()
    except KeyboardInterrupt:
        logger.info("Watchdog interrupted by user")
        watchdog.stop()

if __name__ == "__main__":
    asyncio.run(main())