"""Task service module for CyberCorp Server."""

from typing import Dict, Any, List, Optional, Tuple
from uuid import uuid4
from datetime import datetime

from ..models.tasks import (
    Task, TaskCreate, TaskUpdate, TaskStatus, TaskType,
    TaskQuery, TaskComment, TaskDependency
)
from ..database import get_db_connection
from ..logging_config import get_logger

logger = get_logger(__name__)


class TaskService:
    """Service for task management operations."""
    
    def __init__(self):
        """Initialize the task service."""
        self.db = None
    
    async def initialize(self):
        """Initialize the service with database connection."""
        self.db = await get_db_connection()
        logger.info("Task service initialized")
    
    async def shutdown(self):
        """Shutdown the service."""
        logger.info("Task service shutting down")
    
    async def list_tasks(self, query: TaskQuery) -> List[Task]:
        """List tasks based on query parameters."""
        try:
            # Build query
            filter_conditions = {}
            if query.type is not None:
                filter_conditions["type"] = query.type
            if query.status is not None:
                filter_conditions["status"] = query.status
            if query.assigned_to is not None:
                filter_conditions["assigned_to"] = query.assigned_to
            if query.created_by is not None:
                filter_conditions["created_by"] = query.created_by
            if query.project_id is not None:
                filter_conditions["project_id"] = query.project_id
            if query.tag is not None:
                filter_conditions["tags"] = {"$in": [query.tag]}
            if query.name_contains is not None:
                filter_conditions["name"] = {"$regex": query.name_contains, "$options": "i"}
            
            # Execute query
            cursor = self.db.tasks.find(
                filter_conditions,
                skip=query.offset,
                limit=query.limit
            ).sort("created_at", -1)  # Newest first
            
            # Convert to list of Task objects
            tasks = []
            async for doc in cursor:
                tasks.append(Task(**doc))
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            raise
    
    async def count_tasks(self, query: TaskQuery) -> int:
        """Count tasks based on query parameters."""
        try:
            # Build query
            filter_conditions = {}
            if query.type is not None:
                filter_conditions["type"] = query.type
            if query.status is not None:
                filter_conditions["status"] = query.status
            if query.assigned_to is not None:
                filter_conditions["assigned_to"] = query.assigned_to
            if query.created_by is not None:
                filter_conditions["created_by"] = query.created_by
            if query.project_id is not None:
                filter_conditions["project_id"] = query.project_id
            if query.tag is not None:
                filter_conditions["tags"] = {"$in": [query.tag]}
            if query.name_contains is not None:
                filter_conditions["name"] = {"$regex": query.name_contains, "$options": "i"}
            
            # Count documents
            count = await self.db.tasks.count_documents(filter_conditions)
            return count
            
        except Exception as e:
            logger.error(f"Error counting tasks: {e}")
            raise
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        try:
            doc = await self.db.tasks.find_one({"id": task_id})
            if doc:
                return Task(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            raise
    
    async def create_task(self, task: Task) -> Task:
        """Create a new task."""
        try:
            # Set created_at and updated_at
            now = datetime.utcnow()
            task_dict = task.dict()
            task_dict["created_at"] = now
            task_dict["updated_at"] = now
            
            # Insert into database
            await self.db.tasks.insert_one(task_dict)
            
            # Return the created task
            return Task(**task_dict)
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            raise
    
    async def update_task(self, task_id: str, task_update: TaskUpdate) -> Optional[Task]:
        """Update a task."""
        try:
            # Get existing task
            existing = await self.get_task(task_id)
            if not existing:
                return None
            
            # Prepare update
            update_data = task_update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            # Update in database
            await self.db.tasks.update_one(
                {"id": task_id},
                {"$set": update_data}
            )
            
            # Get and return updated task
            return await self.get_task(task_id)
            
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            raise
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        try:
            # Delete from database
            result = await self.db.tasks.delete_one({"id": task_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            raise
    
    async def update_task_status(self, task_id: str, status: TaskStatus, reason: Optional[str] = None, progress_percentage: Optional[int] = None) -> Optional[Task]:
        """Update task status."""
        try:
            # Get existing task
            existing = await self.get_task(task_id)
            if not existing:
                return None
            
            # Prepare update
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            # Set progress percentage if provided
            if progress_percentage is not None:
                update_data["progress_percentage"] = progress_percentage
            
            # Set started_at if moving to IN_PROGRESS
            if status == TaskStatus.IN_PROGRESS and existing.status != TaskStatus.IN_PROGRESS:
                update_data["started_at"] = datetime.utcnow()
            
            # Set completed_at if moving to COMPLETED or FAILED
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and existing.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                update_data["completed_at"] = datetime.utcnow()
            
            # Add status change history
            status_change = {
                "from": existing.status,
                "to": status,
                "timestamp": datetime.utcnow(),
                "reason": reason
            }
            
            # Update in database
            await self.db.tasks.update_one(
                {"id": task_id},
                {
                    "$set": update_data,
                    "$push": {"status_history": status_change}
                }
            )
            
            # Get and return updated task
            return await self.get_task(task_id)
            
        except Exception as e:
            logger.error(f"Error updating task status {task_id}: {e}")
            raise
    
    async def assign_task(self, task_id: str, employee_id: str, message: Optional[str] = None) -> Optional[Task]:
        """Assign task to an employee."""
        try:
            # Get existing task
            existing = await self.get_task(task_id)
            if not existing:
                return None
            
            # Prepare update
            update_data = {
                "assigned_to": employee_id,
                "updated_at": datetime.utcnow()
            }
            
            # Add assignment history
            assignment = {
                "from": existing.assigned_to,
                "to": employee_id,
                "timestamp": datetime.utcnow(),
                "message": message
            }
            
            # Update in database
            await self.db.tasks.update_one(
                {"id": task_id},
                {
                    "$set": update_data,
                    "$push": {"assignment_history": assignment}
                }
            )
            
            # Get and return updated task
            return await self.get_task(task_id)
            
        except Exception as e:
            logger.error(f"Error assigning task {task_id}: {e}")
            raise
    
    async def execute_task(self, task_id: str, parameters: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute a task."""
        try:
            # Get existing task
            existing = await self.get_task(task_id)
            if not existing:
                raise ValueError("Task not found")
            
            # Generate execution ID
            execution_id = str(uuid4())
            started_at = datetime.utcnow()
            
            # Update task status to IN_PROGRESS
            await self.update_task_status(task_id, TaskStatus.IN_PROGRESS, "Task execution started")
            
            # Execute task based on type
            result = None
            status = "SUCCESS"
            error = None
            
            try:
                # Different execution logic based on task type
                if existing.type == TaskType.SYSTEM_COMMAND:
                    # Execute system command
                    # This is a placeholder - actual implementation would depend on system requirements
                    result = {"message": "System command executed successfully"}
                    
                elif existing.type == TaskType.DATA_PROCESSING:
                    # Process data
                    # This is a placeholder - actual implementation would depend on data processing requirements
                    result = {"message": "Data processed successfully"}
                    
                elif existing.type == TaskType.MONITORING:
                    # Run monitoring task
                    # This is a placeholder - actual implementation would depend on monitoring requirements
                    result = {"message": "Monitoring task executed successfully"}
                    
                else:
                    # Generic task execution
                    result = {"message": "Task executed successfully"}
                
                # Update task status to COMPLETED
                await self.update_task_status(task_id, TaskStatus.COMPLETED, "Task execution completed successfully")
                
            except Exception as e:
                # Handle execution error
                status = "FAILED"
                error = str(e)
                
                # Update task status to FAILED
                await self.update_task_status(task_id, TaskStatus.FAILED, f"Task execution failed: {error}")
            
            # Record execution completion
            completed_at = datetime.utcnow()
            
            # Create execution record
            execution_record = {
                "execution_id": execution_id,
                "task_id": task_id,
                "parameters": parameters,
                "status": status,
                "result": result,
                "error": error,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_seconds": (completed_at - started_at).total_seconds()
            }
            
            # Store execution record
            await self.db.task_executions.insert_one(execution_record)
            
            # Return execution result
            return {
                "execution_id": execution_id,
                "status": status,
                "result": result,
                "error": error,
                "started_at": started_at,
                "completed_at": completed_at
            }
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
            raise
    
    async def get_task_history(self, task_id: str, limit: int = 100, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """Get task history."""
        try:
            # Get existing task
            existing = await self.get_task(task_id)
            if not existing:
                raise ValueError("Task not found")
            
            # Query task executions
            cursor = self.db.task_executions.find(
                {"task_id": task_id},
                skip=offset,
                limit=limit
            ).sort("started_at", -1)  # Newest first
            
            # Convert to list of dictionaries
            history = []
            async for doc in cursor:
                # Remove _id field
                doc.pop("_id", None)
                history.append(doc)
            
            # Count total executions
            total = await self.db.task_executions.count_documents({"task_id": task_id})
            
            return history, total
            
        except Exception as e:
            logger.error(f"Error getting task history {task_id}: {e}")
            raise
    
    async def get_task_comments(self, task_id: str, limit: int = 100, offset: int = 0) -> Tuple[List[TaskComment], int]:
        """Get task comments."""
        try:
            # Get existing task
            existing = await self.get_task(task_id)
            if not existing:
                raise ValueError("Task not found")
            
            # Query task comments
            cursor = self.db.task_comments.find(
                {"task_id": task_id},
                skip=offset,
                limit=limit
            ).sort("created_at", -1)  # Newest first
            
            # Convert to list of TaskComment objects
            comments = []
            async for doc in cursor:
                comments.append(TaskComment(**doc))
            
            # Count total comments
            total = await self.db.task_comments.count_documents({"task_id": task_id})
            
            return comments, total
            
        except Exception as e:
            logger.error(f"Error getting task comments {task_id}: {e}")
            raise
    
    async def add_task_comment(self, task_id: str, comment_id: str, user_id: str, content: str) -> TaskComment:
        """Add a comment to a task."""
        try:
            # Get existing task
            existing = await self.get_task(task_id)
            if not existing:
                raise ValueError("Task not found")
            
            # Create comment
            now = datetime.utcnow()
            comment = TaskComment(
                id=comment_id,
                task_id=task_id,
                user_id=user_id,
                content=content,
                created_at=now
            )
            
            # Insert into database
            await self.db.task_comments.insert_one(comment.dict())
            
            # Return the created comment
            return comment
            
        except Exception as e:
            logger.error(f"Error adding task comment {task_id}: {e}")
            raise


# Singleton instance
task_service = TaskService()