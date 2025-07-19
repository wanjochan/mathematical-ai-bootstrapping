"""Plugin for process information commands"""

import psutil
import os
from server_hotreload import register_command

def handle_get_processes(client, params):
    """Get process information for the client's session"""
    try:
        processes = []
        current_user = params.get('user', os.environ.get('USERNAME'))
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info']):
            try:
                pinfo = proc.info
                if pinfo['username'] and current_user in pinfo['username']:
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'memory_mb': pinfo['memory_info'].rss / 1024 / 1024 if pinfo['memory_info'] else 0
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by memory usage
        processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        
        return {
            'success': True,
            'processes': processes[:20],  # Top 20 processes
            'total_count': len(processes)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Register the command
register_command('get_processes', handle_get_processes)