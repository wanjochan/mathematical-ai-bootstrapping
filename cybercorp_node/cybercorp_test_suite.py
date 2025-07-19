"""
CyberCorp Node Unified Test Suite
整合所有测试功能到一个命令行工具
"""

import argparse
import asyncio
import json
import sys
import os
import time
from typing import Dict, Any, List, Optional, Callable
import logging
from datetime import datetime
import concurrent.futures
from functools import partial

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    CyberCorpClient,
    ClientManager,
    CommandForwarder,
    DataPersistence,
    VSCodeUIAnalyzer,
    VSCodeAutomation,
    ResponseHandler,
    Win32Backend,
    OCRBackend
)

# Configure logging with more details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'test_suite_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger('TestSuite')


class TestContext:
    """Test execution context"""
    def __init__(self):
        self.client: Optional[CyberCorpClient] = None
        self.client_manager: Optional[ClientManager] = None
        self.forwarder: Optional[CommandForwarder] = None
        self.persistence = DataPersistence()
        self.target_client_id: Optional[str] = None
        self.target_username: Optional[str] = None
        
    async def setup(self, port: int = 9998, target_username: Optional[str] = None):
        """Setup test context"""
        self.client = CyberCorpClient(client_type="test_suite", port=port)
        await self.client.connect()
        self.client_manager = ClientManager(self.client)
        self.forwarder = CommandForwarder(self.client)
        
        if target_username:
            self.target_username = target_username
            target_client = await self.client_manager.find_client_by_username(target_username)
            if target_client:
                self.target_client_id = target_client['id']
                logger.info(f"Target client found: {self.target_client_id} ({target_username})")
            else:
                logger.warning(f"Target client '{target_username}' not found")
                
    async def teardown(self):
        """Teardown test context"""
        if self.client:
            await self.client.disconnect()


