"""
Cleanup old test scripts that have been integrated into unified tools
"""

import os
import shutil
from datetime import datetime

# Scripts that have been integrated into cybercorp_test_suite.py or cybercorp_cli.py
DEPRECATED_SCRIPTS = [
    # Integrated into test suite
    'test_stable.py',
    'test_connection.py', 
    'test_simple_connection.py',
    'test_multi_client.py',
    'test_server_with_list.py',
    'test_client_9998.py',
    'test_server_hotreload.py',
    
    # Integrated into CLI
    'check_status.py',
    'list_clients_now.py',
    'show_client_info.py',
    'test_list_clients.py',
    'test_control.py',
    'test_all_info.py',
    
    # VSCode/Roo specific - integrated
    'get_vscode_structure.py',
    'send_to_roo_code.py',
    'interact_with_roo_code.py',
    'check_roo_response.py',
    'simple_roo_check.py',
    'analyze_vscode_content.py',
    'analyze_roo_task.py',
    
    # Utility scripts - integrated
    'format_windows.py',
    'save_window_info.py',
    
    # Server management - keep as separate tools
    # 'monitor_server.py',
    # 'restart_server.py', 
    # 'kill_server.py',
    # 'update_server.py',
    # 'start_server_background.py',
    # 'start_hotreload_background.py',
    # 'notify_client_restart.py',
    
    # Simple versions - no longer needed
    'simple_server.py',
    'simple_client.py',
]

# Scripts to keep (core functionality)
KEEP_SCRIPTS = [
    'server.py',
    'client.py',
    'server_hotreload.py',
    'server_console.py',
    'server_headless.py',
    'cybercorp_cli.py',
    'cybercorp_test.py',
    'cybercorp_test_suite.py',
    'migrate_to_cli.py',
    
    # New feature tests (keep for now)
    'test_mouse_drag.py',
    'test_ocr_engines.py', 
    'test_vision_model.py',
    'test_new_features.py',
    
    # Server management (keep)
    'monitor_server.py',
    'restart_server.py',
    'kill_server.py',
    'update_server.py',
    'start_server_background.py',
    'start_hotreload_background.py',
    'notify_client_restart.py',
    
    # Analysis scripts
    'enhanced_window_control.py',
    'background_roo_rpa.py',
    'robust_roo_code_rpa.py',
    'rpa_failure_analysis.py',
]

def cleanup_scripts(dry_run=True):
    """Clean up deprecated scripts"""
    
    # Create backup directory
    backup_dir = f"deprecated_scripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not dry_run:
        os.makedirs(backup_dir, exist_ok=True)
    
    print("CyberCorp Node Script Cleanup")
    print("=" * 60)
    
    deprecated_found = []
    keep_found = []
    
    # Check all Python files
    for filename in os.listdir('.'):
        if filename.endswith('.py'):
            if filename in DEPRECATED_SCRIPTS:
                deprecated_found.append(filename)
            elif filename in KEEP_SCRIPTS:
                keep_found.append(filename)
                
    print(f"\nFound {len(deprecated_found)} deprecated scripts")
    print(f"Found {len(keep_found)} scripts to keep")
    
    if dry_run:
        print("\n[DRY RUN MODE - No files will be moved]")
        
    print("\nDeprecated scripts to be backed up:")
    for script in sorted(deprecated_found):
        print(f"  - {script}")
        if not dry_run:
            shutil.move(script, os.path.join(backup_dir, script))
            
    print("\nScripts to keep:")
    for script in sorted(keep_found):
        print(f"  + {script}")
        
    if not dry_run and deprecated_found:
        print(f"\nMoved {len(deprecated_found)} files to {backup_dir}/")
        
        # Create a manifest
        manifest_path = os.path.join(backup_dir, 'MANIFEST.txt')
        with open(manifest_path, 'w') as f:
            f.write("Deprecated CyberCorp Node Scripts\n")
            f.write(f"Backed up on: {datetime.now().isoformat()}\n")
            f.write("\nThese scripts have been integrated into:\n")
            f.write("- cybercorp_cli.py (unified CLI tool)\n")
            f.write("- cybercorp_test_suite.py (unified test suite)\n")
            f.write("\nDeprecated files:\n")
            for script in sorted(deprecated_found):
                f.write(f"- {script}\n")
                
    # Show migration guide
    print("\n" + "=" * 60)
    print("Migration Guide")
    print("=" * 60)
    print("\nUse the new unified tools instead:")
    print("\n1. For testing:")
    print("   python cybercorp_test_suite.py --help")
    print("   python cybercorp_test_suite.py status list -t wjchk")
    print("\n2. For CLI operations:")
    print("   python cybercorp_cli.py --help")
    print("   python cybercorp_cli.py command wjchk get_windows")
    print("\n3. For specific tests:")
    print("   python cybercorp_test_suite.py ocr drag win32 -t wjchk")


def show_statistics():
    """Show file statistics"""
    print("\n" + "=" * 60)
    print("File Statistics")
    print("=" * 60)
    
    py_files = [f for f in os.listdir('.') if f.endswith('.py')]
    test_files = [f for f in py_files if f.startswith('test_')]
    util_files = [f for f in py_files if any(f.startswith(p) for p in 
                 ['check_', 'show_', 'get_', 'send_', 'analyze_', 'format_', 'save_', 'interact_', 'simple_'])]
    
    print(f"Total .py files: {len(py_files)}")
    print(f"Test files: {len(test_files)}")
    print(f"Utility files: {len(util_files)}")
    print(f"Core files: {len(py_files) - len(test_files) - len(util_files)}")
    
    print(f"\nAfter cleanup: ~{len(KEEP_SCRIPTS)} files (from {len(py_files)})")
    print(f"Reduction: ~{len(py_files) - len(KEEP_SCRIPTS)} files ({(1 - len(KEEP_SCRIPTS)/len(py_files))*100:.0f}%)")


if __name__ == "__main__":
    import sys
    
    print("This will clean up deprecated test scripts.")
    print("They will be moved to a backup directory.\n")
    
    show_statistics()
    
    if '--dry-run' in sys.argv:
        cleanup_scripts(dry_run=True)
    else:
        response = input("\nProceed with cleanup? (y/n): ")
        if response.lower() == 'y':
            cleanup_scripts(dry_run=False)
            print("\nCleanup completed!")
        else:
            print("Cleanup cancelled.")
            
    print("\nRecommended next steps:")
    print("1. Test the unified tools to ensure everything works")
    print("2. Update any scripts or documentation that reference old files")
    print("3. Remove the backup directory once confirmed")