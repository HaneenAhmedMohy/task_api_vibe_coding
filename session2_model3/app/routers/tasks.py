from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ..models.task import (
    Task, TaskStatus as TaskStatusEnum, TaskPriority as TaskPriorityEnum,
    task_dependencies
)
from ..schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskStatus, TaskPriority,
    BulkTaskUpdate, TaskStatusTransition, TaskStatistics, TaskDependency
)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)


def _convert_task_to_response(task: Task, db: Session) -> TaskResponse:
    """Helper function to convert Task model to TaskResponse"""
    dependencies = [
        TaskDependency(
            id=dep.id,
            title=dep.title,
            status=TaskStatus(dep.status.value)
        )
        for dep in task.dependencies
    ]

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=TaskStatus(task.status.value),
        priority=TaskPriority(task.priority.value),
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        due_date=task.due_date,
        assigned_to=task.assigned_to,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        tags=task.tags_list,
        progress_percentage=task.get_progress_percentage(),
        is_ready_to_start=task.is_ready_to_start(),
        dependencies=dependencies
    )


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task with optional dependencies"""
    try:
        # Validate dependencies exist
        if task.dependency_ids:
            existing_deps = db.query(Task).filter(Task.id.in_(task.dependency_ids)).all()
            if len(existing_deps) != len(task.dependency_ids):
                raise HTTPException(
                    status_code=400,
                    detail="One or more dependency tasks not found"
                )

        db_task = Task(
            title=task.title,
            description=task.description,
            status=TaskStatusEnum(task.status),
            priority=TaskPriorityEnum(task.priority),
            due_date=task.due_date,
            assigned_to=task.assigned_to,
            estimated_hours=task.estimated_hours,
            tags_list=task.tags or []
        )

        db.add(db_task)
        db.flush()  # Get the ID without committing

        # Add dependencies
        if task.dependency_ids:
            for dep_id in task.dependency_ids:
                db.execute(
                    task_dependencies.insert().values(
                        parent_id=db_task.id,
                        child_id=dep_id
                    )
                )

        db.commit()
        db.refresh(db_task)
        return _convert_task_to_response(db_task, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[TaskResponse])
def get_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    search: Optional[str] = Query(None, description="Search tasks by title or description"),
    due_soon: Optional[bool] = Query(False, description="Filter tasks due within 7 days"),
    overdue: Optional[bool] = Query(False, description="Filter overdue tasks"),
    skip: Optional[int] = Query(0, ge=0, description="Number of tasks to skip"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_desc: Optional[bool] = Query(True, description="Sort descending"),
    db: Session = Depends(get_db)
):
    """Get all tasks with comprehensive filtering, searching, and sorting"""
    try:
        query = db.query(Task).options(joinedload(Task.dependencies))

        # Apply filters
        if status:
            query = query.filter(Task.status == TaskStatusEnum(status))

        if priority:
            query = query.filter(Task.priority == TaskPriorityEnum(priority))

        if assigned_to:
            query = query.filter(Task.assigned_to.ilike(f"%{assigned_to}%"))

        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            for tag in tag_list:
                query = query.filter(Task.tags.ilike(f"%{tag}%"))

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Task.title.ilike(search_term)) |
                (Task.description.ilike(search_term)) |
                (Task.assigned_to.ilike(search_term))
            )

        if due_soon:
            seven_days_from_now = datetime.utcnow() + timedelta(days=7)
            query = query.filter(
                and_(
                    Task.due_date <= seven_days_from_now,
                    Task.due_date >= datetime.utcnow(),
                    Task.status.in_([TaskStatusEnum.PENDING, TaskStatusEnum.IN_PROGRESS])
                )
            )

        if overdue:
            query = query.filter(
                and_(
                    Task.due_date < datetime.utcnow(),
                    Task.status.in_([TaskStatusEnum.PENDING, TaskStatusEnum.IN_PROGRESS])
                )
            )

        # Apply sorting
        sort_column = getattr(Task, sort_by, Task.created_at)
        if sort_desc:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        # Apply pagination
        tasks = query.offset(skip).limit(limit).all()

        return [_convert_task_to_response(task, db) for task in tasks]

    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics", response_model=TaskStatistics)
def get_task_statistics(db: Session = Depends(get_db)):
    """Get comprehensive task statistics"""
    try:
        now = datetime.utcnow()

        # Basic counts by status
        status_counts = db.query(
            Task.status, func.count(Task.id)
        ).group_by(Task.status).all()

        counts = {status.value: count for status, count in status_counts}

        # Priority distribution
        priority_counts = db.query(
            Task.priority, func.count(Task.id)
        ).group_by(Task.priority).all()

        priority_dist = {priority.value: count for priority, count in priority_counts}

        # Overdue tasks
        overdue_count = db.query(Task).filter(
            and_(
                Task.due_date < now,
                Task.status.in_([TaskStatusEnum.PENDING, TaskStatusEnum.IN_PROGRESS])
            )
        ).count()

        # Average completion time for completed tasks
        completed_tasks = db.query(Task).filter(
            and_(
                Task.status == TaskStatusEnum.COMPLETED,
                Task.completed_at.isnot(None)
            )
        ).all()

        avg_completion_time = None
        if completed_tasks:
            total_time = sum(
                (task.completed_at - task.created_at).total_seconds() / 3600
                for task in completed_tasks
            )
            avg_completion_time = total_time / len(completed_tasks)

        return TaskStatistics(
            total_tasks=sum(counts.values()),
            pending_tasks=counts.get(TaskStatusEnum.PENDING.value, 0),
            in_progress_tasks=counts.get(TaskStatusEnum.IN_PROGRESS.value, 0),
            completed_tasks=counts.get(TaskStatusEnum.COMPLETED.value, 0),
            cancelled_tasks=counts.get(TaskStatusEnum.CANCELLED.value, 0),
            on_hold_tasks=counts.get(TaskStatusEnum.ON_HOLD.value, 0),
            overdue_tasks=overdue_count,
            tasks_by_priority=priority_dist,
            average_completion_time=avg_completion_time
        )

    except Exception as e:
        logger.error(f"Error fetching statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bulk-update", response_model=List[TaskResponse])
def bulk_update_tasks(
    bulk_update: BulkTaskUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update multiple tasks at once"""
    try:
        tasks = db.query(Task).filter(Task.id.in_(bulk_update.task_ids)).all()

        if len(tasks) != len(bulk_update.task_ids):
            found_ids = [task.id for task in tasks]
            missing_ids = set(bulk_update.task_ids) - set(found_ids)
            raise HTTPException(
                status_code=404,
                detail=f"Tasks with IDs {missing_ids} not found"
            )

        update_data = bulk_update.updates.model_dump(exclude_unset=True)

        # Convert enums
        if 'status' in update_data:
            update_data['status'] = TaskStatusEnum(update_data['status'])
        if 'priority' in update_data:
            update_data['priority'] = TaskPriorityEnum(update_data['priority'])

        # Handle special status transition logic
        if 'status' in update_data:
            new_status = update_data['status']
            for task in tasks:
                if not task.can_transition_to(new_status):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Task {task.id} cannot transition from {task.status.value} to {new_status.value}"
                    )

        # Apply updates
        for task in tasks:
            for field, value in update_data.items():
                setattr(task, field, value)

            # Set completed_at when status changes to completed
            if 'status' in update_data and update_data['status'] == TaskStatusEnum.COMPLETED:
                task.completed_at = datetime.utcnow()

        db.commit()

        # Return updated tasks
        return [_convert_task_to_response(task, db) for task in tasks]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{task_id}/status-transition", response_model=TaskStatusTransition)
