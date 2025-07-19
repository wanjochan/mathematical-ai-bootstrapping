"""Interactive console for CyberCorp server"""

import sys
import os

print("CyberCorp Server Console")
print("=" * 50)
print("This will connect to the server's stdin/stdout")
print()
print("Commands:")
print("  list - Show all connected clients")
print("  info <client_id> - Show client details")
print("  exit - Stop server")
print()
print("Enter commands (Ctrl+C to exit):")
print()

try:
    while True:
        command = input("server> ")
        print(f"Command sent: {command}")
        
        # Note: This is a placeholder. In reality, we need to connect
        # to the running server process. For now, just show what would be sent.
        
        if command == "exit":
            print("Exit command - server would shut down")
            break
            
except KeyboardInterrupt:
    print("\nConsole closed")