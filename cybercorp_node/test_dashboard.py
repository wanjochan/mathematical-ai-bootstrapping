"""
Test dashboard functionality - comprehensive system overview
"""

import asyncio
import json
import websockets
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestDashboard')

class DashboardData:
    """Collect and display dashboard data"""
    
    def __init__(self):
        self.clients = []
        self.health_data = {}
        self.performance_data = {}
        self.log_stats = {}
        self.system_info = {}
    
    def display(self):
        """Display dashboard in terminal"""
        print("\n" + "="*80)
        print(f"CyberCorp Node Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Client Overview
        print("\n📊 CLIENT OVERVIEW")
        print("-"*40)
        if self.clients:
            for client in self.clients:
                status = "🟢" if client.get('connected') else "🔴"
                print(f"{status} {client['id'][:8]}... | {client['user_session']} | Connected: {client.get('connected_time', 'N/A')}")
                
                # Show health status if available
                if client['id'] in self.health_data:
                    health = self.health_data[client['id']]
                    overall = health.get('health', {}).get('overall', 'unknown')
                    health_icon = {
                        'healthy': '✅',
                        'warning': '⚠️',
                        'critical': '❌',
                        'unknown': '❓'
                    }.get(overall, '❓')
                    print(f"   Health: {health_icon} {overall}")
                    
                    # Show metrics
                    metrics = health.get('metrics', {})
                    if 'system_metrics' in metrics:
                        sys_metrics = metrics['system_metrics']
                        print(f"   CPU: {sys_metrics.get('cpu_percent_avg', 0):.1f}% | "
                              f"Memory: {sys_metrics.get('memory_percent_avg', 0):.1f}% | "
                              f"Heartbeat: {sys_metrics.get('heartbeat_latency_avg', 0)*1000:.0f}ms")
                    
                    # Command stats
                    if 'command_stats' in metrics:
                        cmd_stats = metrics['command_stats']
                        total = cmd_stats.get('total', 0)
                        success = cmd_stats.get('success', 0)
                        if total > 0:
                            success_rate = success / total * 100
                            print(f"   Commands: {total} total, {success_rate:.1f}% success")
        else:
            print("No clients connected")
        
        # System Information
        print("\n💻 SYSTEM INFORMATION")
        print("-"*40)
        for client_id, info in self.system_info.items():
            print(f"Client {client_id[:8]}...")
            print(f"   Hostname: {info.get('hostname', 'N/A')}")
            print(f"   Platform: {info.get('platform', 'N/A')}")
            print(f"   CPU: {info.get('processor', 'N/A')} ({info.get('cpu_count', 0)} cores)")
            print(f"   Memory: {info.get('memory_gb', 0):.1f} GB")
            print(f"   User: {info.get('user', 'N/A')}")
        
        # Performance Overview
        print("\n⚡ PERFORMANCE METRICS")
        print("-"*40)
        for client_id, perf in self.performance_data.items():
            print(f"Client {client_id[:8]}...")
            for command, stats in perf.items():
                print(f"   {command}: {stats['avg_time']:.3f}s avg ({stats['count']} calls)")
        
        # Log Statistics
        print("\n📝 LOG STATISTICS")
        print("-"*40)
        for client_id, stats in self.log_stats.items():
            print(f"Client {client_id[:8]}...")
            print(f"   Total entries: {stats.get('total_entries', 0)}")
            print(f"   Error entries: {stats.get('error_entries', 0)}")
            if 'level_counts' in stats:
                level_str = ", ".join([f"{k}: {v}" for k, v in stats['level_counts'].items()])
                print(f"   Levels: {level_str}")
        
        # Feature Status
        print("\n🔧 FEATURE STATUS")
        print("-"*40)
        features = {
            'Hot Reload': any(c.get('capabilities', {}).get('hot_reload', False) for c in self.clients),
            'Health Monitor': len(self.health_data) > 0,
            'Unified Response': True,  # Always enabled now
            'Remote Restart': True,    # Always available
            'Window Control': any(c.get('capabilities', {}).get('vscode_control', False) for c in self.clients),
            'OCR Support': any(c.get('capabilities', {}).get('ocr', False) for c in self.clients),
        }
        
        for feature, enabled in features.items():
            status = "✅" if enabled else "❌"
            print(f"{status} {feature}")
        
        print("\n" + "="*80)

async def collect_dashboard_data(ws, dashboard: DashboardData):
    """Collect all dashboard data"""
    
    # Get client list
    await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
    response = await ws.recv()
    data = json.loads(response)
    
    dashboard.clients = data.get('clients', [])
    
    if not dashboard.clients:
        logger.warning("No clients connected")
        return
    
    # Collect data from each client
    for client in dashboard.clients:
        client_id = client['id']
        
        # Health status
        try:
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'health_status'
                }
            }))
            
            await ws.recv()  # ack
            
            result = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(result)
            
            if data.get('type') == 'command_result':
                result_data = data.get('result', {})
                if result_data.get('success'):
                    dashboard.health_data[client_id] = result_data.get('data', {})
        except:
            pass
        
        # System info
        try:
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'get_system_info'
                }
            }))
            
            await ws.recv()  # ack
            
            result = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(result)
            
            if data.get('type') == 'command_result':
                result_data = data.get('result', {})
                if result_data.get('success'):
                    dashboard.system_info[client_id] = result_data.get('data', {})
        except:
            pass
        
        # Log stats
        try:
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'get_log_stats'
                }
            }))
            
            await ws.recv()  # ack
            
            result = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(result)
            
            if data.get('type') == 'command_result':
                result_data = data.get('result', {})
                if result_data.get('success'):
                    dashboard.log_stats[client_id] = result_data.get('data', {}).get('stats', {})
        except:
            pass
        
        # Quick performance test
        perf_commands = ['get_windows', 'health_status']
        dashboard.performance_data[client_id] = {}
        
        for cmd in perf_commands:
            try:
                times = []
                for _ in range(3):
                    start = time.time()
                    
                    await ws.send(json.dumps({
                        'type': 'forward_command',
                        'target_client': client_id,
                        'command': {
                            'type': 'command',
                            'command': cmd
                        }
                    }))
                    
                    await ws.recv()  # ack
                    await asyncio.wait_for(ws.recv(), timeout=5.0)
                    
                    times.append(time.time() - start)
                
                if times:
                    dashboard.performance_data[client_id][cmd] = {
                        'avg_time': sum(times) / len(times),
                        'count': len(times)
                    }
            except:
                pass

