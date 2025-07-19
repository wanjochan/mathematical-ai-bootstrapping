"""Migration guide from old test scripts to new unified CLI

This script shows how to migrate from the old individual test scripts
to the new unified cybercorp_cli.py tool.
"""

import os

# Mapping of old scripts to new CLI commands
MIGRATION_MAP = {
    # Status and monitoring
    "check_status.py": "python cybercorp_cli.py status",
    "monitor_server.py": "python cybercorp_cli.py status -v",
    
    # Client listing
    "list_clients_now.py": "python cybercorp_cli.py list",
    "test_list_clients.py": "python cybercorp_cli.py list -c",
    "show_client_info.py": "python cybercorp_cli.py list -c -v",
    
    # Basic commands
    "test_control.py": "python cybercorp_cli.py control <username>",
    "test_all_info.py": "python cybercorp_cli.py command <username> get_system_info",
    "get_vscode_structure.py": "python cybercorp_cli.py command <username> vscode_get_content -s",
    
    # Roo Code operations
    "send_to_roo_code.py": "python cybercorp_cli.py roo <username> send -m 'Your message'",
    "check_roo_response.py": "python cybercorp_cli.py roo <username> check -s",
    "interact_with_roo_code.py": "python cybercorp_cli.py roo <username> send -m 'Your message'",
    "background_roo_rpa.py": "python cybercorp_cli.py roo <username> send -m 'Your message'",
    
    # Analysis scripts
    "analyze_vscode_content.py": "python cybercorp_cli.py command <username> vscode_get_content -s",
    "analyze_roo_task.py": "python cybercorp_cli.py roo <username> check -s",
    
    # Test scripts (replaced by unified tool)
    "cybercorp_test.py": "python cybercorp_cli.py",
    "test_simple_connection.py": "python cybercorp_cli.py status",
    "test_multi_client.py": "python cybercorp_cli.py list",
    
    # Window operations
    "save_window_info.py": "python cybercorp_cli.py command <username> get_windows -s",
    "format_windows.py": "python cybercorp_cli.py command <username> get_windows -j",
}

# Scripts that are now part of the utility classes
ABSORBED_SCRIPTS = [
    "simple_server.py",  # Use server.py or server_hotreload.py directly
    "simple_client.py",  # Use client.py directly
    "test_stable.py",    # Stability is built into utils
    "test_connection.py",  # Connection testing is built into CLI
    "server_console.py",  # Use CLI interactive mode instead
    "restart_server.py",  # Manual process management
    "kill_server.py",     # Manual process management
    "update_server.py",   # Use hot reload server
    "start_server_background.py",  # Use batch files
    "start_hotreload_background.py",  # Use batch files
    "notify_client_restart.py",  # Built into client reconnect
    "rpa_failure_analysis.py",  # Error handling built into utils
    "robust_roo_code_rpa.py",  # Robustness built into utils
    "enhanced_window_control.py",  # Built into VSCodeAutomation
    "simple_roo_check.py",  # Use roo check command
    "test_server_hotreload.py",  # Testing built into CLI
    "test_client_9998.py",  # Port configuration in CLI
    "test_server_with_list.py",  # List functionality in CLI
]


def print_migration_guide():
    """Print migration guide"""
    print("=" * 80)
    print("CyberCorp Node Migration Guide")
    print("From individual test scripts to unified CLI")
    print("=" * 80)
    print()
    
    print("## Script Migration Map")
    print("-" * 80)
    
    for old_script, new_command in MIGRATION_MAP.items():
        print(f"OLD: python {old_script}")
        print(f"NEW: {new_command}")
        print()
    
    print("\n## Scripts Now Part of Utility Classes")
    print("-" * 80)
    print("These scripts are no longer needed as their functionality is built into the utilities:")
    print()
    
    for script in ABSORBED_SCRIPTS:
        print(f"  - {script}")
    
    print("\n## New Features Available")
    print("-" * 80)
    print("1. Batch operations: Execute multiple commands from JSON file")
    print("   python cybercorp_cli.py batch <username> examples/batch_commands.json")
    print()
    print("2. Interactive control mode: Control VSCode interactively")
    print("   python cybercorp_cli.py control <username>")
    print()
    print("3. JSON output: Get structured output for scripting")
    print("   python cybercorp_cli.py command <username> get_processes -j")
    print()
    print("4. Save outputs: Automatically save results to var/ directory")
    print("   python cybercorp_cli.py command <username> vscode_get_content -s")
    print()
    
    print("\n## Quick Start Examples")
    print("-" * 80)
    print("# Check server status")
    print("python cybercorp_cli.py status")
    print()
    print("# List all clients with capabilities")
    print("python cybercorp_cli.py list -c")
    print()
    print("# Send command to specific client")
    print("python cybercorp_cli.py command wjchk get_windows")
    print()
    print("# Send message to Roo Code")
    print('python cybercorp_cli.py roo wjchk send -m "Hello Roo"')
    print()
    print("# Interactive control")
    print("python cybercorp_cli.py control wjchk")
    print()
    
    print("\n## Advantages of the New System")
    print("-" * 80)
    print("1. Single entry point for all operations")
    print("2. Consistent error handling and output format")
    print("3. Built-in retry and timeout handling")
    print("4. Automatic result saving with timestamps")
    print("5. Batch operations support")
    print("6. Interactive and non-interactive modes")
    print("7. Extensible command system")
    print("8. Reduced code duplication")
    print("9. Better testability and maintainability")
    print()


def check_old_scripts():
    """Check which old scripts exist in the current directory"""
    print("\n## Old Scripts Found in Current Directory")
    print("-" * 80)
    
    found_scripts = []
    all_old_scripts = list(MIGRATION_MAP.keys()) + ABSORBED_SCRIPTS
    
    for script in all_old_scripts:
        if os.path.exists(script):
            found_scripts.append(script)
    
    if found_scripts:
        print(f"Found {len(found_scripts)} old scripts that can be migrated:")
        for script in found_scripts:
            print(f"  - {script}")
        print("\nConsider removing these after verifying the new CLI works for your needs.")
    else:
        print("No old scripts found. Migration may already be complete!")
    
    return found_scripts


def create_migration_batch():
    """Create a batch file for common migrations"""
    batch_content = """@echo off
REM CyberCorp Node CLI Examples
REM Replace <username> with actual target username

echo === Server Status ===
python cybercorp_cli.py status

echo.
echo === List Clients ===
python cybercorp_cli.py list -c

echo.
echo === Get System Info ===
python cybercorp_cli.py command <username> get_system_info

echo.
echo === Get VSCode Content ===
python cybercorp_cli.py command <username> vscode_get_content -s

echo.
echo === Check Roo Code ===
python cybercorp_cli.py roo <username> check

echo.
echo Done! Check var/ directory for saved outputs.
pause
"""
    
    with open("cli_examples.bat", "w") as f:
        f.write(batch_content)
    
    print("\nCreated cli_examples.bat with common CLI usage examples.")


if __name__ == "__main__":
    print_migration_guide()
    found = check_old_scripts()
    
    if found:
        response = input("\nCreate example batch file? (y/n): ")
        if response.lower() == 'y':
            create_migration_batch()
    
    print("\nMigration guide complete!")
    print("Start using: python cybercorp_cli.py --help")