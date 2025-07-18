"""Process service module for CyberCorp Server."""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio
import platform
import psutil
import os
import signal
import subprocess

from ..logging_config import get_logger

logger = get_logger(__name__)


class ProcessService:
    """Service for process management operations."""
    
    def __init__(self):
        """Initialize the process service."""
        self.platform = platform.system()
        self.process_cache = {}
        self.cache_expiry = 3  # seconds
        self.last_cache_update = None
        self.managed_processes = {}
    
    async def initialize(self):
        """Initialize the service."""
        logger.info(f"Process service initialized for platform: {self.platform}")
    
    async def shutdown(self):
        """Shutdown the service."""
        # Terminate all managed processes
        for process_id, process_info in list(self.managed_processes.items()):
            try:
                await self.terminate_process(process_id)
            except Exception as e:
                logger.error(f"Error terminating managed process {process_id} during shutdown: {e}")
        
        logger.info("Process service shutting down")
    
    async def list_processes(self, name_filter: Optional[str] = None, limit: int = 100, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """List processes."""
        try:
            # Check if cache is valid
            now = datetime.utcnow()
            if not self.last_cache_update or (now - self.last_cache_update).total_seconds() > self.cache_expiry:
                # Cache expired, refresh processes
                await self._refresh_process_cache()
            
            # Filter processes
            filtered_processes = []
            for proc in self.process_cache.values():
                if name_filter and name_filter.lower() not in proc["name"].lower():
                    continue
                filtered_processes.append(proc)
            
            # Sort by CPU usage (descending)
            filtered_processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
            
            # Apply pagination
            total = len(filtered_processes)
            paginated_processes = filtered_processes[offset:offset + limit]
            
            return paginated_processes, total
        except Exception as e:
            logger.error(f"Error listing processes: {e}")
            raise
    
    async def get_process(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get process by PID."""
        try:
            # Check if process is in cache
            if pid in self.process_cache:
                return self.process_cache[pid]
            
            # Not in cache, get directly
            try:
                proc = psutil.Process(pid)
                process_info = await self._get_process_info(proc)
                
                # Add to cache
                self.process_cache[pid] = process_info
                
                return process_info
            except psutil.NoSuchProcess:
                return None
        except Exception as e:
            logger.error(f"Error getting process {pid}: {e}")
            raise
    
    async def terminate_process(self, pid: int) -> bool:
        """Terminate a process."""
        try:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                
                # Wait for process to terminate
                try:
                    proc.wait(timeout=5)  # Wait up to 5 seconds
                except psutil.TimeoutExpired:
                    # Process didn't terminate, force kill
                    proc.kill()
                
                # Remove from cache
                if pid in self.process_cache:
                    del self.process_cache[pid]
                
                # Remove from managed processes
                if pid in self.managed_processes:
                    del self.managed_processes[pid]
                
                return True
            except psutil.NoSuchProcess:
                # Process already terminated
                return True
        except Exception as e:
            logger.error(f"Error terminating process {pid}: {e}")
            raise
    
    async def kill_process(self, pid: int) -> bool:
        """Kill a process."""
        try:
            try:
                proc = psutil.Process(pid)
                proc.kill()
                
                # Remove from cache
                if pid in self.process_cache:
                    del self.process_cache[pid]
                
                # Remove from managed processes
                if pid in self.managed_processes:
                    del self.managed_processes[pid]
                
                return True
            except psutil.NoSuchProcess:
                # Process already terminated
                return True
        except Exception as e:
            logger.error(f"Error killing process {pid}: {e}")
            raise
    
    async def suspend_process(self, pid: int) -> bool:
        """Suspend a process."""
        try:
            try:
                proc = psutil.Process(pid)
                proc.suspend()
                
                # Update cache
                if pid in self.process_cache:
                    self.process_cache[pid]["status"] = "stopped"
                
                return True
            except psutil.NoSuchProcess:
                return False
        except Exception as e:
            logger.error(f"Error suspending process {pid}: {e}")
            raise
    
    async def resume_process(self, pid: int) -> bool:
        """Resume a suspended process."""
        try:
            try:
                proc = psutil.Process(pid)
                proc.resume()
                
                # Update cache
                if pid in self.process_cache:
                    self.process_cache[pid]["status"] = "running"
                
                return True
            except psutil.NoSuchProcess:
                return False
        except Exception as e:
            logger.error(f"Error resuming process {pid}: {e}")
            raise
    
    async def get_process_memory(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get process memory usage."""
        try:
            try:
                proc = psutil.Process(pid)
                memory_info = proc.memory_info()
                memory_percent = proc.memory_percent()
                
                return {
                    "rss": memory_info.rss,  # Resident Set Size
                    "vms": memory_info.vms,  # Virtual Memory Size
                    "shared": getattr(memory_info, "shared", 0),  # Shared memory
                    "text": getattr(memory_info, "text", 0),  # Text (code)
                    "data": getattr(memory_info, "data", 0),  # Data + stack
                    "lib": getattr(memory_info, "lib", 0),  # Library
                    "dirty": getattr(memory_info, "dirty", 0),  # Dirty pages
                    "percent": memory_percent
                }
            except psutil.NoSuchProcess:
                return None
        except Exception as e:
            logger.error(f"Error getting process memory {pid}: {e}")
            raise
    
    async def get_process_cpu(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get process CPU usage."""
        try:
            try:
                proc = psutil.Process(pid)
                cpu_percent = proc.cpu_percent(interval=0.1)
                cpu_times = proc.cpu_times()
                
                return {
                    "percent": cpu_percent,
                    "user": cpu_times.user,
                    "system": cpu_times.system,
                    "children_user": getattr(cpu_times, "children_user", 0),
                    "children_system": getattr(cpu_times, "children_system", 0),
                    "iowait": getattr(cpu_times, "iowait", 0)
                }
            except psutil.NoSuchProcess:
                return None
        except Exception as e:
            logger.error(f"Error getting process CPU {pid}: {e}")
            raise
    
    async def get_process_io(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get process I/O statistics."""
        try:
            try:
                proc = psutil.Process(pid)
                io_counters = proc.io_counters() if hasattr(proc, "io_counters") else None
                
                if io_counters:
                    return {
                        "read_count": io_counters.read_count,
                        "write_count": io_counters.write_count,
                        "read_bytes": io_counters.read_bytes,
                        "write_bytes": io_counters.write_bytes,
                        "other_count": getattr(io_counters, "other_count", 0),
                        "other_bytes": getattr(io_counters, "other_bytes", 0)
                    }
                return None
            except psutil.NoSuchProcess:
                return None
        except Exception as e:
            logger.error(f"Error getting process IO {pid}: {e}")
            raise
    
    async def get_process_connections(self, pid: int) -> Optional[List[Dict[str, Any]]]:
        """Get process network connections."""
        try:
            try:
                proc = psutil.Process(pid)
                connections = proc.connections()
                
                result = []
                for conn in connections:
                    conn_info = {
                        "fd": conn.fd,
                        "family": conn.family,
                        "type": conn.type,
                        "status": conn.status,
                    }
                    
                    # Add local address if available
                    if conn.laddr:
                        conn_info["local_ip"] = conn.laddr.ip
                        conn_info["local_port"] = conn.laddr.port
                    
                    # Add remote address if available
                    if conn.raddr:
                        conn_info["remote_ip"] = conn.raddr.ip
                        conn_info["remote_port"] = conn.raddr.port
                    
                    result.append(conn_info)
                
                return result
            except psutil.NoSuchProcess:
                return None
        except Exception as e:
            logger.error(f"Error getting process connections {pid}: {e}")
            raise
    
    async def get_process_threads(self, pid: int) -> Optional[List[Dict[str, Any]]]:
        """Get process threads."""
        try:
            try:
                proc = psutil.Process(pid)
                threads = proc.threads()
                
                result = []
                for thread in threads:
                    thread_info = {
                        "id": thread.id,
                        "user_time": thread.user_time,
                        "system_time": thread.system_time
                    }
                    result.append(thread_info)
                
                return result
            except psutil.NoSuchProcess:
                return None
        except Exception as e:
            logger.error(f"Error getting process threads {pid}: {e}")
            raise
    
    async def get_process_files(self, pid: int) -> Optional[List[Dict[str, Any]]]:
        """Get files opened by process."""
        try:
            try:
                proc = psutil.Process(pid)
                files = proc.open_files()
                
                result = []
                for file in files:
                    file_info = {
                        "path": file.path,
                        "fd": file.fd,
                        "position": getattr(file, "position", 0),
                        "mode": getattr(file, "mode", "")
                    }
                    result.append(file_info)
                
                return result
            except psutil.NoSuchProcess:
                return None
        except Exception as e:
            logger.error(f"Error getting process files {pid}: {e}")
            raise
    
    async def start_process(self, command: str, args: List[str] = None, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Start a new process."""
        try:
            # Prepare command and arguments
            if args is None:
                args = []
            
            cmd = [command] + args
            
            # Start process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
            )
            
            # Get process info
            try:
                proc = psutil.Process(process.pid)
                process_info = await self._get_process_info(proc)
                
                # Add to cache
                self.process_cache[process.pid] = process_info
                
                # Add to managed processes
                self.managed_processes[process.pid] = {
                    "process": process,
                    "command": command,
                    "args": args,
                    "cwd": cwd,
                    "env": env,
                    "started_at": datetime.utcnow().isoformat()
                }
                
                # Start output reader tasks
                asyncio.create_task(self._read_process_output(process.pid, process))
                
                return {
                    "pid": process.pid,
                    **process_info
                }
            except psutil.NoSuchProcess:
                # Process already terminated
                return {
                    "pid": process.pid,
                    "name": command,
                    "status": "terminated",
                    "created": datetime.utcnow().isoformat(),
                    "error": "Process terminated immediately"
                }
        except Exception as e:
            logger.error(f"Error starting process '{command}': {e}")
            raise
    
    async def get_process_output(self, pid: int, max_lines: int = 100) -> Optional[Dict[str, Any]]:
        """Get process output (stdout and stderr)."""
        try:
            if pid not in self.managed_processes:
                return None
            
            process_info = self.managed_processes[pid]
            
            # Get output from process info
            stdout = process_info.get("stdout", [])
            stderr = process_info.get("stderr", [])
            
            # Limit to max_lines
            if len(stdout) > max_lines:
                stdout = stdout[-max_lines:]
            if len(stderr) > max_lines:
                stderr = stderr[-max_lines:]
            
            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": process_info.get("exit_code"),
                "running": process_info["process"].returncode is None
            }
        except Exception as e:
            logger.error(f"Error getting process output {pid}: {e}")
            raise
    
    async def send_signal(self, pid: int, signal_num: int) -> bool:
        """Send a signal to a process."""
        try:
            try:
                os.kill(pid, signal_num)
                return True
            except ProcessLookupError:
                return False
        except Exception as e:
            logger.error(f"Error sending signal {signal_num} to process {pid}: {e}")
            raise
    
    async def _refresh_process_cache(self) -> None:
        """Refresh the process cache."""
        try:
            # Get all processes
            processes = {}
            for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'create_time', 'memory_percent', 'cpu_percent']):
                try:
                    process_info = await self._get_process_info(proc)
                    processes[proc.pid] = process_info
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Update cache
            self.process_cache = processes
            self.last_cache_update = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error refreshing process cache: {e}")
            raise
    
    async def _get_process_info(self, proc: psutil.Process) -> Dict[str, Any]:
        """Get detailed information about a process."""
        try:
            # Get basic info
            with proc.oneshot():
                info = {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "status": proc.status(),
                    "username": proc.username(),
                    "created": datetime.fromtimestamp(proc.create_time()).isoformat(),
                    "cpu_percent": proc.cpu_percent(interval=0),
                    "memory_percent": proc.memory_percent(),
                    "command_line": proc.cmdline() if hasattr(proc, "cmdline") else [],
                    "exe": proc.exe() if hasattr(proc, "exe") else None,
                    "cwd": proc.cwd() if hasattr(proc, "cwd") else None,
                    "num_threads": proc.num_threads() if hasattr(proc, "num_threads") else None,
                    "parent": proc.ppid() if hasattr(proc, "ppid") else None,
                    "children": [child.pid for child in proc.children()] if hasattr(proc, "children") else []
                }
                
                # Get memory info
                try:
                    memory_info = proc.memory_info()
                    info["memory"] = {
                        "rss": memory_info.rss,
                        "vms": memory_info.vms
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                # Get CPU times
                try:
                    cpu_times = proc.cpu_times()
                    info["cpu_times"] = {
                        "user": cpu_times.user,
                        "system": cpu_times.system
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            raise
    
    async def _read_process_output(self, pid: int, process: asyncio.subprocess.Process) -> None:
        """Read and store process output."""
        try:
            # Initialize output buffers
            if pid in self.managed_processes:
                self.managed_processes[pid]["stdout"] = []
                self.managed_processes[pid]["stderr"] = []
            
            # Read stdout
            stdout_task = asyncio.create_task(self._read_stream(pid, process.stdout, "stdout"))
            
            # Read stderr
            stderr_task = asyncio.create_task(self._read_stream(pid, process.stderr, "stderr"))
            
            # Wait for process to complete
            exit_code = await process.wait()
            
            # Wait for output readers to complete
            await stdout_task
            await stderr_task
            
            # Update process info
            if pid in self.managed_processes:
                self.managed_processes[pid]["exit_code"] = exit_code
                self.managed_processes[pid]["completed_at"] = datetime.utcnow().isoformat()
            
            # Update cache
            if pid in self.process_cache:
                self.process_cache[pid]["status"] = "terminated"
            
            logger.info(f"Process {pid} completed with exit code {exit_code}")
        except Exception as e:
            logger.error(f"Error reading process output for {pid}: {e}")
    
    async def _read_stream(self, pid: int, stream, stream_name: str) -> None:
        """Read from a process output stream."""
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                
                # Decode line
                try:
                    line_str = line.decode("utf-8").rstrip()
                except UnicodeDecodeError:
                    line_str = line.decode("latin-1").rstrip()
                
                # Store line
                if pid in self.managed_processes:
                    self.managed_processes[pid][stream_name].append(line_str)
                    
                    # Limit buffer size
                    max_lines = 1000
                    if len(self.managed_processes[pid][stream_name]) > max_lines:
                        self.managed_processes[pid][stream_name] = self.managed_processes[pid][stream_name][-max_lines:]
        except Exception as e:
            logger.error(f"Error reading from {stream_name} for process {pid}: {e}")


# Singleton instance
process_service = ProcessService()