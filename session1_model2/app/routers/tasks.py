from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db
from app.models.enums import TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService
from app.exceptions.task_exceptions import TaskNotFoundException, DatabaseOperationException

router = APIRouter()


@router.get("/", response_model=List[TaskResponse], status_code=200)
async def get_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by task priority"),
    search: Optional[str] = Query(None, min_length=1, description="Search in title and description"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all tasks with optional filtering and pagination.

    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)
        status: Filter tasks by status
        priority: Filter tasks by priority
        search: Search term for title and description
        db: Database session

    Returns:
        List of tasks matching the criteria
    """
    try:
        tasks = TaskService.get_all_tasks(
            db=db,
            skip=skip,
            limit=limit,
            status=status,
            priority=priority,
            search=search
        )
        return tasks
    except Exception as e:
        raise DatabaseOperationException(str(e))


@router.get("/count", status_code=200)
async def get_tasks_count(
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by task priority"),
    search: Optional[str] = Query(None, min_length=1, description="Search in title and description"),
    db: Session = Depends(get_db)
):
    """
    Get the total count of tasks matching the filters.

    Args:
        status: Filter tasks by status
        priority: Filter tasks by priority
        search: Search term for title and description
        db: Database session

    Returns:
        Dictionary with total count
    """
    try:
        total = TaskService.get_task_count(
            db=db,
            status=status,
            priority=priority,
            search=search
        )
        return {"total": total}
    except Exception as e:
        raise DatabaseOperationException(str(e))


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new task.

    Args:
        task: Task creation data
        db: Database session

    Returns:
        Created task data
    """
    try:
        created_task = TaskService.create_task(db=db, task_data=task)
        return created_task
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("/status/list", status_code=200)
async def get_task_status_list():
    """
    Get the list of available task statuses.

    Returns:
        List of available task statuses
    """
    return {
        "statuses": TaskStatus.values(),
        "description": {
            "pending": "Task is not started",
            "in-progress": "Task is currently being worked on",
            "completed": "Task is finished"
        }
    }


@router.get("/priority/list", status_code=200)
async def get_task_priority_list():
    """
    Get the list of available task priorities.

    Returns:
        List of available task priorities
    """
    return {
        "priorities": TaskPriority.values(),
        "description": {
            "low": "Low priority task",
            "medium": "Medium priority task",
            "high": "High priority task"
        }
    }


@router.get("/{task_id}", response_model=TaskResponse, status_code=200)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific task by ID.

    Args:
        task_id: ID of the task to retrieve
        db: Database session

    Returns:
        Task data

    Raises:
        HTTPException: If task is not found
    """
    try:
        task = TaskService.get_task_by_id(db=db, task_id=task_id)
        if not task:
            raise TaskNotFoundException(task_id)
        return task
    except TaskNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise DatabaseOperationException(str(e))


@router.put("/{task_id}", response_model=TaskResponse, status_code=200)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing task.

    Args:
        task_id: ID of the task to update
        task_update: Task update data
        db: Database session

    Returns:
        Updated task data

    Raises:
        HTTPException: If task is not found or update fails
    """
    try:
        updated_task = TaskService.update_task(
            db=db,
            task_id=task_id,
            task_data=task_update
        )
        if not updated_task:
            raise TaskNotFoundException(task_id)
        return updated_task
    except TaskNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update task: {str(e)}"
        )


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a task.

    Args:
        task_id: ID of the task to delete
        db: Database session

    Raises:
        HTTPException: If task is not found
    """
    try:
        deleted = TaskService.delete_task(db=db, task_id=task_id)
        if not deleted:
            raise TaskNotFoundException(task_id)
        # No content to return for successful deletion
        return
    except TaskNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise DatabaseOperationException(str(e))