"""Performance test for optimized CyberCorp system"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import json
from utils.remote_control import RemoteController
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceTester:
    """Test performance improvements"""
    
    def __init__(self):
        self.results = {
            'window_lookup': [],
            'command_execution': [],
            'screenshot': [],
            'uia_structure': [],
            'batch_commands': []
        }
        
    async def test_window_lookup_speed(self, controller: RemoteController, iterations: int = 10):
        """Test window lookup performance"""
        logger.info(f"Testing window lookup speed ({iterations} iterations)...")
        
        # First lookup (cold cache)
        start = time.time()
        window = await controller.find_window("Cursor", use_cache=False)
        cold_time = time.time() - start
        logger.info(f"Cold lookup: {cold_time:.3f}s")
        
        # Subsequent lookups (warm cache)
        for i in range(iterations):
            start = time.time()
            window = await controller.find_window("Cursor", use_cache=True)
            duration = time.time() - start
            self.results['window_lookup'].append(duration)
            
        avg_warm = statistics.mean(self.results['window_lookup'])
        logger.info(f"Warm lookup average: {avg_warm:.3f}s")
        logger.info(f"Speed improvement: {cold_time/avg_warm:.1f}x")
        
    async def test_command_execution(self, controller: RemoteController, iterations: int = 5):
        """Test command execution speed"""
        logger.info(f"Testing command execution speed ({iterations} iterations)...")
        
        for i in range(iterations):
            start = time.time()
            windows = await controller.get_windows()
            duration = time.time() - start
            self.results['command_execution'].append(duration)
            
        avg_time = statistics.mean(self.results['command_execution'])
        logger.info(f"Average command execution: {avg_time:.3f}s")
        
    async def test_screenshot_performance(self, controller: RemoteController, hwnd: int):
        """Test screenshot performance"""
        logger.info("Testing screenshot performance...")
        
        # Full screen
        start = time.time()
        path = await controller.screenshot()
        full_screen_time = time.time() - start
        logger.info(f"Full screen screenshot: {full_screen_time:.3f}s")
        
        # Window screenshot
        start = time.time()
        path = await controller.screenshot(hwnd=hwnd)
        window_time = time.time() - start
        logger.info(f"Window screenshot: {window_time:.3f}s")
        
        self.results['screenshot'] = [full_screen_time, window_time]
        
    async def test_batch_execution(self, controller: RemoteController):
        """Test batch command execution"""
        logger.info("Testing batch command execution...")
        
        # Sequential execution
        start = time.time()
        for i in range(5):
            await controller.click(100 + i*10, 100)
            await asyncio.sleep(0.1)
        sequential_time = time.time() - start
        
        # Batch execution
        from utils.remote_control import BatchExecutor
        batch = BatchExecutor(controller)
        
        for i in range(5):
            batch.add_click(100 + i*10, 100)
            batch.add_wait(0.1)
            
        start = time.time()
        await batch.execute()
        batch_time = time.time() - start
        
        logger.info(f"Sequential: {sequential_time:.3f}s")
        logger.info(f"Batch: {batch_time:.3f}s")
        logger.info(f"Speed improvement: {sequential_time/batch_time:.1f}x")
        
        self.results['batch_commands'] = [sequential_time, batch_time]
        
    async def test_uia_performance(self, controller: RemoteController, hwnd: int):
        """Test UIA structure retrieval performance"""
        logger.info("Testing UIA structure retrieval...")
        
        start = time.time()
        structure = await controller.get_uia_structure(hwnd)
        duration = time.time() - start
        
        logger.info(f"UIA structure retrieval: {duration:.3f}s")
        self.results['uia_structure'].append(duration)
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        report = {}
        
        for test_name, times in self.results.items():
            if times:
                report[test_name] = {
                    'count': len(times),
                    'min': min(times),
                    'max': max(times),
                    'avg': statistics.mean(times),
                    'stdev': statistics.stdev(times) if len(times) > 1 else 0
                }
                
        return report
        
    def print_report(self):
        """Print performance report"""
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("PERFORMANCE TEST REPORT")
        print("="*60)
        
        for test_name, stats in report.items():
            print(f"\n{test_name.upper()}:")
            print(f"  Samples: {stats['count']}")
            print(f"  Average: {stats['avg']:.3f}s")
            print(f"  Min: {stats['min']:.3f}s")
            print(f"  Max: {stats['max']:.3f}s")
            if stats['stdev'] > 0:
                print(f"  StdDev: {stats['stdev']:.3f}s")
                
        print("\n" + "="*60)


async def run_performance_tests():
    """Run all performance tests"""
    tester = PerformanceTester()
    controller = RemoteController()
    
    try:
        # Connect
        await controller.connect("perf_test")
        
        # Find test client
        await controller.find_client("wjchk")
        
        # Find test window
        window = await controller.find_window("Cursor")
        if not window:
            logger.error("Test window not found")
            return
            
        hwnd = window['hwnd']
        logger.info(f"Using test window: {window['title']} (hwnd: {hwnd})")
        
        # Run tests
        await tester.test_window_lookup_speed(controller)
        await asyncio.sleep(1)
        
        await tester.test_command_execution(controller)
        await asyncio.sleep(1)
        
        await tester.test_screenshot_performance(controller, hwnd)
        await asyncio.sleep(1)
        
        await tester.test_batch_execution(controller)
        await asyncio.sleep(1)
        
        await tester.test_uia_performance(controller, hwnd)
        
        # Generate report
        tester.print_report()
        
        # Save report
        with open('performance_report.json', 'w') as f:
            json.dump(tester.generate_report(), f, indent=2)
            logger.info("Report saved to performance_report.json")
            
    finally:
        await controller.close()


if __name__ == "__main__":
    asyncio.run(run_performance_tests())