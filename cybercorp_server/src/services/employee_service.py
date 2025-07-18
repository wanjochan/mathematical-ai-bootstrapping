"""Employee service module for CyberCorp Server."""

from typing import Dict, Any, List, Optional, Tuple
from uuid import uuid4
from datetime import datetime

from ..models.employees import (
    Employee, EmployeeCreate, EmployeeUpdate, EmployeeStatus,
    EmployeeQuery, EmployeePerformanceMetrics
)
from ..models.tasks import Task
from ..database import get_db_connection
from ..logging_config import get_logger

logger = get_logger(__name__)


class EmployeeService:
    """Service for employee management operations."""
    
    def __init__(self):
        """Initialize the employee service."""
        self.db = None
    
    async def initialize(self):
        """Initialize the service with database connection."""
        self.db = await get_db_connection()
        logger.info("Employee service initialized")
    
    async def shutdown(self):
        """Shutdown the service."""
        logger.info("Employee service shutting down")
    
    async def list_employees(self, query: EmployeeQuery) -> List[Employee]:
        """List employees based on query parameters."""
        try:
            # Build query
            filter_conditions = {}
            if query.type is not None:
                filter_conditions["type"] = query.type
            if query.status is not None:
                filter_conditions["status"] = query.status
            if query.skill is not None:
                filter_conditions["skills"] = {"$in": [query.skill]}
            if query.name_contains is not None:
                filter_conditions["name"] = {"$regex": query.name_contains, "$options": "i"}
            
            # Execute query
            cursor = self.db.employees.find(
                filter_conditions,
                skip=query.offset,
                limit=query.limit
            ).sort("created_at", -1)  # Newest first
            
            # Convert to list of Employee objects
            employees = []
            async for doc in cursor:
                employees.append(Employee(**doc))
            
            return employees
            
        except Exception as e:
            logger.error(f"Error listing employees: {e}")
            raise
    
    async def count_employees(self, query: EmployeeQuery) -> int:
        """Count employees based on query parameters."""
        try:
            # Build query
            filter_conditions = {}
            if query.type is not None:
                filter_conditions["type"] = query.type
            if query.status is not None:
                filter_conditions["status"] = query.status
            if query.skill is not None:
                filter_conditions["skills"] = {"$in": [query.skill]}
            if query.name_contains is not None:
                filter_conditions["name"] = {"$regex": query.name_contains, "$options": "i"}
            
            # Count documents
            count = await self.db.employees.count_documents(filter_conditions)
            return count
            
        except Exception as e:
            logger.error(f"Error counting employees: {e}")
            raise
    
    async def get_employee(self, employee_id: str) -> Optional[Employee]:
        """Get employee by ID."""
        try:
            doc = await self.db.employees.find_one({"id": employee_id})
            if doc:
                return Employee(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting employee {employee_id}: {e}")
            raise
    
    async def create_employee(self, employee: Employee) -> Employee:
        """Create a new employee."""
        try:
            # Set created_at and updated_at
            now = datetime.utcnow()
            employee_dict = employee.dict()
            employee_dict["created_at"] = now
            employee_dict["updated_at"] = now
            
            # Insert into database
            await self.db.employees.insert_one(employee_dict)
            
            # Return the created employee
            return Employee(**employee_dict)
            
        except Exception as e:
            logger.error(f"Error creating employee: {e}")
            raise
    
    async def update_employee(self, employee_id: str, employee_update: EmployeeUpdate) -> Optional[Employee]:
        """Update an employee."""
        try:
            # Get existing employee
            existing = await self.get_employee(employee_id)
            if not existing:
                return None
            
            # Prepare update
            update_data = employee_update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            # Update in database
            await self.db.employees.update_one(
                {"id": employee_id},
                {"$set": update_data}
            )
            
            # Get and return updated employee
            return await self.get_employee(employee_id)
            
        except Exception as e:
            logger.error(f"Error updating employee {employee_id}: {e}")
            raise
    
    async def delete_employee(self, employee_id: str) -> bool:
        """Delete an employee."""
        try:
            # Delete from database
            result = await self.db.employees.delete_one({"id": employee_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting employee {employee_id}: {e}")
            raise
    
    async def update_employee_status(self, employee_id: str, status: EmployeeStatus, reason: Optional[str] = None) -> Optional[Employee]:
        """Update employee status."""
        try:
            # Get existing employee
            existing = await self.get_employee(employee_id)
            if not existing:
                return None
            
            # Prepare update
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            # Add status change history
            status_change = {
                "from": existing.status,
                "to": status,
                "timestamp": datetime.utcnow(),
                "reason": reason
            }
            
            # Update in database
            await self.db.employees.update_one(
                {"id": employee_id},
                {
                    "$set": update_data,
                    "$push": {"status_history": status_change}
                }
            )
            
            # Get and return updated employee
            return await self.get_employee(employee_id)
            
        except Exception as e:
            logger.error(f"Error updating employee status {employee_id}: {e}")
            raise
    
    async def get_employee_tasks(self, employee_id: str, limit: int = 100, offset: int = 0) -> Tuple[List[Task], int]:
        """Get tasks assigned to an employee."""
        try:
            # Query tasks
            cursor = self.db.tasks.find(
                {"assigned_to": employee_id},
                skip=offset,
                limit=limit
            ).sort("created_at", -1)  # Newest first
            
            # Convert to list of Task objects
            tasks = []
            async for doc in cursor:
                tasks.append(Task(**doc))
            
            # Count total tasks
            total = await self.db.tasks.count_documents({"assigned_to": employee_id})
            
            return tasks, total
            
        except Exception as e:
            logger.error(f"Error getting employee tasks {employee_id}: {e}")
            raise
    
    async def get_employee_performance(self, employee_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> EmployeePerformanceMetrics:
        """Get employee performance metrics."""
        try:
            # Default date range to last 30 days if not specified
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date.replace(day=end_date.day - 30)
            
            # Query completed tasks
            completed_tasks_cursor = self.db.tasks.find({
                "assigned_to": employee_id,
                "status": "COMPLETED",
                "completed_at": {"$gte": start_date, "$lte": end_date}
            })
            
            # Calculate metrics
            completed_tasks = []
            total_time_spent = 0
            async for doc in completed_tasks_cursor:
                task = Task(**doc)
                completed_tasks.append(task)
                if task.started_at and task.completed_at:
                    time_spent = (task.completed_at - task.started_at).total_seconds() / 3600  # hours
                    total_time_spent += time_spent
            
            # Count tasks by status
            pending_count = await self.db.tasks.count_documents({
                "assigned_to": employee_id,
                "status": "PENDING"
            })
            
            in_progress_count = await self.db.tasks.count_documents({
                "assigned_to": employee_id,
                "status": "IN_PROGRESS"
            })
            
            completed_count = len(completed_tasks)
            
            failed_count = await self.db.tasks.count_documents({
                "assigned_to": employee_id,
                "status": "FAILED",
                "completed_at": {"$gte": start_date, "$lte": end_date}
            })
            
            # Calculate average completion time
            avg_completion_time = 0
            if completed_count > 0:
                avg_completion_time = total_time_spent / completed_count
            
            # Create performance metrics
            metrics = EmployeePerformanceMetrics(
                employee_id=employee_id,
                period_start=start_date,
                period_end=end_date,
                tasks_completed=completed_count,
                tasks_pending=pending_count,
                tasks_in_progress=in_progress_count,
                tasks_failed=failed_count,
                avg_completion_time=avg_completion_time,
                total_time_spent=total_time_spent
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting employee performance {employee_id}: {e}")
            raise


# Singleton instance
employee_service = EmployeeService()