def check_status_transition(
    task_id: int,
    new_status: TaskStatus,
    db: Session = Depends(get_db)
):
    """Check if a status transition is allowed for a task"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )

        target_status = TaskStatusEnum(new_status)
        current_status = task.status

        is_allowed = task.can_transition_to(target_status)
        reason = None

        if not is_allowed:
            allowed_transitions = task.get_allowed_transitions().get(current_status, set())
            allowed_str = ", ".join(t.value for t in allowed_transitions)
            reason = f"Cannot transition from {current_status.value} to {target_status.value}. Allowed: {allowed_str}"

        return TaskStatusTransition(
            task_id=task_id,
            current_status=TaskStatus(current_status.value),
            new_status=new_status,
            is_allowed=is_allowed,
            reason=reason
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking status transition: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID with all details"""
    try:
        task = db.query(Task).options(joinedload(Task.dependencies)).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )
        return _convert_task_to_response(task, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific task by ID with validation"""
    try:
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )

        update_data = task_update.model_dump(exclude_unset=True)

        # Handle status transition validation
        if 'status' in update_data:
            new_status = TaskStatusEnum(update_data['status'])
            if not db_task.can_transition_to(new_status):
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot transition from {db_task.status.value} to {new_status.value}"
                )
            update_data['status'] = new_status

        if 'priority' in update_data:
            update_data['priority'] = TaskPriorityEnum(update_data['priority'])

        # Handle tags
        if 'tags' in update_data:
            db_task.tags_list = update_data.pop('tags')

        # Apply updates
        for field, value in update_data.items():
            setattr(db_task, field, value)

        # Auto-set completed_at when status changes to completed
        if 'status' in update_data and update_data['status'] == TaskStatusEnum.COMPLETED:
            db_task.completed_at = datetime.utcnow()
        elif 'status' in update_data and update_data['status'] != TaskStatusEnum.COMPLETED:
            db_task.completed_at = None

        db.commit()
        db.refresh(db_task)
        return _convert_task_to_response(db_task, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a specific task by ID"""
    try:
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )

        # Check if other tasks depend on this task
        dependent_tasks = db.query(Task).join(task_dependencies, task_dependencies.c.parent_id == Task.id).filter(
            task_dependencies.c.child_id == task_id
        ).count()

        if dependent_tasks > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete task {task_id} as {dependent_tasks} other tasks depend on it"
            )

        db.delete(db_task)
        db.commit()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/count", response_model=dict)
def get_task_count(db: Session = Depends(get_db)):
    """Get total count of tasks"""
    try:
        total = db.query(Task).count()
        return {"total": total}
    except Exception as e:
        logger.error(f"Error getting task count: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


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