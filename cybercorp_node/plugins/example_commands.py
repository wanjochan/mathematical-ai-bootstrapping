"""Example plugin for CyberCorp server"""

import logging

logger = logging.getLogger('ExamplePlugin')

async def handle_echo(client, params):
    """Echo command handler"""
    message = params.get('message', 'Hello from server!')
    logger.info(f"Echo command from {client.id}: {message}")
    return {'echo': message, 'client': client.id}

async def handle_status(client, params):
    """Get server status"""
    return {
        'status': 'online',
        'client_count': len(client.server.clients),
        'uptime': str(datetime.now() - client.server.start_time)
    }

def register_commands(register_func):
    """Register plugin commands"""
    register_func('echo', handle_echo)
    register_func('status', handle_status)
    logger.info("Example plugin commands registered")
