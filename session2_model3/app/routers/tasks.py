from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.task import Task, TaskStatus as TaskStatusEnum, TaskPriority as TaskPriorityEnum
from ..schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskStatus, TaskPriority

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    db_task = Task(
        title=task.title,
        description=task.description,
        status=TaskStatusEnum(task.status),
        priority=TaskPriorityEnum(task.priority)
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/", response_model=List[TaskResponse])
def get_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search tasks by title or description"),
    skip: Optional[int] = Query(0, ge=0, description="Number of tasks to skip"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    db: Session = Depends(get_db)
):
    """Get all tasks with optional filtering, searching, and pagination"""
    query = db.query(Task)

    if status:
        query = query.filter(Task.status == TaskStatusEnum(status))

    if priority:
        query = query.filter(Task.priority == TaskPriorityEnum(priority))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Task.title.ilike(search_term)) |
            (Task.description.ilike(search_term))
        )

    tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
    return tasks


@router.get("/count", response_model=dict)
def get_task_count(db: Session = Depends(get_db)):
    """Get total count of tasks"""
    total = db.query(Task).count()
    return {"total": total}


@router.get("/status/list", response_model=dict)
def get_status_list():
    """Get list of available task statuses"""
    return {
        "statuses": [status.value for status in TaskStatusEnum]
    }


@router.get("/priority/list", response_model=dict)
def get_priority_list():
    """Get list of available task priorities"""
    return {
        "priorities": [priority.value for priority in TaskPriorityEnum]
    }


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific task by ID"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )

    # Update only provided fields
    update_data = task_update.model_dump(exclude_unset=True)

    if 'status' in update_data:
        update_data['status'] = TaskStatusEnum(update_data['status'])

    if 'priority' in update_data:
        update_data['priority'] = TaskPriorityEnum(update_data['priority'])

    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)
    return db_task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a specific task by ID"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )

    db.delete(db_task)
    db.commit()
    return None