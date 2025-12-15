from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Annotated
from app.models.enums import TaskStatus, TaskPriority
from app.schemas.base import create_enum_validator, ResponseModelMixin


class TaskBase(BaseModel):
    """Base schema for Task with common fields."""

    title: Annotated[
        str,
        Field(
            min_length=1,
            max_length=200,
            description="The title of the task (1-200 characters)",
            json_schema_extra={"example": "Complete project documentation"}
        )
    ]
    description: Annotated[
        Optional[str],
        Field(
            None,
            description="Detailed description of the task",
            json_schema_extra={"example": "Write comprehensive documentation for the new API endpoints"}
        )
    ]
    status: Annotated[
        TaskStatus,
        Field(
            TaskStatus.PENDING,
            description="Current status of the task",
            json_schema_extra={"example": TaskStatus.PENDING}
        )
    ]
    priority: Annotated[
        TaskPriority,
        Field(
            TaskPriority.MEDIUM,
            description="Priority level of the task",
            json_schema_extra={"example": TaskPriority.MEDIUM}
        )
    ]

    # Add validators using the factory function
    _validate_status = create_enum_validator(TaskStatus, "status")
    _validate_priority = create_enum_validator(TaskPriority, "priority")

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "title": "Complete project documentation",
                "description": "Write comprehensive documentation for the new API endpoints",
                "status": "pending",
                "priority": "medium"
            }
        }
    )


class TaskCreate(TaskBase):
    """Schema for creating a new task.

    Inherits all fields from TaskBase with their validation rules.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Complete project documentation",
                "description": "Write comprehensive documentation for the new API endpoints",
                "status": "pending",
                "priority": "high"
            }
        }
    )


class TaskUpdate(BaseModel):
    """Schema for updating an existing task.

    All fields are optional to allow partial updates.
    """

    title: Annotated[
        Optional[str],
        Field(
            None,
            min_length=1,
            max_length=200,
            description="Updated title of the task",
            json_schema_extra={"example": "Updated project documentation"}
        )
    ]
    description: Annotated[
        Optional[str],
        Field(
            None,
            description="Updated description of the task",
            json_schema_extra={"example": "Updated description with more details"}
        )
    ]
    status: Annotated[
        Optional[TaskStatus],
        Field(
            None,
            description="Updated status of the task",
            json_schema_extra={"example": TaskStatus.IN_PROGRESS}
        )
    ]
    priority: Annotated[
        Optional[TaskPriority],
        Field(
            None,
            description="Updated priority level of the task",
            json_schema_extra={"example": TaskPriority.HIGH}
        )
    ]

    # Add validators using the factory function
    _validate_status = create_enum_validator(TaskStatus, "status")
    _validate_priority = create_enum_validator(TaskPriority, "priority")

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "status": "in-progress",
                "priority": "high"
            }
        }
    )


class TaskResponse(TaskBase, ResponseModelMixin):
    """Schema for returning task data with system-generated fields."""

    id: Annotated[
        int,
        Field(
            ...,
            description="Unique identifier for the task",
            json_schema_extra={"example": 1}
        )
    ]
    created_at: Annotated[
        datetime,
        Field(
            ...,
            description="Timestamp when the task was created",
            json_schema_extra={"example": "2024-01-01T12:00:00Z"}
        )
    ]
    updated_at: Annotated[
        Optional[datetime],
        Field(
            None,
            description="Timestamp when the task was last updated",
            json_schema_extra={"example": "2024-01-01T13:00:00Z"}
        )
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Complete project documentation",
                "description": "Write comprehensive documentation for the new API endpoints",
                "status": "pending",
                "priority": "medium",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": None
            }
        }
    )