"""Test all available information from controlled clients"""

import asyncio
import subprocess
import sys

async def test_all_commands():
    """Test all available commands on wjchk client"""
    
    commands = [
        # System information
        ("get_system_info", "System Information"),
        ("get_processes", "Running Processes"),
        ("get_windows", "Open Windows"),
        ("get_screen_size", "Screen Size"),
        
        # VSCode specific
        ("vscode_get_content", "VSCode Content"),
        
        # Can also test but might be intrusive
        # ("take_screenshot", "Screenshot"),
    ]
    
    print("Testing all available commands on wjchk client")
    print("=" * 80)
    
    for cmd, description in commands:
        print(f"\n[{description}] - Command: {cmd}")
        print("-" * 60)
        
        try:
            # Run the test command
            result = subprocess.run(
                [sys.executable, "cybercorp_test.py", "command", "wjchk", cmd],
                capture_output=True,
                text=True,
                cwd="."
            )
            
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"Error: {result.stderr}")
                
        except Exception as e:
            print(f"Failed to run command: {e}")
        
        # Small delay between commands
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_all_commands())