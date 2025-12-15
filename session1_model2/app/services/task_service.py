"""Service layer for Task operations."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """Service class for handling Task CRUD operations."""

    @staticmethod
    def get_all_tasks(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        search: Optional[str] = None
    ) -> List[Task]:
        """
        Get all tasks with optional filtering.

        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            status: Filter by task status
            priority: Filter by task priority
            search: Search in title and description

        Returns:
            List of tasks matching the criteria
        """
        query = db.query(Task)

        # Apply filters
        if status is not None:
            query = query.filter(Task.status == status)

        if priority is not None:
            query = query.filter(Task.priority == priority)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Task.title.ilike(search_pattern),
                    Task.description.ilike(search_pattern)
                )
            )

        # Apply pagination and ordering
        tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
        return tasks

    @staticmethod
    def get_task_by_id(db: Session, task_id: int) -> Optional[Task]:
        """
        Get a single task by ID.

        Args:
            db: Database session
            task_id: ID of the task to retrieve

        Returns:
            Task object if found, None otherwise
        """
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def create_task(db: Session, task_data: TaskCreate) -> Task:
        """
        Create a new task.

        Args:
            db: Database session
            task_data: Task creation data

        Returns:
            Created task object
        """
        db_task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task

    @staticmethod
    def update_task(db: Session, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """
        Update an existing task.

        Args:
            db: Database session
            task_id: ID of the task to update
            task_data: Task update data

        Returns:
            Updated task object if found and updated, None otherwise
        """
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            return None

        # Update fields only if they are provided in the update data
        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_task, field, value)

        db.commit()
        db.refresh(db_task)
        return db_task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """
        Delete a task.

        Args:
            db: Database session
            task_id: ID of the task to delete

        Returns:
            True if task was deleted, False if task was not found
        """
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            return False

        db.delete(db_task)
        db.commit()
        return True

    @staticmethod
    def get_task_count(
        db: Session,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        search: Optional[str] = None
    ) -> int:
        """
        Get the total count of tasks matching the filters.

        Args:
            db: Database session
            status: Filter by task status
            priority: Filter by task priority
            search: Search in title and description

        Returns:
            Total count of tasks matching the criteria
        """
        query = db.query(Task)

        if status is not None:
            query = query.filter(Task.status == status)

        if priority is not None:
            query = query.filter(Task.priority == priority)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Task.title.ilike(search_pattern),
                    Task.description.ilike(search_pattern)
                )
            )

        return query.count()