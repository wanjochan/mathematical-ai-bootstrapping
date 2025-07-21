"""
Test log management functionality
"""

import asyncio
import json
import websockets
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestLogManager')

async def test_log_manager(host='localhost', port=9998):
    """Test log management commands"""
    url = f'ws://{host}:{port}'
    
    try:
        # Connect as admin
        ws = await websockets.connect(url)
        
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': 'admin',
            'client_start_time': '2024',
            'capabilities': {'management': True}
        }))
        
        response = await ws.recv()
        logger.info(f"Registration: {response}")
        
        # Get client list
        await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
        response = await ws.recv()
        data = json.loads(response)
        
        clients = data.get('clients', [])
        
        if not clients:
            logger.warning("No clients found")
            return
        
        # Test each client
        for client in clients:
            client_id = client['id']
            logger.info(f"\nTesting log manager on client: {client_id}")
            
            # Get log stats
            logger.info("\n1. Getting log statistics...")
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'get_log_stats'
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result = data.get('result', {})
                    if result.get('success'):
                        stats = result.get('stats', {})
                        logger.info(f"Log Statistics:")
                        logger.info(f"  Total entries: {stats.get('total_entries', 0)}")
                        logger.info(f"  Error entries: {stats.get('error_entries', 0)}")
                        
                        if 'level_counts' in stats:
                            logger.info("  Level counts:")
                            for level, count in stats['level_counts'].items():
                                logger.info(f"    {level}: {count}")
                        
                        if 'log_files' in stats:
                            logger.info("  Log files:")
                            for name, info in stats['log_files'].items():
                                logger.info(f"    {name}: {info['size']} bytes")
                    else:
                        logger.error(f"Log stats error: {result.get('error')}")
                        
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
                continue
            
            # Get recent logs
            logger.info("\n2. Getting recent logs...")
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'get_logs',
                    'params': {
                        'count': 10,
                        'level': 'INFO'
                    }
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result = data.get('result', {})
                    if result.get('success'):
                        logs = result.get('logs', [])
                        logger.info(f"Recent logs ({len(logs)} entries):")
                        for log in logs[-5:]:  # Show last 5
                            logger.info(f"  [{log.get('level_name')}] {log.get('message', '')[:80]}...")
                    else:
                        logger.error(f"Get logs error: {result.get('error')}")
                        
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
            
            # Search logs
            logger.info("\n3. Searching logs for 'command'...")
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'get_logs',
                    'params': {
                        'count': 5,
                        'search': 'command'
                    }
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result = data.get('result', {})
                    if result.get('success'):
                        logs = result.get('logs', [])
                        logger.info(f"Search results ({len(logs)} entries):")
                        for log in logs[:3]:  # Show first 3
                            logger.info(f"  [{log.get('level_name')}] {log.get('message', '')[:80]}...")
                    else:
                        logger.error(f"Search logs error: {result.get('error')}")
                        
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
            
            # Set log level
            logger.info("\n4. Setting log level to DEBUG...")
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'set_log_level',
                    'params': {
                        'level': 'DEBUG'
                    }
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result = data.get('result', {})
                    if result.get('success'):
                        logger.info(f"Log level set to {result.get('level')} for {result.get('logger')}")
                    else:
                        logger.error(f"Set log level error: {result.get('error')}")
                        
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Test error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test log management functionality')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    
    args = parser.parse_args()
    
    asyncio.run(test_log_manager(args.host, args.port))

if __name__ == '__main__':
    main()