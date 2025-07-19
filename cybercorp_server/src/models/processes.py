"""Process management data models."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from enum import Enum


class ProcessStatus(str, Enum):
    """Process status enumeration."""
    RUNNING = "running"
    SLEEPING = "sleeping"
    DISK_SLEEP = "disk_sleep"
    STOPPED = "stopped"
    TRACING_STOP = "tracing_stop"
    ZOMBIE = "zombie"
    DEAD = "dead"
    WAKE_KILL = "wake_kill"
    WAKING = "waking"
    IDLE = "idle"
    LOCKED = "locked"
    WAITING = "waiting"
    SUSPENDED = "suspended"


class ProcessAction(str, Enum):
    """Process action enumeration."""
    TERMINATE = "terminate"
    KILL = "kill"
    SUSPEND = "suspend"
    RESUME = "resume"
    NICE = "nice"
    IONICE = "ionice"
    CPU_AFFINITY = "cpu_affinity"
    MEMORY_LIMIT = "memory_limit"


class ProcessPriority(str, Enum):
    """Process priority enumeration."""
    REALTIME = "realtime"
    HIGH = "high"
    ABOVE_NORMAL = "above_normal"
    NORMAL = "normal"
    BELOW_NORMAL = "below_normal"
    IDLE = "idle"


class MemoryInfo(BaseModel):
    """Process memory information."""
    rss: int = Field(..., description="Resident Set Size in bytes")
    vms: int = Field(..., description="Virtual Memory Size in bytes")
    shared: Optional[int] = Field(None, description="Shared memory in bytes")
    text: Optional[int] = Field(None, description="Text (code) memory in bytes")
    lib: Optional[int] = Field(None, description="Library memory in bytes")
    data: Optional[int] = Field(None, description="Data memory in bytes")
    dirty: Optional[int] = Field(None, description="Dirty pages in bytes")
    uss: Optional[int] = Field(None, description="Unique Set Size in bytes")
    pss: Optional[int] = Field(None, description="Proportional Set Size in bytes")
    swap: Optional[int] = Field(None, description="Swap memory in bytes")


class IOCounters(BaseModel):
    """Process I/O counters."""
    read_count: int = Field(..., description="Number of read operations")
    write_count: int = Field(..., description="Number of write operations")
    read_bytes: int = Field(..., description="Number of bytes read")
    write_bytes: int = Field(..., description="Number of bytes written")
    read_chars: Optional[int] = Field(None, description="Number of characters read")
    write_chars: Optional[int] = Field(None, description="Number of characters written")


class NetworkConnection(BaseModel):
    """Network connection information."""
    fd: int = Field(..., description="File descriptor")
    family: str = Field(..., description="Address family (AF_INET, AF_INET6, etc.)")
    type: str = Field(..., description="Socket type (SOCK_STREAM, SOCK_DGRAM, etc.)")
    laddr: Tuple[str, int] = Field(..., description="Local address (host, port)")
    raddr: Optional[Tuple[str, int]] = Field(None, description="Remote address (host, port)")
    status: str = Field(..., description="Connection status")
    pid: Optional[int] = Field(None, description="Process ID")


class ProcessInfo(BaseModel):
    """Process information data model."""
    id: str = Field(..., description="Unique process identifier")
    pid: int = Field(..., description="Process ID")
    ppid: Optional[int] = Field(None, description="Parent process ID")
    name: str = Field(..., description="Process name")
    exe: Optional[str] = Field(None, description="Executable path")
    cmdline: List[str] = Field(default_factory=list, description="Command line arguments")
    cwd: Optional[str] = Field(None, description="Current working directory")
    status: ProcessStatus = Field(..., description="Process status")
    username: Optional[str] = Field(None, description="Process owner username")
    create_time: datetime = Field(..., description="Process creation time")
    cpu_percent: float = Field(..., ge=0, description="CPU usage percentage")
    memory_percent: float = Field(..., ge=0, le=100, description="Memory usage percentage")
    memory_info: Optional[MemoryInfo] = Field(None, description="Memory information")
    io_counters: Optional[IOCounters] = Field(None, description="I/O counters")
    num_threads: Optional[int] = Field(None, description="Number of threads")
    num_fds: Optional[int] = Field(None, description="Number of file descriptors")
    num_handles: Optional[int] = Field(None, description="Number of handles (Windows)")
    priority: Optional[ProcessPriority] = Field(None, description="Process priority")
    nice: Optional[int] = Field(None, description="Process nice value")
    ionice: Optional[int] = Field(None, description="Process I/O nice value")
    cpu_affinity: Optional[List[int]] = Field(None, description="CPU affinity mask")
    open_files: List[str] = Field(default_factory=list, description="List of open files")
    connections: List[NetworkConnection] = Field(default_factory=list, description="Network connections")
    environ: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    terminal: Optional[str] = Field(None, description="Terminal associated with process")
    gids: Optional[Tuple[int, int, int]] = Field(None, description="Real, effective, saved group IDs")
    uids: Optional[Tuple[int, int, int]] = Field(None, description="Real, effective, saved user IDs")
    cpu_times: Optional[Dict[str, float]] = Field(None, description="CPU times breakdown")
    memory_maps: Optional[List[Dict[str, Any]]] = Field(None, description="Memory maps")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


class ProcessControlRequest(BaseModel):
    """Process control request data model."""
    action: ProcessAction = Field(..., description="Action to perform on the process")
    force: bool = Field(False, description="Force the action if possible")
    timeout: Optional[int] = Field(None, ge=1, le=300, description="Timeout in seconds")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")


class ProcessTerminateRequest(BaseModel):
    """Process termination request parameters."""
    force: bool = Field(False, description="Force kill if terminate fails")
    timeout: int = Field(10, ge=1, le=300, description="Timeout before force kill")


class ProcessNiceRequest(BaseModel):
    """Process nice/priority request parameters."""
    nice_value: int = Field(..., ge=-20, le=19, description="Nice value (-20 to 19)")


class ProcessAffinityRequest(BaseModel):
    """Process CPU affinity request parameters."""
    cpu_list: List[int] = Field(..., description="List of CPU cores to bind to")


class ProcessQuery(BaseModel):
    """Query parameters for process listing."""
    status: Optional[ProcessStatus] = Field(None, description="Filter by process status")
    username: Optional[str] = Field(None, description="Filter by username")
    name_contains: Optional[str] = Field(None, description="Filter by name containing text")
    exe_contains: Optional[str] = Field(None, description="Filter by executable path containing text")
    min_cpu_percent: Optional[float] = Field(None, ge=0, description="Minimum CPU usage percentage")
    min_memory_percent: Optional[float] = Field(None, ge=0, le=100, description="Minimum memory usage percentage")
    sort_by: str = Field("cpu_percent", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Result offset for pagination")
    include_threads: bool = Field(False, description="Include thread information")
    include_connections: bool = Field(False, description="Include network connections")
    include_open_files: bool = Field(False, description="Include open files")
    include_environ: bool = Field(False, description="Include environment variables")


class ProcessListResponse(BaseModel):
    """Response model for process listing."""
    data: List[ProcessInfo] = Field(..., description="List of processes")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
    total: int = Field(..., description="Total number of processes")
    summary: Dict[str, Any] = Field(..., description="Process summary statistics")


class ProcessResponse(BaseModel):
    """Response model for single process operations."""
    data: ProcessInfo = Field(..., description="Process information")


class ProcessControlResponse(BaseModel):
    """Response model for process control operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Operation result message")
    process_id: str = Field(..., description="Process ID that was controlled")
    pid: int = Field(..., description="System process ID")
    action: ProcessAction = Field(..., description="Action that was performed")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional operation details")


