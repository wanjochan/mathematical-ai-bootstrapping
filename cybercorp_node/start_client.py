"""
Simple startup script for CyberCorp Client with auto-restart
"""

import sys
import os
import subprocess
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('StartClient')

def main():
    """Start the client with watchdog"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    watchdog_script = os.path.join(script_dir, 'client_watchdog.py')
    
    if not os.path.exists(watchdog_script):
        logger.error(f"Watchdog script not found: {watchdog_script}")
        return 1
    
    logger.info("Starting CyberCorp Client with auto-restart...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Run the watchdog
        process = subprocess.run(
            [sys.executable, watchdog_script],
            cwd=script_dir
        )
        return process.returncode
        
    except KeyboardInterrupt:
        logger.info("\nStopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())