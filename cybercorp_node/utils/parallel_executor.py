"""Parallel task execution framework for CyberCorp Node"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Callable, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import concurrent.futures
from functools import partial


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a task to be executed"""
    id: str
    name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    dependencies: List[str] = None
    priority: int = 0
    timeout: Optional[float] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    task_name: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: float = None
    end_time: float = None
    duration: float = None


class ParallelExecutor:
    """Execute tasks in parallel with dependency management"""
    
    def __init__(self, max_workers: int = 5, use_processes: bool = False):
        """Initialize parallel executor
        
        Args:
            max_workers: Maximum number of concurrent workers
            use_processes: Use processes instead of threads for CPU-bound tasks
        """
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.tasks: Dict[str, Task] = {}
        self.results: Dict[str, TaskResult] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
    def add_task(self, task: Task):
        """Add a task to the executor"""
        self.tasks[task.id] = task
        logger.debug(f"Added task: {task.name} (ID: {task.id})")
        
    def add_tasks(self, tasks: List[Task]):
        """Add multiple tasks"""
        for task in tasks:
            self.add_task(task)
            
    def _can_run_task(self, task: Task) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            if dep_id not in self.results:
                return False
            if self.results[dep_id].status != TaskStatus.COMPLETED:
                return False
        return True
        
    def _get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to run"""
        ready = []
        for task_id, task in self.tasks.items():
            if task_id not in self.results and self._can_run_task(task):
                ready.append(task)
                
        # Sort by priority (higher first)
        ready.sort(key=lambda t: t.priority, reverse=True)
        return ready
        
    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute a single task"""
        result = TaskResult(
            task_id=task.id,
            task_name=task.name,
            status=TaskStatus.RUNNING,
            start_time=time.time()
        )
        
        logger.info(f"Executing task: {task.name}")
        
        try:
            # Handle both sync and async functions
            if asyncio.iscoroutinefunction(task.func):
                # Async function
                if task.timeout:
                    task_result = await asyncio.wait_for(
                        task.func(*task.args, **task.kwargs),
                        timeout=task.timeout
                    )
                else:
                    task_result = await task.func(*task.args, **task.kwargs)
            else:
                # Sync function - run in executor
                loop = asyncio.get_event_loop()
                if self.use_processes:
                    executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)
                else:
                    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                    
                try:
                    if task.timeout:
                        task_result = await asyncio.wait_for(
                            loop.run_in_executor(
                                executor,
                                partial(task.func, *task.args, **task.kwargs)
                            ),
                            timeout=task.timeout
                        )
                    else:
                        task_result = await loop.run_in_executor(
                            executor,
                            partial(task.func, *task.args, **task.kwargs)
                        )
                finally:
                    executor.shutdown(wait=False)
                    
            result.result = task_result
            result.status = TaskStatus.COMPLETED
            logger.info(f"Task completed: {task.name}")
            
        except asyncio.TimeoutError:
            result.status = TaskStatus.FAILED
            result.error = f"Task timed out after {task.timeout} seconds"
            logger.error(f"Task timed out: {task.name}")
            
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            logger.error(f"Task failed: {task.name} - {e}")
            
        result.end_time = time.time()
        result.duration = result.end_time - result.start_time
        
        return result
        
    async def execute_all(self, continue_on_error: bool = True) -> Dict[str, TaskResult]:
        """Execute all tasks respecting dependencies
        
        Args:
            continue_on_error: Continue executing other tasks if one fails
            
        Returns:
            Dictionary of task results
        """
        logger.info(f"Starting parallel execution of {len(self.tasks)} tasks")
        start_time = time.time()
        
        # Reset results
        self.results = {}
        self.running_tasks = {}
        
        # Create a semaphore to limit concurrent tasks
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def run_task_with_semaphore(task: Task):
            async with semaphore:
                return await self._execute_task(task)
        
        # Main execution loop
        while len(self.results) < len(self.tasks):
            # Get ready tasks
            ready_tasks = self._get_ready_tasks()
            
            if not ready_tasks and not self.running_tasks:
                # No tasks can run - check for circular dependencies
                remaining = set(self.tasks.keys()) - set(self.results.keys())
                if remaining:
                    logger.error(f"Circular dependency detected. Remaining tasks: {remaining}")
                    for task_id in remaining:
                        self.results[task_id] = TaskResult(
                            task_id=task_id,
                            task_name=self.tasks[task_id].name,
                            status=TaskStatus.FAILED,
                            error="Circular dependency"
                        )
                break
                
            # Start ready tasks
            for task in ready_tasks:
                if task.id not in self.running_tasks:
                    task_coro = run_task_with_semaphore(task)
                    self.running_tasks[task.id] = asyncio.create_task(task_coro)
                    
            # Wait for at least one task to complete
            if self.running_tasks:
                done, pending = await asyncio.wait(
                    self.running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task_future in done:
                    result = await task_future
                    self.results[result.task_id] = result
                    
                    # Remove from running tasks
                    del self.running_tasks[result.task_id]
                    
                    # Check if we should stop on error
                    if result.status == TaskStatus.FAILED and not continue_on_error:
                        logger.error(f"Stopping execution due to failed task: {result.task_name}")
                        # Cancel remaining tasks
                        for task_id, task_future in self.running_tasks.items():
                            task_future.cancel()
                            self.results[task_id] = TaskResult(
                                task_id=task_id,
                                task_name=self.tasks[task_id].name,
                                status=TaskStatus.CANCELLED
                            )
                        break
                        
        # Wait for any remaining tasks
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
            
        elapsed = time.time() - start_time
        logger.info(f"Parallel execution completed in {elapsed:.2f}s")
        
        # Log summary
        completed = sum(1 for r in self.results.values() if r.status == TaskStatus.COMPLETED)
        failed = sum(1 for r in self.results.values() if r.status == TaskStatus.FAILED)
        logger.info(f"Results: {completed} completed, {failed} failed")
        
        return self.results
        
    def visualize_dependencies(self) -> str:
        """Create a simple text visualization of task dependencies"""
        lines = ["Task Dependency Graph:", "=" * 50]
        
        for task_id, task in self.tasks.items():
            deps = " <- " + ", ".join(task.dependencies) if task.dependencies else ""
            lines.append(f"{task.name} ({task_id}){deps}")
            
        return "\n".join(lines)
        
    def get_execution_order(self) -> List[List[str]]:
        """Get the execution order as levels (tasks that can run in parallel)"""
        levels = []
        executed = set()
        
        while len(executed) < len(self.tasks):
            level = []
            for task_id, task in self.tasks.items():
                if task_id not in executed:
                    # Check if all dependencies are executed
                    if all(dep in executed for dep in task.dependencies):
                        level.append(task_id)
                        
            if not level:
                # No progress - circular dependency
                break
                
            levels.append(level)
            executed.update(level)
            
        return levels


class TaskBuilder:
    """Helper class to build tasks easily"""
    
    def __init__(self):
        self.tasks = []
        self.task_counter = 0
        
    def add(self, name: str, func: Callable, *args, 
            dependencies: List[str] = None, priority: int = 0,
            timeout: Optional[float] = None, **kwargs) -> str:
        """Add a task and return its ID"""
        task_id = f"task_{self.task_counter}"
        self.task_counter += 1
        
        task = Task(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            dependencies=dependencies or [],
            priority=priority,
            timeout=timeout
        )
        
        self.tasks.append(task)
        return task_id
        
    def add_sequence(self, tasks: List[Tuple[str, Callable, tuple]]) -> List[str]:
        """Add tasks that must run in sequence"""
        task_ids = []
        prev_id = None
        
        for name, func, args in tasks:
            deps = [prev_id] if prev_id else []
            task_id = self.add(name, func, *args, dependencies=deps)
            task_ids.append(task_id)
            prev_id = task_id
            
        return task_ids
        
    def add_parallel(self, tasks: List[Tuple[str, Callable, tuple]]) -> List[str]:
        """Add tasks that can run in parallel"""
        task_ids = []
        
        for name, func, args in tasks:
            task_id = self.add(name, func, *args)
            task_ids.append(task_id)
            
        return task_ids
        
    def build(self) -> List[Task]:
        """Get the built tasks"""
        return self.tasks


# Example usage functions for testing
async def example_async_task(name: str, duration: float = 1.0) -> str:
    """Example async task"""
    logger.info(f"Starting async task: {name}")
    await asyncio.sleep(duration)
    logger.info(f"Completed async task: {name}")
    return f"Result from {name}"


def example_sync_task(name: str, duration: float = 1.0) -> str:
    """Example sync task"""
    logger.info(f"Starting sync task: {name}")
    time.sleep(duration)
    logger.info(f"Completed sync task: {name}")
    return f"Result from {name}"