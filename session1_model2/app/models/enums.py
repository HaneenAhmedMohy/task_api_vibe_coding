"""Enum definitions for the Task Management API."""

from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"

    @classmethod
    def values(cls):
        """Get all possible status values."""
        return [status.value for status in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a status value is valid."""
        return value in cls.values()


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def values(cls):
        """Get all possible priority values."""
        return [priority.value for priority in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a priority value is valid."""
        return value in cls.values()