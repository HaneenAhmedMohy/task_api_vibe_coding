"""Custom exceptions for the Task Management API."""


class TaskNotFoundException(Exception):
    """Exception raised when a task is not found."""

    def __init__(self, task_id: int):
        self.task_id = task_id
        self.message = f"Task with id {task_id} not found"
        super().__init__(self.message)


class TaskValidationError(Exception):
    """Exception raised when task validation fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DatabaseOperationException(Exception):
    """Exception raised when a database operation fails."""

    def __init__(self, message: str):
        self.message = f"Database operation failed: {message}"
        super().__init__(self.message)