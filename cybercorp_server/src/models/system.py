"""System monitoring data models."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class CPUMetrics(BaseModel):
    """CPU metrics data model."""
    usage_percent: float = Field(..., ge=0, le=100, description="Overall CPU usage percentage")
    per_cpu: List[float] = Field(default_factory=list, description="Per-CPU usage percentages")
    frequency: Optional[float] = Field(None, description="CPU frequency in MHz")
    temperature: Optional[float] = Field(None, description="CPU temperature in Celsius")
    load_average: Optional[List[float]] = Field(None, description="Load average (1, 5, 15 minutes)")


class MemoryMetrics(BaseModel):
    """Memory metrics data model."""
    total: int = Field(..., description="Total memory in bytes")
    available: int = Field(..., description="Available memory in bytes")
    used: int = Field(..., description="Used memory in bytes")
    percent: float = Field(..., ge=0, le=100, description="Memory usage percentage")
    swap_total: Optional[int] = Field(None, description="Total swap memory in bytes")
    swap_used: Optional[int] = Field(None, description="Used swap memory in bytes")
    swap_percent: Optional[float] = Field(None, ge=0, le=100, description="Swap usage percentage")


class DiskMetrics(BaseModel):
    """Disk metrics data model."""
    total: int = Field(..., description="Total disk space in bytes")
    used: int = Field(..., description="Used disk space in bytes")
    free: int = Field(..., description="Free disk space in bytes")
    percent: float = Field(..., ge=0, le=100, description="Disk usage percentage")
    read_bytes: Optional[int] = Field(None, description="Bytes read from disk")
    write_bytes: Optional[int] = Field(None, description="Bytes written to disk")
    read_count: Optional[int] = Field(None, description="Number of read operations")
    write_count: Optional[int] = Field(None, description="Number of write operations")


class NetworkMetrics(BaseModel):
    """Network metrics data model."""
    bytes_sent: int = Field(..., description="Total bytes sent")
    bytes_recv: int = Field(..., description="Total bytes received")
    packets_sent: int = Field(..., description="Total packets sent")
    packets_recv: int = Field(..., description="Total packets received")
    errin: Optional[int] = Field(None, description="Total input errors")
    errout: Optional[int] = Field(None, description="Total output errors")
    dropin: Optional[int] = Field(None, description="Total input packets dropped")
    dropout: Optional[int] = Field(None, description="Total output packets dropped")


class SystemMetrics(BaseModel):
    """Complete system metrics data model."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    hostname: str = Field(..., description="System hostname")
    cpu: CPUMetrics = Field(..., description="CPU metrics")
    memory: MemoryMetrics = Field(..., description="Memory metrics")
    disk: DiskMetrics = Field(..., description="Disk metrics")
    network: NetworkMetrics = Field(..., description="Network metrics")
    uptime: Optional[float] = Field(None, description="System uptime in seconds")
    boot_time: Optional[datetime] = Field(None, description="System boot time")


class SystemInfo(BaseModel):
    """System information data model."""
    hostname: str = Field(..., description="System hostname")
    platform: str = Field(..., description="Operating system platform")
    platform_release: str = Field(..., description="OS release version")
    platform_version: str = Field(..., description="OS version details")
    architecture: str = Field(..., description="System architecture")
    processor: str = Field(..., description="Processor information")
    cpu_count: int = Field(..., description="Number of CPU cores")
    total_memory: int = Field(..., description="Total system memory in bytes")
    boot_time: datetime = Field(..., description="System boot time")
    uptime: float = Field(..., description="System uptime in seconds")
    python_version: str = Field(..., description="Python version")
    client_version: str = Field(..., description="Client software version")
    timezone: Optional[str] = Field(None, description="System timezone")
    locale: Optional[str] = Field(None, description="System locale")


class MetricsQuery(BaseModel):
    """Query parameters for metrics retrieval."""
    start_time: Optional[datetime] = Field(None, description="Start time for historical data")
    end_time: Optional[datetime] = Field(None, description="End time for historical data")
    interval: Optional[int] = Field(300, ge=60, le=3600, description="Aggregation interval in seconds")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to include")
    format: str = Field("json", regex="^(json|prometheus)$", description="Response format")
    detailed: bool = Field(False, description="Include detailed metrics")


class MetricsResponse(BaseModel):
    """Response model for metrics data."""
    data: SystemMetrics = Field(..., description="Metrics data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class HistoricalMetricsResponse(BaseModel):
    """Response model for historical metrics data."""
    data: List[SystemMetrics] = Field(..., description="Historical metrics data")
    pagination: Optional[Dict[str, Any]] = Field(None, description="Pagination information")
    aggregation: Optional[Dict[str, Any]] = Field(None, description="Aggregation details")


class SystemStatus(str, Enum):
    """System status enumeration."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class SystemHealth(BaseModel):
    """System health status model."""
    status: SystemStatus = Field(..., description="Overall system status")
    cpu_status: SystemStatus = Field(..., description="CPU health status")
    memory_status: SystemStatus = Field(..., description="Memory health status")
    disk_status: SystemStatus = Field(..., description="Disk health status")
    network_status: SystemStatus = Field(..., description="Network health status")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last health check time")
    issues: List[str] = Field(default_factory=list, description="List of detected issues")
    recommendations: List[str] = Field(default_factory=list, description="System recommendations")


class AlertThreshold(BaseModel):
    """Alert threshold configuration."""
    metric: str = Field(..., description="Metric name")
    warning_threshold: float = Field(..., description="Warning threshold value")
    critical_threshold: float = Field(..., description="Critical threshold value")
    duration: int = Field(300, description="Duration in seconds before triggering alert")
    enabled: bool = Field(True, description="Whether alert is enabled")


class SystemAlert(BaseModel):
    """System alert model."""
    id: str = Field(..., description="Alert ID")
    metric: str = Field(..., description="Metric that triggered the alert")
    level: SystemStatus = Field(..., description="Alert severity level")
    value: float = Field(..., description="Current metric value")
    threshold: float = Field(..., description="Threshold that was exceeded")
    message: str = Field(..., description="Alert message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Alert timestamp")
    acknowledged: bool = Field(False, description="Whether alert has been acknowledged")
    resolved: bool = Field(False, description="Whether alert has been resolved")