from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on-hold"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, max_length=5000, description="Task description")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Task status")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    assigned_to: Optional[str] = Field(None, max_length=100, description="Task assignee")
    estimated_hours: Optional[int] = Field(None, ge=0, le=10000, description="Estimated hours to complete")
    tags: Optional[List[str]] = Field(None, description="List of tags")
    dependency_ids: Optional[List[int]] = Field(None, description="List of dependency task IDs")

    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @validator('assigned_to')
    def validate_assigned_to(cls, v):
        if v and not v.strip():
            return None
        return v.strip() if v else v

    @validator('tags')
    def validate_tags(cls, v):
        if v is None:
            return []
        unique_tags = list(set(tag.strip() for tag in v if tag.strip()))
        if len(unique_tags) > 20:
            raise ValueError('Maximum 20 unique tags allowed')
        return unique_tags

    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "title": "Complete project documentation",
                "description": "Write comprehensive documentation for the API",
                "status": "pending",
                "priority": "high",
                "due_date": "2024-12-31T23:59:59Z",
                "assigned_to": "john.doe@example.com",
                "estimated_hours": 40,
                "tags": ["documentation", "api", "urgent"],
                "dependency_ids": [1, 2, 3]
            }
        }


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, max_length=5000, description="Task description")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    priority: Optional[TaskPriority] = Field(None, description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    assigned_to: Optional[str] = Field(None, max_length=100, description="Task assignee")
    estimated_hours: Optional[int] = Field(None, ge=0, le=10000, description="Estimated hours to complete")
    actual_hours: Optional[int] = Field(None, ge=0, le=10000, description="Actual hours spent")
    tags: Optional[List[str]] = Field(None, description="List of tags")

    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip() if v else v

    @validator('assigned_to')
    def validate_assigned_to(cls, v):
        if v is not None and not v.strip():
            return None
        return v.strip() if v else v

    @validator('tags')
    def validate_tags(cls, v):
        if v is None:
            return None
        unique_tags = list(set(tag.strip() for tag in v if tag.strip()))
        if len(unique_tags) > 20:
            raise ValueError('Maximum 20 unique tags allowed')
        return unique_tags

    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "title": "Updated project documentation",
                "status": "in-progress",
                "priority": "medium",
                "actual_hours": 15,
                "tags": ["documentation", "api"]
            }
        }


class TaskDependency(BaseModel):
    id: int = Field(..., description="Dependency task ID")
    title: str = Field(..., description="Dependency task title")
    status: TaskStatus = Field(..., description="Dependency task status")

    class Config:
        from_attributes = True
        use_enum_values = True


class TaskResponse(BaseModel):
    id: int = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: TaskStatus = Field(..., description="Task status")
    priority: TaskPriority = Field(..., description="Task priority")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Task last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    assigned_to: Optional[str] = Field(None, description="Task assignee")
    estimated_hours: Optional[int] = Field(None, description="Estimated hours to complete")
    actual_hours: Optional[int] = Field(None, description="Actual hours spent")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    progress_percentage: float = Field(..., description="Progress percentage")
    is_ready_to_start: bool = Field(..., description="Whether task can be started")
    dependencies: List[TaskDependency] = Field(default_factory=list, description="Task dependencies")

    class Config:
        from_attributes = True
        use_enum_values = True
        schema_extra = {
            "example": {
                "id": 1,
                "title": "Complete project documentation",
                "description": "Write comprehensive documentation for the API",
                "status": "in-progress",
                "priority": "high",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-16T14:20:00Z",
                "completed_at": None,
                "due_date": "2024-12-31T23:59:59Z",
                "assigned_to": "john.doe@example.com",
                "estimated_hours": 40,
                "actual_hours": 15,
                "tags": ["documentation", "api", "urgent"],
                "progress_percentage": 50.0,
                "is_ready_to_start": True,
                "dependencies": []
            }
        }


class BulkTaskUpdate(BaseModel):
    task_ids: List[int] = Field(..., min_items=1, max_items=100, description="List of task IDs to update")
    updates: TaskUpdate = Field(..., description="Updates to apply to all tasks")

    class Config:
        schema_extra = {
            "example": {
                "task_ids": [1, 2, 3],
                "updates": {
                    "status": "in-progress",
                    "priority": "high"
                }
            }
        }


class TaskStatusTransition(BaseModel):
    task_id: int = Field(..., description="Task ID")
    current_status: TaskStatus = Field(..., description="Current status")
    new_status: TaskStatus = Field(..., description="New status")
    is_allowed: bool = Field(..., description="Whether transition is allowed")
    reason: Optional[str] = Field(None, description="Reason if transition is not allowed")

    class Config:
        use_enum_values = True


class TaskStatistics(BaseModel):
    total_tasks: int = Field(..., description="Total number of tasks")
    pending_tasks: int = Field(..., description="Number of pending tasks")
    in_progress_tasks: int = Field(..., description="Number of in-progress tasks")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    cancelled_tasks: int = Field(..., description="Number of cancelled tasks")
    on_hold_tasks: int = Field(..., description="Number of on-hold tasks")
    overdue_tasks: int = Field(..., description="Number of overdue tasks")
    tasks_by_priority: dict = Field(..., description="Tasks grouped by priority")
    average_completion_time: Optional[float] = Field(None, description="Average completion time in hours")

    class Config:
        schema_extra = {
            "example": {
                "total_tasks": 100,
                "pending_tasks": 30,
                "in_progress_tasks": 15,
                "completed_tasks": 45,
                "cancelled_tasks": 5,
                "on_hold_tasks": 5,
                "overdue_tasks": 8,
                "tasks_by_priority": {"low": 20, "medium": 50, "high": 25, "critical": 5},
                "average_completion_time": 38.5
            }
        }