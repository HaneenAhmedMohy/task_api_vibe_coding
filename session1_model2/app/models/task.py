from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.models.database import Base
from app.models.enums import TaskStatus, TaskPriority

class Task(Base):
    """
    Task model for the task management system.

    Attributes:
        id: Primary key for the task.
        title: The title of the task (required, max 200 chars).
        description: Optional detailed description of the task.
        status: Current status of the task (pending/in-progress/completed).
        priority: Priority level of the task (low/medium/high).
        created_at: Timestamp when the task was created.
        updated_at: Timestamp when the task was last updated.
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, comment="Unique identifier for the task")
    title = Column(String(200), nullable=False, index=True, comment="Title of the task")
    description = Column(Text, nullable=True, comment="Detailed description of the task")
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        comment="Current status of the task"
    )
    priority = Column(
        Enum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False,
        comment="Priority level of the task"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when task was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
        comment="Timestamp when task was last updated"
    )

    def __repr__(self) -> str:
        return (
            f"<Task(id={self.id}, title='{self.title}', "
            f"status='{self.status.value}', priority='{self.priority.value}')>"
        )

    @property
    def is_completed(self) -> bool:
        """Check if the task is completed."""
        return self.status == TaskStatus.COMPLETED

    @property
    def is_active(self) -> bool:
        """Check if the task is active (pending or in-progress)."""
        return self.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]