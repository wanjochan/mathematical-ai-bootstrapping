"""Monitoring service for CyberCorp server."""
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import platform
import psutil


class MonitoringService:
    """System monitoring and metrics service."""
    
    def __init__(self):
        """Initialize monitoring service."""
        self.is_monitoring = False
        self.metrics_cache = {}
        self._collect_task = None
        
    def initialize(self):
        """Initialize monitoring."""
        self.is_monitoring = True
        
    def start(self):
        """Start the monitoring service."""
        if not self.is_monitoring:
            self.initialize()
            
    def stop(self):
        """Stop the monitoring service."""
        self.is_monitoring = False
        if self._collect_task:
            self._collect_task.cancel()
            
    def is_running(self) -> bool:
        """Check if monitoring service is running."""
        return self.is_monitoring
        
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_used = memory.used / (1024**3)  # GB
            memory_total = memory.total / (1024**3)  # GB
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_used = disk.used / (1024**3)  # GB
            disk_total = disk.total / (1024**3)  # GB
            disk_percent = disk.percent
            
            # Network metrics
            net_io = psutil.net_io_counters()
            
            # Process metrics
            process_count = len(psutil.pids())
            
            metrics = {
                "cpu": {
                    "percentage": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "used_gb": round(memory_used, 2),
                    "total_gb": round(memory_total, 2),
                    "percentage": memory_percent
                },
                "disk": {
                    "used_gb": round(disk_used, 2),
                    "total_gb": round(disk_total, 2),
                    "percentage": disk_percent
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv
                },
                "processes": {
                    "count": process_count
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache metrics
            self.metrics_cache = metrics
            return metrics
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
    def get_cached_metrics(self) -> Optional[Dict[str, Any]]:
        """Get cached metrics if available."""
        return self.metrics_cache


# Global monitoring service instance
monitoring_service = MonitoringService()