async def test_dashboard(host='localhost', port=9998, refresh_interval=30):
    """Test dashboard functionality"""
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
        
        dashboard = DashboardData()
        
        # Initial collection
        logger.info("Collecting dashboard data...")
        await collect_dashboard_data(ws, dashboard)
        
        # Display dashboard
        dashboard.display()
        
        if refresh_interval > 0:
            logger.info(f"\nDashboard will refresh every {refresh_interval} seconds. Press Ctrl+C to stop.")
            
            try:
                while True:
                    await asyncio.sleep(refresh_interval)
                    
                    # Clear screen (works on Windows)
                    import os
                    os.system('cls' if os.name == 'nt' else 'clear')
                    
                    # Refresh data
                    dashboard = DashboardData()
                    await collect_dashboard_data(ws, dashboard)
                    dashboard.display()
                    
            except KeyboardInterrupt:
                logger.info("\nDashboard stopped by user")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='CyberCorp Node Dashboard')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    parser.add_argument('--refresh', type=int, default=0, 
                       help='Auto-refresh interval in seconds (0 to disable)')
    
    args = parser.parse_args()
    
    logger.info("Starting CyberCorp Node Dashboard...")
    
    asyncio.run(test_dashboard(args.host, args.port, args.refresh))

if __name__ == '__main__':
    main()