class ProcessEvent(BaseModel):
    """Process event data model."""
    event_type: str = Field(..., description="Type of process event")
    process_id: str = Field(..., description="Process ID")
    pid: int = Field(..., description="System process ID")
    process_info: Optional[ProcessInfo] = Field(None, description="Process information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional event details")


class ProcessEventType(str, Enum):
    """Process event type enumeration."""
    CREATED = "process_created"
    TERMINATED = "process_terminated"
    STATUS_CHANGED = "process_status_changed"
    CPU_SPIKE = "process_cpu_spike"
    MEMORY_SPIKE = "process_memory_spike"
    SUSPENDED = "process_suspended"
    RESUMED = "process_resumed"
    PRIORITY_CHANGED = "process_priority_changed"
    AFFINITY_CHANGED = "process_affinity_changed"


class ProcessCreateRequest(BaseModel):
    """Request model for creating a new process."""
    command: str = Field(..., description="Command to execute")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    cwd: Optional[str] = Field(None, description="Working directory")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    detach: bool = Field(default=False, description="Run process in background")
    priority: ProcessPriority = Field(default=ProcessPriority.NORMAL, description="Process priority")
    cpu_limit: Optional[float] = Field(None, ge=0.1, le=100.0, description="CPU limit percentage")
    memory_limit: Optional[int] = Field(None, ge=1024, description="Memory limit in bytes")
    timeout: Optional[int] = Field(None, ge=1, description="Process timeout in seconds")
    capture_output: bool = Field(default=True, description="Capture stdout and stderr")
    shell: bool = Field(default=False, description="Execute in shell")


class ProcessStatistics(BaseModel):
    """Process statistics data model."""
    total_processes: int = Field(..., description="Total number of processes")
    running_processes: int = Field(..., description="Number of running processes")
    sleeping_processes: int = Field(..., description="Number of sleeping processes")
    stopped_processes: int = Field(..., description="Number of stopped processes")
    zombie_processes: int = Field(..., description="Number of zombie processes")
    total_cpu_percent: float = Field(..., description="Total CPU usage by all processes")
    total_memory_percent: float = Field(..., description="Total memory usage by all processes")
    top_cpu_processes: List[Dict[str, Any]] = Field(default_factory=list, description="Top CPU consuming processes")
    top_memory_processes: List[Dict[str, Any]] = Field(default_factory=list, description="Top memory consuming processes")
    process_count_by_user: Dict[str, int] = Field(default_factory=dict, description="Process count by user")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Statistics timestamp")


class ProcessTree(BaseModel):
    """Process tree data model."""
    process: ProcessInfo = Field(..., description="Process information")
    children: List["ProcessTree"] = Field(default_factory=list, description="Child processes")
    depth: int = Field(0, description="Depth in the process tree")


class ProcessFilter(BaseModel):
    """Process filtering criteria."""
    include_system_processes: bool = Field(True, description="Include system processes")
    include_kernel_threads: bool = Field(False, description="Include kernel threads")
    exclude_current_process: bool = Field(True, description="Exclude current process")
    min_uptime_seconds: Optional[int] = Field(None, ge=0, description="Minimum process uptime")
    max_uptime_seconds: Optional[int] = Field(None, ge=0, description="Maximum process uptime")
    exclude_usernames: List[str] = Field(default_factory=list, description="Usernames to exclude")
    include_usernames: List[str] = Field(default_factory=list, description="Usernames to include")
    exclude_process_names: List[str] = Field(default_factory=list, description="Process names to exclude")
    include_process_names: List[str] = Field(default_factory=list, description="Process names to include")


# Enable forward references for ProcessTree
ProcessTree.model_rebuild()