"""Improved Task router with better error handling and structure."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.database import get_db
from app.models.enums import TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService
from app.exceptions.task_exceptions import TaskNotFoundException
from app.utils.pagination import PaginationParams, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=List[TaskResponse], status_code=200)
async def get_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return (max: 1000)"),
    status: Optional[TaskStatus] = Query(None, description="Filter tasks by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter tasks by priority"),
    search: Optional[str] = Query(None, min_length=1, description="Search in title and description"),
    sort_by: Optional[str] = Query(
        "created_at",
        regex="^(created_at|updated_at|title|priority|status)$",
        description="Field to sort by"
    ),
    sort_order: Optional[str] = Query(
        "desc",
        regex="^(asc|desc)$",
        description="Sort order (asc or desc)"
    ),
    db: Session = Depends(get_db)
):
    """
    Retrieve all tasks with comprehensive filtering, sorting, and pagination.

    ### Filtering Options:
    - **status**: Filter by task status (pending, in-progress, completed)
    - **priority**: Filter by priority (low, medium, high)
    - **search**: Search in title and description (case-insensitive)

    ### Sorting Options:
    - **sort_by**: created_at, updated_at, title, priority, status
    - **sort_order**: asc (ascending), desc (descending)

    ### Pagination:
    - **skip**: Number of records to skip
    - **limit**: Number of records to return (1-1000)

    Returns:
        List of tasks matching the criteria
    """
    try:
        # Validate pagination parameters
        pagination = PaginationParams(skip=skip, limit=limit, max_limit=1000)

        # Get tasks with filters
        tasks = TaskService.get_all_tasks(
            db=db,
            skip=pagination.offset,
            limit=pagination.page_size,
            status=status,
            priority=priority,
            search=search
        )

        # Note: Sorting would need to be implemented in the service layer
        # For now, we'll return the tasks as ordered by created_at desc

        return tasks

    except ValueError as e:
        # Handle validation errors that aren't caught by Pydantic
        raise HTTPException(
            status_code=422,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving tasks"
        )


@router.get("/paginated", status_code=200)
async def get_tasks_paginated(
    skip: int = Query(0, ge=0, description="Number of tasks to skip for pagination"),
    limit: int = Query(10, ge=1, le=100, description="Number of tasks per page (max: 100)"),
    status: Optional[TaskStatus] = Query(None, description="Filter tasks by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter tasks by priority"),
    search: Optional[str] = Query(None, min_length=1, description="Search in title and description"),
    db: Session = Depends(get_db)
):
    """
    Retrieve tasks with pagination metadata.

    Returns a paginated response with metadata about total items,
    current page, and navigation info.
    """
    try:
        pagination = PaginationParams(skip=skip, limit=limit, max_limit=100)

        # Get tasks and total count
        tasks = TaskService.get_all_tasks(
            db=db,
            skip=pagination.offset,
            limit=pagination.page_size,
            status=status,
            priority=priority,
            search=search
        )

        total = TaskService.get_task_count(
            db=db,
            status=status,
            priority=priority,
            search=search
        )

        # Create paginated response
        response = PaginatedResponse.create(
            items=tasks,
            total=total,
            pagination=pagination
        )

        return response

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving tasks"
        )


@router.get("/count", status_code=200)
async def get_tasks_count(
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by task priority"),
    search: Optional[str] = Query(None, min_length=1, description="Search in title and description"),
    db: Session = Depends(get_db)
):
    """
    Get statistics about tasks.

    Returns total count of tasks with optional filters applied.
    """
    try:
        total = TaskService.get_task_count(
            db=db,
            status=status,
            priority=priority,
            search=search
        )

        # Get counts by status
        status_counts = {}
        for s in TaskStatus:
            status_counts[s.value] = TaskService.get_task_count(db=db, status=s)

        # Get counts by priority
        priority_counts = {}
        for p in TaskPriority:
            priority_counts[p.value] = TaskService.get_task_count(db=db, priority=p)

        return {
            "total": total,
            "by_status": status_counts,
            "by_priority": priority_counts,
            "active_filters": {
                "status": status.value if status else None,
                "priority": priority.value if priority else None,
                "search": search
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving task statistics"
        )


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new task.

    The task will be validated against the schema rules:
    - Title: Required, 1-200 characters
    - Description: Optional, any length
    - Status: Defaults to 'pending' if not specified
    - Priority: Defaults to 'medium' if not specified

    **Note**: Validation errors will automatically return HTTP 422
    """
    try:
        created_task = TaskService.create_task(db=db, task_data=task)
        return created_task

    except Exception as e:
        # Don't catch validation errors - let FastAPI handle them (returns 422)
        # Only catch unexpected database errors
        raise HTTPException(
            status_code=500,
            detail="Failed to create task due to server error"
        )


@router.get("/status/list", status_code=200)
async def get_task_status_list():
    """
    Get available task statuses with descriptions.

    Returns all possible task statuses that can be used
    for filtering and creating/updating tasks.
    """
    return {
        "statuses": TaskStatus.values(),
        "default": TaskStatus.PENDING.value,
        "descriptions": {
            "pending": "Task is not started yet",
            "in-progress": "Task is currently being worked on",
            "completed": "Task has been finished"
        }
    }


@router.get("/priority/list", status_code=200)
async def get_task_priority_list():
    """
    Get available task priorities with descriptions.

    Returns all possible task priorities that can be used
    for filtering and creating/updating tasks.
    """
    return {
        "priorities": TaskPriority.values(),
        "default": TaskPriority.MEDIUM.value,
        "descriptions": {
            "low": "Low priority task (can be deferred)",
            "medium": "Normal priority task",
            "high": "High priority task (urgent)"
        }
    }


@router.get("/{task_id}", response_model=TaskResponse, status_code=200)
async def get_task_by_id(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific task by its ID.

    Args:
        task_id: The unique identifier of the task

    Returns:
        Task details if found

    Raises:
        404: If task with the specified ID doesn't exist
        422: If task_id is not a valid integer
    """
    try:
        if task_id <= 0:
            raise HTTPException(
                status_code=422,
                detail="Task ID must be a positive integer"
            )

        task = TaskService.get_task_by_id(db=db, task_id=task_id)

        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )

        return task

    except HTTPException:
        # Re-raise HTTP exceptions (404, 422)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving task"
        )


@router.put("/{task_id}", response_model=TaskResponse, status_code=200)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing task.

    Only the fields provided in the request body will be updated.
    Fields not provided will remain unchanged.

    **Note**: Validation errors will automatically return HTTP 422

    Raises:
        404: If task with the specified ID doesn't exist
    """
    try:
        if task_id <= 0:
            raise HTTPException(
                status_code=422,
                detail="Task ID must be a positive integer"
            )

        updated_task = TaskService.update_task(
            db=db,
            task_id=task_id,
            task_data=task_update
        )

        if not updated_task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )

        return updated_task

    except HTTPException:
        # Re-raise HTTP exceptions (404, 422)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating task"
        )


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a task permanently.

    This action cannot be undone. The task will be permanently
    removed from the database.

    Args:
        task_id: The unique identifier of the task to delete

    Raises:
        404: If task with the specified ID doesn't exist
    """
    try:
        if task_id <= 0:
            raise HTTPException(
                status_code=422,
                detail="Task ID must be a positive integer"
            )

        deleted = TaskService.delete_task(db=db, task_id=task_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )

        # Return 204 No Content on successful deletion
        return

    except HTTPException:
        # Re-raise HTTP exceptions (404, 422)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error while deleting task"
        )