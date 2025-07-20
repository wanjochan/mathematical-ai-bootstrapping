"""
Health monitoring system for CyberCorp client
Tracks system health, performance metrics, and command execution status
"""

import time
import psutil
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import deque
import json

logger = logging.getLogger('HealthMonitor')

class HealthMonitor:
    """Monitors client health and performance"""
    
    def __init__(self, check_interval: float = 5.0):
        """
        Initialize health monitor
        
        Args:
            check_interval: How often to check health metrics (seconds)
        """
        self.check_interval = check_interval
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Metrics storage
        self.metrics: Dict[str, deque] = {
            'cpu_percent': deque(maxlen=60),  # Last 60 samples
            'memory_percent': deque(maxlen=60),
            'disk_io': deque(maxlen=60),
            'network_io': deque(maxlen=60),
            'heartbeat_latency': deque(maxlen=30),
            'command_success_rate': deque(maxlen=100),
            'command_response_time': deque(maxlen=100),
        }
        
        # Health status
        self.health_status = {
            'overall': 'healthy',
            'cpu': 'healthy',
            'memory': 'healthy',
            'network': 'healthy',
            'commands': 'healthy',
            'last_check': None
        }
        
        # Thresholds
        self.thresholds = {
            'cpu_warning': 70,
            'cpu_critical': 90,
            'memory_warning': 80,
            'memory_critical': 95,
            'heartbeat_timeout': 60,
            'command_failure_rate': 0.2  # 20% failure rate
        }
        
        # Callbacks
        self.health_callbacks: List[Callable] = []
        
        # Command tracking
        self.command_stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'timeout': 0,
            'in_progress': {}
        }
        
        # Last heartbeat time
        self.last_heartbeat = time.time()
        
    def update_heartbeat(self, latency: Optional[float] = None):
        """Update heartbeat timestamp and optionally latency"""
        self.last_heartbeat = time.time()
        if latency is not None:
            self.metrics['heartbeat_latency'].append(latency)
    
    def track_command_start(self, command_id: str, command: str):
        """Track command execution start"""
        self.command_stats['total'] += 1
        self.command_stats['in_progress'][command_id] = {
            'command': command,
            'start_time': time.time()
        }
    
    def track_command_end(self, command_id: str, success: bool, error: Optional[str] = None):
        """Track command execution end"""
        if command_id not in self.command_stats['in_progress']:
            return
        
        cmd_info = self.command_stats['in_progress'].pop(command_id)
        response_time = time.time() - cmd_info['start_time']
        
        self.metrics['command_response_time'].append(response_time)
        
        if success:
            self.command_stats['success'] += 1
            self.metrics['command_success_rate'].append(1.0)
        else:
            self.command_stats['failed'] += 1
            self.metrics['command_success_rate'].append(0.0)
            
            if error and 'timeout' in error.lower():
                self.command_stats['timeout'] += 1
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.metrics['cpu_percent'].append(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['memory_percent'].append(memory.percent)
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self.metrics['disk_io'].append({
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'timestamp': time.time()
                })
            
            # Network I/O
            net_io = psutil.net_io_counters()
            if net_io:
                self.metrics['network_io'].append({
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'timestamp': time.time()
                })
                
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _evaluate_health(self):
        """Evaluate overall health status"""
        old_status = self.health_status.copy()
        
        # Check CPU health
        if self.metrics['cpu_percent']:
            avg_cpu = sum(self.metrics['cpu_percent']) / len(self.metrics['cpu_percent'])
            if avg_cpu >= self.thresholds['cpu_critical']:
                self.health_status['cpu'] = 'critical'
            elif avg_cpu >= self.thresholds['cpu_warning']:
                self.health_status['cpu'] = 'warning'
            else:
                self.health_status['cpu'] = 'healthy'
        
        # Check memory health
        if self.metrics['memory_percent']:
            avg_memory = sum(self.metrics['memory_percent']) / len(self.metrics['memory_percent'])
            if avg_memory >= self.thresholds['memory_critical']:
                self.health_status['memory'] = 'critical'
            elif avg_memory >= self.thresholds['memory_warning']:
                self.health_status['memory'] = 'warning'
            else:
                self.health_status['memory'] = 'healthy'
        
        # Check heartbeat health
        heartbeat_age = time.time() - self.last_heartbeat
        if heartbeat_age > self.thresholds['heartbeat_timeout']:
            self.health_status['network'] = 'critical'
        elif heartbeat_age > self.thresholds['heartbeat_timeout'] / 2:
            self.health_status['network'] = 'warning'
        else:
            self.health_status['network'] = 'healthy'
        
        # Check command health
        if self.metrics['command_success_rate'] and len(self.metrics['command_success_rate']) >= 10:
            success_rate = sum(self.metrics['command_success_rate']) / len(self.metrics['command_success_rate'])
            if success_rate < (1 - self.thresholds['command_failure_rate']):
                self.health_status['commands'] = 'warning'
            else:
                self.health_status['commands'] = 'healthy'
        
        # Determine overall health
        statuses = [self.health_status[k] for k in ['cpu', 'memory', 'network', 'commands']]
        if 'critical' in statuses:
            self.health_status['overall'] = 'critical'
        elif 'warning' in statuses:
            self.health_status['overall'] = 'warning'
        else:
            self.health_status['overall'] = 'healthy'
        
        self.health_status['last_check'] = datetime.now().isoformat()
        
        # Trigger callbacks if health changed
        if old_status['overall'] != self.health_status['overall']:
            self._trigger_health_callbacks(old_status['overall'], self.health_status['overall'])
    
    def _trigger_health_callbacks(self, old_status: str, new_status: str):
        """Trigger health change callbacks"""
        for callback in self.health_callbacks:
            try:
                callback(old_status, new_status, self.health_status)
            except Exception as e:
                logger.error(f"Error in health callback: {e}")
    
    def add_health_callback(self, callback: Callable):
        """
        Add callback for health status changes
        
        Callback signature: callback(old_status: str, new_status: str, full_status: dict)
        """
        self.health_callbacks.append(callback)
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Health monitor started")
        
        while self.running:
            try:
                # Collect metrics
                await self._collect_system_metrics()
                
                # Evaluate health
                self._evaluate_health()
                
                # Log if unhealthy
                if self.health_status['overall'] != 'healthy':
                    logger.warning(f"Health status: {self.health_status['overall']} - {self.get_health_summary()}")
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
            
            await asyncio.sleep(self.check_interval)
        
        logger.info("Health monitor stopped")
    
    async def start(self):
        """Start health monitoring"""
        if self.running:
            logger.warning("Health monitor already running")
            return
        
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        """Stop health monitoring"""
        self.running = False
        
        if self.monitor_task:
            await self.monitor_task
            self.monitor_task = None
    
    def get_health_status(self) -> dict:
        """Get current health status"""
        return self.health_status.copy()
    
    def get_health_summary(self) -> str:
        """Get health summary string"""
        status = self.health_status
        parts = []
        
        if status['cpu'] != 'healthy':
            parts.append(f"CPU: {status['cpu']}")
        if status['memory'] != 'healthy':
            parts.append(f"Memory: {status['memory']}")
        if status['network'] != 'healthy':
            parts.append(f"Network: {status['network']}")
        if status['commands'] != 'healthy':
            parts.append(f"Commands: {status['commands']}")
        
        return ", ".join(parts) if parts else "All systems healthy"
    
    def get_metrics_summary(self) -> dict:
        """Get summary of current metrics"""
        summary = {
            'health_status': self.health_status,
            'system_metrics': {},
            'command_stats': self.command_stats.copy()
        }
        
        # Average system metrics
        if self.metrics['cpu_percent']:
            summary['system_metrics']['cpu_percent_avg'] = sum(self.metrics['cpu_percent']) / len(self.metrics['cpu_percent'])
            
        if self.metrics['memory_percent']:
            summary['system_metrics']['memory_percent_avg'] = sum(self.metrics['memory_percent']) / len(self.metrics['memory_percent'])
            
        if self.metrics['heartbeat_latency']:
            summary['system_metrics']['heartbeat_latency_avg'] = sum(self.metrics['heartbeat_latency']) / len(self.metrics['heartbeat_latency'])
            
        if self.metrics['command_response_time']:
            times = list(self.metrics['command_response_time'])
            summary['system_metrics']['command_response_avg'] = sum(times) / len(times)
            summary['system_metrics']['command_response_max'] = max(times)
            
        # Remove in-progress details for summary
        summary['command_stats'].pop('in_progress', None)
        
        return summary
    
    def export_metrics(self) -> dict:
        """Export all metrics for analysis"""
        return {
            'health_status': self.health_status,
            'metrics': {
                k: list(v) for k, v in self.metrics.items()
            },
            'command_stats': self.command_stats,
            'thresholds': self.thresholds,
            'export_time': datetime.now().isoformat()
        }