from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from typing import Dict, Set
from ..database import Base


class TaskStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on-hold"


class TaskPriority(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Association table for many-to-many relationship between tasks (dependencies)
task_dependencies = Table(
    'task_dependencies',
    Base.metadata,
    Column('parent_id', Integer, ForeignKey('tasks.id'), primary_key=True),
    Column('child_id', Integer, ForeignKey('tasks.id'), primary_key=True)
)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(String(100), nullable=True, index=True)
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags

    # Relationships
    dependencies = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin="Task.id == task_dependencies.c.parent_id",
        secondaryjoin="Task.id == task_dependencies.c.child_id",
        back_populates="dependents"
    )

    dependents = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin="Task.id == task_dependencies.c.child_id",
        secondaryjoin="Task.id == task_dependencies.c.parent_id",
        back_populates="dependencies"
    )

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status.value}', priority='{self.priority.value}')>"

    @property
    def tags_list(self) -> list:
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    @tags_list.setter
    def tags_list(self, tags: list):
        """Set tags from a list"""
        self.tags = ', '.join(tags) if tags else None

    def can_transition_to(self, new_status: TaskStatus) -> bool:
        """Check if status transition is allowed"""
        transitions = self.get_allowed_transitions()
        return new_status in transitions.get(self.status, set())

    def get_allowed_transitions(self) -> Dict[TaskStatus, Set[TaskStatus]]:
        """Get allowed status transitions"""
        return {
            TaskStatus.PENDING: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED, TaskStatus.ON_HOLD},
            TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.ON_HOLD, TaskStatus.CANCELLED},
            TaskStatus.ON_HOLD: {TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
            TaskStatus.COMPLETED: {TaskStatus.IN_PROGRESS},  # Allow reopening
            TaskStatus.CANCELLED: {TaskStatus.PENDING}  # Allow reopening
        }

    def get_blocking_dependencies(self) -> list:
        """Get dependencies that block this task"""
        blocking = []
        for dep in self.dependencies:
            if dep.status != TaskStatus.COMPLETED:
                blocking.append(dep)
        return blocking

    def is_ready_to_start(self) -> bool:
        """Check if task is ready to start (no blocking dependencies)"""
        return len(self.get_blocking_dependencies()) == 0

    def get_progress_percentage(self) -> float:
        """Calculate progress percentage based on status"""
        status_progress = {
            TaskStatus.PENDING: 0.0,
            TaskStatus.IN_PROGRESS: 50.0,
            TaskStatus.COMPLETED: 100.0,
            TaskStatus.ON_HOLD: 25.0,
            TaskStatus.CANCELLED: 0.0
        }
        return status_progress.get(self.status, 0.0)