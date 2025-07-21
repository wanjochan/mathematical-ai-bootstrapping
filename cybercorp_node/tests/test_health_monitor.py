"""
Test health monitoring functionality
"""

import asyncio
import json
import websockets
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestHealthMonitor')

async def test_health_monitor(host='localhost', port=9998):
    """Test health monitoring commands"""
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
            logger.info(f"\nTesting health monitor on client: {client_id}")
            
            # Get health status
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'health_status'
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result = data.get('result', {})
                    if result.get('success'):
                        health = result.get('health', {})
                        metrics = result.get('metrics', {})
                        
                        logger.info(f"Health Status: {health.get('overall', 'unknown')}")
                        logger.info(f"  CPU: {health.get('cpu', 'unknown')}")
                        logger.info(f"  Memory: {health.get('memory', 'unknown')}")
                        logger.info(f"  Network: {health.get('network', 'unknown')}")
                        logger.info(f"  Commands: {health.get('commands', 'unknown')}")
                        
                        if 'system_metrics' in metrics:
                            sys_metrics = metrics['system_metrics']
                            logger.info(f"\nSystem Metrics:")
                            if 'cpu_percent_avg' in sys_metrics:
                                logger.info(f"  CPU Average: {sys_metrics['cpu_percent_avg']:.1f}%")
                            if 'memory_percent_avg' in sys_metrics:
                                logger.info(f"  Memory Average: {sys_metrics['memory_percent_avg']:.1f}%")
                            if 'heartbeat_latency_avg' in sys_metrics:
                                logger.info(f"  Heartbeat Latency: {sys_metrics['heartbeat_latency_avg']*1000:.1f}ms")
                            if 'command_response_avg' in sys_metrics:
                                logger.info(f"  Command Response Avg: {sys_metrics['command_response_avg']:.3f}s")
                        
                        if 'command_stats' in metrics:
                            cmd_stats = metrics['command_stats']
                            logger.info(f"\nCommand Stats:")
                            logger.info(f"  Total: {cmd_stats.get('total', 0)}")
                            logger.info(f"  Success: {cmd_stats.get('success', 0)}")
                            logger.info(f"  Failed: {cmd_stats.get('failed', 0)}")
                            logger.info(f"  Timeout: {cmd_stats.get('timeout', 0)}")
                            
                            if cmd_stats.get('total', 0) > 0:
                                success_rate = cmd_stats.get('success', 0) / cmd_stats.get('total', 1) * 100
                                logger.info(f"  Success Rate: {success_rate:.1f}%")
                    else:
                        logger.error(f"Health status error: {result.get('error')}")
                        
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Test error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test health monitoring functionality')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    
    args = parser.parse_args()
    
    asyncio.run(test_health_monitor(args.host, args.port))

if __name__ == '__main__':
    main()