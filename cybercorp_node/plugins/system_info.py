"""Plugin for system information commands - Hot Reload Test"""

import platform
import psutil
import os
from datetime import datetime
from server_hotreload import register_command

def handle_system_info(client, params):
    """Get system information"""
    try:
        return {
            'success': True,
            'system_info': {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'hostname': platform.node(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'total': psutil.virtual_memory().total // (1024**3),  # GB
                    'available': psutil.virtual_memory().available // (1024**3),
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage('/').total // (1024**3),
                    'free': psutil.disk_usage('/').free // (1024**3),
                    'percent': psutil.disk_usage('/').percent
                },
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                'current_time': datetime.now().isoformat(),
                'user': os.environ.get('USERNAME', 'unknown')
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Register the command
register_command('system_info', handle_system_info)
print("System info plugin loaded!")