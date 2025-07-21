"""
Performance testing for CyberCorp Node optimizations
"""

import asyncio
import json
import websockets
import logging
import argparse
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestPerformance')

class PerformanceMetrics:
    """Track performance metrics"""
    
    def __init__(self):
        self.command_times: Dict[str, List[float]] = {}
        self.response_sizes: Dict[str, List[int]] = {}
        self.error_counts: Dict[str, int] = {}
        self.total_commands = 0
        self.total_errors = 0
        self.start_time = None
        self.end_time = None
    
    def record_command(self, command: str, duration: float, response_size: int, success: bool):
        """Record command execution metrics"""
        if command not in self.command_times:
            self.command_times[command] = []
            self.response_sizes[command] = []
            self.error_counts[command] = 0
        
        self.command_times[command].append(duration)
        self.response_sizes[command].append(response_size)
        self.total_commands += 1
        
        if not success:
            self.error_counts[command] += 1
            self.total_errors += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        summary = {
            'total_commands': self.total_commands,
            'total_errors': self.total_errors,
            'success_rate': (self.total_commands - self.total_errors) / self.total_commands * 100 if self.total_commands > 0 else 0,
            'total_duration': (self.end_time - self.start_time) if self.end_time and self.start_time else 0,
            'commands': {}
        }
        
        for command in self.command_times:
            times = self.command_times[command]
            sizes = self.response_sizes[command]
            
            summary['commands'][command] = {
                'count': len(times),
                'errors': self.error_counts[command],
                'avg_time': statistics.mean(times),
                'min_time': min(times),
                'max_time': max(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                'avg_size': statistics.mean(sizes),
                'success_rate': (len(times) - self.error_counts[command]) / len(times) * 100
            }
        
        return summary

async def test_command_performance(ws, client_id: str, command: str, params: dict = None) -> tuple:
    """Test a single command and measure performance"""
    params = params or {}
    
    # Start timing
    start_time = time.time()
    
    # Send command
    await ws.send(json.dumps({
        'type': 'forward_command',
        'target_client': client_id,
        'command': {
            'type': 'command',
            'command': command,
            'params': params
        }
    }))
    
    # Get acknowledgment
    await ws.recv()
    
    try:
        # Get result with timeout
        result = await asyncio.wait_for(ws.recv(), timeout=30.0)
        end_time = time.time()
        
        data = json.loads(result)
        response_size = len(result)
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            success = result_data.get('success', False)
            
            return end_time - start_time, response_size, success
        else:
            return end_time - start_time, response_size, False
            
    except asyncio.TimeoutError:
        end_time = time.time()
        return end_time - start_time, 0, False

async def stress_test_concurrent(ws, client_id: str, command: str, params: dict, concurrent: int, iterations: int) -> List[tuple]:
    """Run concurrent stress test"""
    results = []
    
    for i in range(iterations):
        # Launch concurrent requests
        tasks = []
        for j in range(concurrent):
            task = test_command_performance(ws, client_id, command, params)
            tasks.append(task)
        
        # Wait for all to complete
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in batch_results:
            if isinstance(result, Exception):
                results.append((0, 0, False))
            else:
                results.append(result)
        
        # Small delay between batches
        await asyncio.sleep(0.1)
    
    return results

async def test_performance(host='localhost', port=9998):
    """Test performance of various optimizations"""
    url = f'ws://{host}:{port}'
    metrics = PerformanceMetrics()
    
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
        
        client_id = clients[0]['id']
        logger.info(f"Testing performance on client: {client_id}")
        
        metrics.start_time = time.time()
        
        # Test 1: Basic command performance
        logger.info("\n=== Test 1: Basic Command Performance ===")
        
        basic_commands = [
            ('get_system_info', {}),
            ('get_windows', {}),
            ('get_processes', {}),
            ('health_status', {}),
            ('get_log_stats', {}),
            ('hot_reload', {'action': 'status'}),
        ]
        
        for command, params in basic_commands:
            logger.info(f"\nTesting {command}...")
            
            # Warm up
            await test_command_performance(ws, client_id, command, params)
            
            # Test multiple times
            for i in range(5):
                duration, size, success = await test_command_performance(ws, client_id, command, params)
                metrics.record_command(command, duration, size, success)
                logger.info(f"  Run {i+1}: {duration:.3f}s, {size} bytes, {'✓' if success else '✗'}")
                await asyncio.sleep(0.1)
        
        # Test 2: Screenshot performance
        logger.info("\n=== Test 2: Screenshot Performance ===")
        
        for i in range(3):
            duration, size, success = await test_command_performance(ws, client_id, 'take_screenshot', {})
            metrics.record_command('take_screenshot', duration, size, success)
            logger.info(f"  Screenshot {i+1}: {duration:.3f}s, {size} bytes, {'✓' if success else '✗'}")
            await asyncio.sleep(0.5)
        
        # Test 3: Window activation performance
        logger.info("\n=== Test 3: Window Activation Performance ===")
        
        for i in range(3):
            duration, size, success = await test_command_performance(ws, client_id, 'activate_window', {})
            metrics.record_command('activate_window', duration, size, success)
            logger.info(f"  Activation {i+1}: {duration:.3f}s, {'✓' if success else '✗'}")
            await asyncio.sleep(1.0)
        
        # Test 4: Concurrent command handling
        logger.info("\n=== Test 4: Concurrent Command Handling ===")
        
        concurrent_tests = [
            ('get_system_info', {}, 5, 3),  # 5 concurrent, 3 iterations
            ('health_status', {}, 10, 2),    # 10 concurrent, 2 iterations
        ]
        
        for command, params, concurrent, iterations in concurrent_tests:
            logger.info(f"\nStress testing {command} ({concurrent} concurrent x {iterations} iterations)...")
            
            results = await stress_test_concurrent(ws, client_id, command, params, concurrent, iterations)
            
            for duration, size, success in results:
                metrics.record_command(f"{command}_concurrent", duration, size, success)
            
            successful = sum(1 for _, _, s in results if s)
            logger.info(f"  Completed: {successful}/{len(results)} successful")
        
        # Test 5: Hot reload performance
        logger.info("\n=== Test 5: Hot Reload Performance ===")
        
        # Test config reload
        duration, size, success = await test_command_performance(
            ws, client_id, 'hot_reload', {'action': 'reload_config'}
        )
        metrics.record_command('hot_reload_config', duration, size, success)
        logger.info(f"  Config reload: {duration:.3f}s, {'✓' if success else '✗'}")
        
        # Test 6: Log retrieval performance
        logger.info("\n=== Test 6: Log Retrieval Performance ===")
        
        log_tests = [
            {'count': 10},
            {'count': 100},
            {'count': 500},
        ]
        
        for params in log_tests:
            duration, size, success = await test_command_performance(ws, client_id, 'get_logs', params)
            metrics.record_command(f"get_logs_{params['count']}", duration, size, success)
            logger.info(f"  Get {params['count']} logs: {duration:.3f}s, {size} bytes, {'✓' if success else '✗'}")
            await asyncio.sleep(0.2)
        
        # Test 7: Command timeout handling
        logger.info("\n=== Test 7: Command Timeout Handling ===")
        
        # This should timeout (unknown command)
        start = time.time()
        duration, size, success = await test_command_performance(ws, client_id, 'unknown_command', {})
        metrics.record_command('timeout_test', duration, size, success)
        logger.info(f"  Timeout handling: {duration:.3f}s, {'✓ handled' if not success else '✗ unexpected success'}")
        
        metrics.end_time = time.time()
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("PERFORMANCE SUMMARY")
        logger.info("="*60)
        
        summary = metrics.get_summary()
        
        logger.info(f"\nOverall Statistics:")
        logger.info(f"  Total commands: {summary['total_commands']}")
        logger.info(f"  Total errors: {summary['total_errors']}")
        logger.info(f"  Success rate: {summary['success_rate']:.1f}%")
        logger.info(f"  Total duration: {summary['total_duration']:.1f}s")
        logger.info(f"  Commands/sec: {summary['total_commands'] / summary['total_duration']:.1f}")
        
        logger.info(f"\nCommand Performance:")
        for command, stats in summary['commands'].items():
            logger.info(f"\n  {command}:")
            logger.info(f"    Count: {stats['count']}")
            logger.info(f"    Avg time: {stats['avg_time']:.3f}s")
            logger.info(f"    Min/Max: {stats['min_time']:.3f}s / {stats['max_time']:.3f}s")
            logger.info(f"    Std dev: {stats['std_dev']:.3f}s")
            logger.info(f"    Avg size: {stats['avg_size']:.0f} bytes")
            logger.info(f"    Success: {stats['success_rate']:.1f}%")
        
        # Performance insights
        logger.info("\n" + "="*60)
        logger.info("PERFORMANCE INSIGHTS")
        logger.info("="*60)
        
        # Find fastest and slowest commands
        avg_times = [(cmd, stats['avg_time']) for cmd, stats in summary['commands'].items()]
        avg_times.sort(key=lambda x: x[1])
        
        logger.info("\nFastest commands:")
        for cmd, time in avg_times[:3]:
            logger.info(f"  {cmd}: {time:.3f}s")
        
        logger.info("\nSlowest commands:")
        for cmd, time in avg_times[-3:]:
            logger.info(f"  {cmd}: {time:.3f}s")
        
        # Check for performance improvements
        logger.info("\nOptimization Impact:")
        
        # Compare concurrent vs sequential
        seq_cmds = [c for c in summary['commands'] if not c.endswith('_concurrent')]
        con_cmds = [c for c in summary['commands'] if c.endswith('_concurrent')]
        
        if seq_cmds and con_cmds:
            seq_avg = statistics.mean([summary['commands'][c]['avg_time'] for c in seq_cmds])
            con_avg = statistics.mean([summary['commands'][c]['avg_time'] for c in con_cmds])
            logger.info(f"  Sequential avg: {seq_avg:.3f}s")
            logger.info(f"  Concurrent avg: {con_avg:.3f}s")
            logger.info(f"  Concurrent handling: {'✓ Good' if con_avg < seq_avg * 2 else '✗ Needs improvement'}")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Test CyberCorp Node performance')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    
    args = parser.parse_args()
    
    logger.info("CyberCorp Node Performance Testing")
    logger.info("==================================")
    logger.info("This will test various performance aspects of the optimized system.")
    logger.info("Make sure the server and client are running.\n")
    
    asyncio.run(test_performance(args.host, args.port))

if __name__ == '__main__':
    main()