class TestSuite:
    """Main test suite class"""
    
    def __init__(self):
        self.tests = {}
        self._register_tests()
        
    def _register_tests(self):
        """Register all available tests"""
        # System tests
        self.tests['status'] = self.test_status
        self.tests['list'] = self.test_list_clients
        self.tests['info'] = self.test_system_info
        
        # Control tests
        self.tests['control'] = self.test_control
        self.tests['windows'] = self.test_windows
        self.tests['processes'] = self.test_processes
        
        # VSCode tests
        self.tests['vscode'] = self.test_vscode
        self.tests['roo'] = self.test_roo_code
        
        # Advanced feature tests
        self.tests['drag'] = self.test_mouse_drag
        self.tests['ocr'] = self.test_ocr
        self.tests['win32'] = self.test_win32
        self.tests['vision'] = self.test_vision_model
        
        # Stress tests
        self.tests['stress'] = self.test_stress
        self.tests['parallel'] = self.test_parallel
        
    async def test_status(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test server status"""
        logger.info("Testing server status...")
        
        clients = await ctx.client_manager.list_clients()
        client_count = len(clients)
        
        result = {
            'server_running': True,
            'client_count': client_count,
            'clients': []
        }
        
        if args.verbose:
            for client in clients:
                client_info = {
                    'id': client['id'],
                    'user_session': client['user_session'],
                    'capabilities': client.get('capabilities', {}),
                    'connected_at': client.get('connected_at', 'unknown')
                }
                result['clients'].append(client_info)
                logger.info(f"Client: {client_info['user_session']} (ID: {client_info['id']})")
                
        return result
        
    async def test_list_clients(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test listing clients"""
        logger.info("Listing connected clients...")
        
        clients = await ctx.client_manager.list_clients()
        
        result = {
            'client_count': len(clients),
            'clients': clients
        }
        
        # Group by capabilities
        if args.group_by == 'capability':
            grouped = {}
            for client in clients:
                caps = client.get('capabilities', {})
                for cap, enabled in caps.items():
                    if enabled:
                        if cap not in grouped:
                            grouped[cap] = []
                        grouped[cap].append(client['user_session'])
            result['grouped'] = grouped
            
        logger.info(f"Found {len(clients)} clients")
        return result
        
    async def test_system_info(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test getting system info"""
        if not ctx.target_client_id:
            return {'error': 'No target client specified'}
            
        logger.info(f"Getting system info from {ctx.target_username}...")
        
        result = await ctx.forwarder.forward_command(
            ctx.target_client_id, 'get_system_info', timeout=args.timeout
        )
        
        # Log sample of result
        if isinstance(result, dict):
            logger.info(f"System info keys: {list(result.keys())[:5]}...")
            
        return result
        
    async def test_control(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test basic control commands"""
        if not ctx.target_client_id:
            return {'error': 'No target client specified'}
            
        logger.info(f"Testing control commands on {ctx.target_username}...")
        
        results = {}
        
        # Test commands based on args
        if args.command:
            # Single command test
            logger.info(f"Executing command: {args.command}")
            if args.params:
                try:
                    params = json.loads(args.params)
                    logger.info(f"With parameters: {json.dumps(params, ensure_ascii=False)[:200]}")
                except:
                    params = None
            else:
                params = None
                
            result = await ctx.forwarder.forward_command(
                ctx.target_client_id, args.command, params, timeout=args.timeout
            )
            
            # Log result sample
            result_str = str(result)
            if len(result_str) > 500:
                logger.info(f"Result (truncated): {result_str[:500]}...")
            else:
                logger.info(f"Result: {result_str}")
                
            results[args.command] = result
        else:
            # Test suite of commands
            test_commands = [
                ('get_screen_size', None),
                ('get_windows', None),
                ('get_processes', None)
            ]
            
            for cmd, params in test_commands:
                logger.info(f"Testing command: {cmd}")
                try:
                    result = await ctx.forwarder.forward_command(
                        ctx.target_client_id, cmd, params, timeout=5.0
                    )
                    results[cmd] = {'success': True, 'data': result}
                except Exception as e:
                    results[cmd] = {'success': False, 'error': str(e)}
                    logger.error(f"Command {cmd} failed: {e}")
                    
        return results
        
    async def test_mouse_drag(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test mouse drag functionality"""
        if not ctx.target_client_id:
            return {'error': 'No target client specified'}
            
        logger.info(f"Testing mouse drag on {ctx.target_username}...")
        
        # Parse drag parameters
        params = {
            'start_x': args.start_x or 100,
            'start_y': args.start_y or 200,
            'end_x': args.end_x or 500,
            'end_y': args.end_y or 200,
            'duration': args.duration or 2.0,
            'humanize': args.humanize,
            'button': args.button or 'left'
        }
        
        logger.info(f"Drag parameters: {params}")
        
        result = await ctx.forwarder.forward_command(
            ctx.target_client_id, 'mouse_drag', params, timeout=10.0
        )
        
        logger.info(f"Drag result: {result}")
        return {'drag_params': params, 'result': result}
        
    async def test_ocr(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test OCR functionality"""
        if not ctx.target_client_id:
            return {'error': 'No target client specified'}
            
        logger.info(f"Testing OCR on {ctx.target_username}...")
        
        results = {}
        
        # Test screen OCR
        if args.screen:
            params = {
                'x': args.x or 0,
                'y': args.y or 0,
                'width': args.width or 800,
                'height': args.height or 600,
                'engine': args.engine
            }
            
            logger.info(f"Screen OCR parameters: {params}")
            
            result = await ctx.forwarder.forward_command(
                ctx.target_client_id, 'ocr_screen', params, timeout=30.0
            )
            
            if result.get('success'):
                detections = result.get('detections', [])
                logger.info(f"OCR found {len(detections)} text regions")
                
                # Log first few detections
                for i, det in enumerate(detections[:3]):
                    logger.info(f"  [{i+1}] '{det.get('text', '')}' (conf: {det.get('confidence', 'N/A')})")
                    
            results['screen_ocr'] = result
            
        # Test window OCR
        if args.window:
            # First find window
            window_result = await ctx.forwarder.forward_command(
                ctx.target_client_id, 'win32_find_window', 
                {'window_name': args.window}, timeout=5.0
            )
            
            if window_result.get('success'):
                hwnd = window_result.get('hwnd')
                logger.info(f"Found window: {window_result.get('info', {}).get('title')}")
                
                # Perform OCR
                ocr_result = await ctx.forwarder.forward_command(
                    ctx.target_client_id, 'ocr_window',
                    {'hwnd': hwnd, 'engine': args.engine}, timeout=30.0
                )
                
                results['window_ocr'] = ocr_result
            else:
                results['window_ocr'] = {'error': 'Window not found'}
                
        return results
        
    async def test_parallel(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test parallel command execution"""
        if not ctx.target_client_id:
            return {'error': 'No target client specified'}
            
        logger.info(f"Testing parallel execution on {ctx.target_username}...")
        
        # Define parallel tasks
        tasks = []
        commands = [
            ('get_windows', None),
            ('get_processes', None),
            ('get_system_info', None),
            ('get_screen_size', None)
        ]
        
        # Create tasks
        for cmd, params in commands:
            task = ctx.forwarder.forward_command(
                ctx.target_client_id, cmd, params, timeout=10.0
            )
            tasks.append((cmd, task))
            
        # Execute in parallel
        start_time = time.time()
        results = {}
        
        for cmd, task in tasks:
            try:
                result = await task
                results[cmd] = {'success': True, 'data': result}
                logger.info(f"Parallel task '{cmd}' completed")
            except Exception as e:
                results[cmd] = {'success': False, 'error': str(e)}
                logger.error(f"Parallel task '{cmd}' failed: {e}")
                
        elapsed = time.time() - start_time
        logger.info(f"Parallel execution completed in {elapsed:.2f}s")
        
        return {
            'execution_time': elapsed,
            'results': results
        }
        
    async def test_stress(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Stress test with multiple rapid commands"""
        if not ctx.target_client_id:
            return {'error': 'No target client specified'}
            
        logger.info(f"Running stress test on {ctx.target_username}...")
        
        iterations = args.iterations or 10
        command = args.command or 'get_screen_size'
        
        results = {
            'iterations': iterations,
            'command': command,
            'successes': 0,
            'failures': 0,
            'times': []
        }
        
        for i in range(iterations):
            start = time.time()
            try:
                await ctx.forwarder.forward_command(
                    ctx.target_client_id, command, timeout=5.0
                )
                results['successes'] += 1
            except Exception as e:
                results['failures'] += 1
                logger.error(f"Iteration {i+1} failed: {e}")
            
            elapsed = time.time() - start
            results['times'].append(elapsed)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Completed {i+1}/{iterations} iterations")
                
        # Calculate statistics
        if results['times']:
            results['avg_time'] = sum(results['times']) / len(results['times'])
            results['min_time'] = min(results['times'])
            results['max_time'] = max(results['times'])
            
        logger.info(f"Stress test completed: {results['successes']} successes, {results['failures']} failures")
        
        return results
        
    async def test_vscode(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test VSCode specific functionality"""
        if not ctx.target_client_id:
            return {'error': 'No target client specified'}
            
        logger.info(f"Testing VSCode on {ctx.target_username}...")
        
        automation = VSCodeAutomation(ctx.forwarder)
        
        # Get VSCode content
        content = await automation.get_content(ctx.target_client_id)
        
        # Analyze structure
        analyzer = VSCodeUIAnalyzer()
        summary = analyzer.get_ui_summary(content)
        
        logger.info(f"VSCode window: {summary['window_title']}")
        logger.info(f"Total elements: {summary['total_elements']}")
        logger.info(f"Has Roo Code: {summary['has_roo_code']}")
        
        return {
            'summary': summary,
            'content': content if args.full else None
        }
        
    async def test_roo_code(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test Roo Code interaction"""
        if not ctx.target_client_id:
            return {'error': 'No target client specified'}
            
        logger.info(f"Testing Roo Code on {ctx.target_username}...")
        
        automation = VSCodeAutomation(ctx.forwarder)
        
        # Get Roo Code state
        state = await automation.get_roo_code_state(ctx.target_client_id)
        
        logger.info(f"Roo Code active: {state['has_roo_code']}")
        
        if args.message and state['has_roo_code']:
            # Send message to Roo Code
            logger.info(f"Sending message: {args.message}")
            result = await automation.send_to_roo_code(
                ctx.target_client_id, args.message, use_background=True
            )
            state['send_result'] = result
            
        return state
        
    async def test_win32(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test Win32 API functionality"""
        if not ctx.target_client_id:
            return {'error': 'No target client specified'}
            
        logger.info(f"Testing Win32 API on {ctx.target_username}...")
        
        results = {}
        
        # Find window test
        if args.find_window:
            logger.info(f"Finding window: {args.find_window}")
            result = await ctx.forwarder.forward_command(
                ctx.target_client_id, 'win32_find_window',
                {'window_name': args.find_window}, timeout=5.0
            )
            results['find_window'] = result
            
        # Send keys test
        if args.send_keys:
            logger.info(f"Sending keys: {args.send_keys}")
            result = await ctx.forwarder.forward_command(
                ctx.target_client_id, 'win32_send_keys',
                {'keys': args.send_keys, 'delay': 0.05}, timeout=5.0
            )
            results['send_keys'] = result
            
        return results
        
    async def test_vision_model(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test vision model (local only)"""
        logger.info("Testing vision model locally...")
        
        from utils.vision_model import UIVisionModel
        import cv2
        import numpy as np
        
        # Create test image
        test_image = np.ones((600, 800, 3), dtype=np.uint8) * 255
        
        # Add some UI elements
        cv2.rectangle(test_image, (50, 50), (200, 100), (200, 200, 200), -1)
        cv2.putText(test_image, "Button", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        # Test vision model
        model = UIVisionModel(use_yolo=False)
        
        # Benchmark
        metrics = model.benchmark(test_image, iterations=args.iterations or 10)
        
        logger.info(f"Vision model FPS: {metrics['fps']:.1f}")
        logger.info(f"Average time: {metrics['avg_time']:.3f}s")
        
        return metrics
        
    async def test_windows(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test window operations"""
        if not ctx.target_client_id:
            return {'error': 'No target client specified'}
            
        logger.info(f"Getting windows from {ctx.target_username}...")
        
        result = await ctx.forwarder.forward_command(
            ctx.target_client_id, 'get_windows', timeout=args.timeout
        )
        
        if isinstance(result, list):
            logger.info(f"Found {len(result)} windows")
            
            # Log first few windows
            for i, window in enumerate(result[:5]):
                logger.info(f"  [{i+1}] {window.get('title', 'Untitled')}")
                
        return {'windows': result, 'count': len(result) if isinstance(result, list) else 0}
        
    async def test_processes(self, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Test process listing"""
        if not ctx.target_client_id:
            return {'error': 'No target client specified'}
            
        logger.info(f"Getting processes from {ctx.target_username}...")
        
        result = await ctx.forwarder.forward_command(
            ctx.target_client_id, 'get_processes', timeout=args.timeout
        )
        
        if isinstance(result, list):
            logger.info(f"Found {len(result)} processes")
            
            # Find interesting processes
            interesting = ['python', 'node', 'code', 'chrome', 'firefox']
            for proc in result:
                name = proc.get('name', '').lower()
                if any(x in name for x in interesting):
                    logger.info(f"  Process: {proc.get('name')} (PID: {proc.get('pid')})")
                    
        return {'processes': result[:50] if args.limit else result}  # Limit output
        
    async def run_test(self, test_name: str, ctx: TestContext, args: argparse.Namespace) -> Dict[str, Any]:
        """Run a single test"""
        if test_name not in self.tests:
            return {'error': f'Unknown test: {test_name}'}
            
        test_func = self.tests[test_name]
        
        try:
            start_time = time.time()
            result = await test_func(ctx, args)
            elapsed = time.time() - start_time
            
            return {
                'test': test_name,
                'success': True,
                'elapsed': elapsed,
                'result': result
            }
        except Exception as e:
            logger.error(f"Test '{test_name}' failed: {e}")
            return {
                'test': test_name,
                'success': False,
                'error': str(e)
            }
            
    async def run_multiple_tests(self, test_names: List[str], ctx: TestContext, 
                               args: argparse.Namespace, parallel: bool = False) -> Dict[str, Any]:
        """Run multiple tests"""
        results = {}
        
        if parallel:
            # Run tests in parallel
            tasks = []
            for test_name in test_names:
                task = self.run_test(test_name, ctx, args)
                tasks.append((test_name, task))
                
            for test_name, task in tasks:
                results[test_name] = await task
        else:
            # Run tests sequentially
            for test_name in test_names:
                results[test_name] = await self.run_test(test_name, ctx, args)
                
        return results


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description='CyberCorp Node Unified Test Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global arguments
    parser.add_argument('-p', '--port', type=int, default=9998,
                       help='Server port (default: 9998)')
    parser.add_argument('-t', '--target', help='Target client username')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('--timeout', type=float, default=10.0,
                       help='Command timeout in seconds')
    parser.add_argument('--save', action='store_true',
                       help='Save test results to file')
    parser.add_argument('--parallel', action='store_true',
                       help='Run tests in parallel')
    
    # Test selection
    parser.add_argument('tests', nargs='*', 
                       help='Tests to run (leave empty to list available tests)')
    
    # Test-specific arguments
    test_group = parser.add_argument_group('test-specific arguments')
    
    # Control test arguments
    test_group.add_argument('-c', '--command', help='Command to execute')
    test_group.add_argument('--params', help='Command parameters (JSON)')
    
    # OCR test arguments
    test_group.add_argument('--screen', action='store_true', help='Test screen OCR')
    test_group.add_argument('--window', help='Window name for OCR')
    test_group.add_argument('--engine', help='OCR engine to use')
    test_group.add_argument('-x', type=int, help='OCR region X')
    test_group.add_argument('-y', type=int, help='OCR region Y')
    test_group.add_argument('--width', type=int, help='OCR region width')
    test_group.add_argument('--height', type=int, help='OCR region height')
    
    # Mouse drag arguments
    test_group.add_argument('--start-x', type=int, help='Drag start X')
    test_group.add_argument('--start-y', type=int, help='Drag start Y')
    test_group.add_argument('--end-x', type=int, help='Drag end X')
    test_group.add_argument('--end-y', type=int, help='Drag end Y')
    test_group.add_argument('--duration', type=float, help='Drag duration')
    test_group.add_argument('--humanize', action='store_true', help='Humanize drag')
    test_group.add_argument('--button', choices=['left', 'right'], help='Mouse button')
    
    # Win32 arguments
    test_group.add_argument('--find-window', help='Window name to find')
    test_group.add_argument('--send-keys', help='Keys to send')
    
    # Other arguments
    test_group.add_argument('--iterations', type=int, help='Number of iterations for stress test')
    test_group.add_argument('--message', help='Message for Roo Code')
    test_group.add_argument('--full', action='store_true', help='Include full data in results')
    test_group.add_argument('--limit', action='store_true', help='Limit output size')
    test_group.add_argument('--group-by', choices=['capability'], help='Group results by')
    
    return parser


async def main():
    """Main function"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create test suite
    suite = TestSuite()
    
    # List available tests if none specified
    if not args.tests:
        print("CyberCorp Node Test Suite")
        print("=" * 60)
        print("\nAvailable tests:")
        for test_name in sorted(suite.tests.keys()):
            print(f"  {test_name}")
        print("\nUsage: python cybercorp_test_suite.py [tests...] [options]")
        print("Example: python cybercorp_test_suite.py status list -t wjchk")
        return
        
    # Setup test context
    ctx = TestContext()
    
    try:
        await ctx.setup(port=args.port, target_username=args.target)
        
        # Run tests
        start_time = time.time()
        
        if len(args.tests) == 1:
            # Single test
            result = await suite.run_test(args.tests[0], ctx, args)
            results = {args.tests[0]: result}
        else:
            # Multiple tests
            results = await suite.run_multiple_tests(args.tests, ctx, args, parallel=args.parallel)
            
        elapsed = time.time() - start_time
        
        # Print summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        success_count = sum(1 for r in results.values() if r.get('success'))
        total_count = len(results)
        
        print(f"Total tests: {total_count}")
        print(f"Successful: {success_count}")
        print(f"Failed: {total_count - success_count}")
        print(f"Total time: {elapsed:.2f}s")
        
        # Print individual results
        for test_name, result in results.items():
            status = "PASS" if result.get('success') else "FAIL"
            elapsed = result.get('elapsed', 0)
            print(f"\n{test_name}: {status} ({elapsed:.2f}s)")
            
            if not result.get('success'):
                print(f"  Error: {result.get('error')}")
                
        # Save results if requested
        if args.save:
            filepath = ctx.persistence.save_json(results, "test_results")
            print(f"\nResults saved to: {filepath}")
            
    except Exception as e:
        logger.error(f"Test suite error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
    finally:
        await ctx.teardown()


if __name__ == "__main__":
    asyncio.run(main())