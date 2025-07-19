import asyncio
import psutil
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

from .models.processes import (
    ProcessInfo, ProcessStatus, ProcessAction, ProcessPriority,
    ProcessCreateRequest, ProcessResponse, ProcessStatistics,
    ProcessListResponse, ProcessControlResponse, ProcessEvent
)

logger = logging.getLogger(__name__)


class ProcessManager:
    """Central process management service for CyberCorp."""
    
    def __init__(self):
        self._processes: Dict[str, subprocess.Popen] = {}
        self._process_info: Dict[str, ProcessInfo] = {}
        self._task_events: List[ProcessEvent] = []
        
    def get_all_processes(self) -> ProcessListResponse:
        """Get list of all managed processes."""
        processes = []
        for proc_id, info in self._process_info.items():
            if proc_id in self._processes:
                self._update_process_metrics(proc_id)
            processes.append(info)
        return ProcessListResponse(processes=processes)
    
    def get_system_processes(self) -> ProcessListResponse:
        """Get list of active system processes."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                info = ProcessInfo(
                    id=f"sys_{proc.info['pid']}",
                    pid=proc.info['pid'],
                    name=proc.info['name'],
                    cmdline=proc.info['cmdline'] or [],
                    cpu_percent=proc.info['cpu_percent'] or 0,
                    memory_percent=proc.info['memory_percent'] or 0,
                    status=ProcessStatus.RUNNING,
                    create_time=datetime.fromtimestamp(proc.create_time())
                )
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return ProcessListResponse(processes=processes)
    
    def get_process_details(self, process_id: str) -> Optional[ProcessResponse]:
        """Get detailed information about a specific process."""
        if process_id in self._process_info:
            self._update_process_metrics(process_id)
            return ProcessResponse(
                success=True,
                process=self._process_info[process_id],
                statistics=self._get_process_statistics(process_id)
            )
        return None
    
    def create_process(self, request: ProcessCreateRequest) -> ProcessResponse:
        """Create a new process."""
        try:
            cmd = [request.command] + request.args
            
            env = dict(os.environ)
            env.update(request.env)
            
            proc = subprocess.Popen(
                cmd,
                cwd=request.cwd or os.getcwd(),
                env=env,
                shell=request.shell,
                stdout=subprocess.PIPE if request.capture_output else subprocess.DEVNULL,
                stderr=subprocess.PIPE if request.capture_output else subprocess.DEVNULL,
                text=True
            )
            
            process_id = f"proc_{int(time.time() * 1000)}"
            
            process_info = ProcessInfo(
                id=process_id,
                pid=proc.pid,
                name=request.command,
                cmdline=cmd,
                cwd=request.cwd or os.getcwd(),
                status=ProcessStatus.RUNNING,
                create_time=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                priority=request.priority,
                username=os.getenv('USERNAME', 'system')
            )
            
            self._processes[process_id] = proc
            self._process_info[process_id] = process_info
            
            # Log process creation event
            event = ProcessEvent(
                event_type="process_created",
                process_id=process_id,
                message=f"Created process {request.command}",
                timestamp=datetime.now()
            )
            self._task_events.append(event)
            
            return ProcessResponse(
                success=True,
                process=process_info,
                message=f"Process {process_id} created successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to create process: {e}")
            return ProcessResponse(success=False, message=str(e))
    
    def control_process(self, process_id: str, action: ProcessAction) -> ProcessControlResponse:
        """Control an existing process."""
        try:
            if process_id not in self._processes:
                return ProcessControlResponse(
                    success=False,
                    message=f"Process {process_id} not found"
                )
            
            proc = self._processes[process_id]
            info = self._process_info[process_id]
            
            if action == ProcessAction.TERMINATE:
                proc.terminate()
                info.status = ProcessStatus.TERMINATED
                message = "Process terminated"
            
            elif action == ProcessAction.KILL:
                proc.kill()
                info.status = ProcessStatus.TERMINATED
                message = "Process killed"
            
            elif action == ProcessAction.SUSPEND:
                proc.suspend() if hasattr(proc, 'suspend') else None
                info.status = ProcessStatus.SUSPENDED
                message = "Process suspended"
            
            elif action == ProcessAction.RESUME:
                proc.resume() if hasattr(proc, 'resume') else None
                info.status = ProcessStatus.RUNNING
                message = "Process resumed"
            
            else:
                return ProcessControlResponse(
                    success=False,
                    message=f"Unsupported action: {action}"
                )
            
            # Log process control event
            event = ProcessEvent(
                event_type=f"process_{action.value}",
                process_id=process_id,
                message=message,
                timestamp=datetime.now()
            )
            self._task_events.append(event)
            
            return ProcessControlResponse(
                success=True,
                message=message,
                process_id=process_id,
                details={"action": action.value, "current_status": info.status.value}
            )
            
        except Exception as e:
            logger.error(f"Failed to control process: {e}")
            return ProcessControlResponse(success=False, message=str(e))
    
    def get_process_events(self, limit: int = 100) -> List[ProcessEvent]:
        """Get recent process events."""
        return self._task_events[-limit:]
    
    def _update_process_metrics(self, process_id: str):
        """Update process metrics for an active process."""
        try:
            info = self._process_info[process_id]
            proc = psutil.Process(info.pid)
            
            cpu_percent = proc.cpu_percent()
            memory_info = proc.memory_info()
            
            info.cpu_percent = cpu_percent
            info.memory_percent = proc.memory_percent()
            info.num_threads = proc.num_threads()
            
        except psutil.NoSuchProcess:
            info.status = ProcessStatus.TERMINATED
            logger.warning(f"Process {process_id} (PID {info.pid}) no longer exists")
    
    def _get_process_statistics(self, process_id: str) -> ProcessStatistics:
        """Get detailed statistics for a process."""
        info = self._process_info[process_id]
        
        return ProcessStatistics(
            timestamp=datetime.now(),
            cpu_percent=info.cpu_percent,
            memory_percent=info.memory_percent,
            memory_usage=info.memory_info.rss if info.memory_info else 0,
            num_threads=info.num_threads or 0,
            uptime=(datetime.now() - info.create_time).total_seconds()
        )
    
    def cleanup(self):
        """Clean up terminated processes."""
        completed = []
        for process_id, proc in self._processes.items():
            if proc.poll() is not None:
                completed.append(process_id)
                if process_id in self._process_info:
                    self._process_info[process_id].status = ProcessStatus.TERMINATED
        
        for process_id in completed:
            del self._processes[process_id]


import os
processes_manager = ProcessManager()