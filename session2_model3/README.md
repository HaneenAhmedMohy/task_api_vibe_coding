# Enhanced Task Management API

A production-ready REST API for task management with advanced features including dependencies, workflow management, and comprehensive analytics.

## Features

### Core Functionality
- ✅ **CRUD Operations**: Create, read, update, and delete tasks
- ✅ **Advanced Filtering**: Filter by status, priority, assignee, tags, due dates
- ✅ **Search**: Full-text search across title, description, and assignee
- ✅ **Pagination**: Efficient pagination with customizable limits
- ✅ **Sorting**: Sort by any field with ascending/descending options

### Enhanced Features
- ✅ **Task Dependencies**: Define and manage task dependencies
- ✅ **Status Workflow**: Enforced status transitions with validation
- ✅ **Bulk Operations**: Update multiple tasks simultaneously
- ✅ **Tags System**: Organize tasks with custom tags
- ✅ **Time Tracking**: Estimate and track actual hours spent
- ✅ **Due Date Management**: Track overdue and upcoming tasks
- ✅ **Assignment**: Assign tasks to team members
- ✅ **Progress Tracking**: Automatic progress calculation

### Analytics & Reporting
- ✅ **Statistics Dashboard**: Comprehensive task statistics
- ✅ **Completion Metrics**: Track average completion times
- ✅ **Overdue Reports**: Identify overdue tasks
- ✅ **Priority Distribution**: Tasks grouped by priority levels
- ✅ **Status Distribution**: Tasks grouped by current status

## API Endpoints

### Task Management
- `POST /api/v1/tasks/` - Create new task with optional dependencies
- `GET /api/v1/tasks/` - List tasks with filtering and pagination
- `GET /api/v1/tasks/{task_id}` - Get specific task details
- `PUT /api/v1/tasks/{task_id}` - Update task with validation
- `DELETE /api/v1/tasks/{task_id}` - Delete task (with dependency checks)

### Advanced Operations
- `POST /api/v1/tasks/bulk-update` - Update multiple tasks at once
- `POST /api/v1/tasks/{task_id}/status-transition` - Check status transition validity
- `GET /api/v1/tasks/statistics` - Get comprehensive task statistics

### Utility Endpoints
- `GET /api/v1/tasks/count` - Get total task count
- `GET /api/v1/tasks/status/list` - List available statuses
- `GET /api/v1/tasks/priority/list` - List available priorities
- `GET /health` - Health check
- `GET /` - API information

## Enhanced Data Model

### Task Fields
- `id`: Unique identifier
- `title`: Task title (required, max 255 chars)
- `description`: Detailed description (optional, max 5000 chars)
- `status`: Current status (pending, in-progress, completed, cancelled, on-hold)
- `priority`: Task priority (low, medium, high, critical)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `completed_at`: Completion timestamp (when applicable)
- `due_date`: Due date (optional)
- `assigned_to`: Assignee email/identifier (optional, max 100 chars)
- `estimated_hours`: Estimated completion time (optional)
- `actual_hours`: Actual time spent (optional)
- `tags`: List of tags for organization (max 20 tags)

### Status Workflow
The API enforces valid status transitions:
- **pending** → in-progress, cancelled, on-hold
- **in-progress** → completed, on-hold, cancelled
- **on-hold** → pending, in-progress, cancelled
- **completed** → in-progress (reopening allowed)
- **cancelled** → pending (reopening allowed)

## Usage Examples

### Creating a Task with Dependencies
```json
POST /api/v1/tasks/
{
  "title": "Implement User Authentication",
  "description": "Add JWT-based authentication to the API",
  "priority": "high",
  "due_date": "2024-12-31T23:59:59Z",
  "assigned_to": "developer@example.com",
  "estimated_hours": 40,
  "tags": ["authentication", "security", "backend"],
  "dependency_ids": [1, 2]
}
```

### Advanced Filtering
```bash
# Get high priority tasks assigned to a developer
GET /api/v1/tasks/?priority=high&assigned_to=developer@example.com

# Get overdue tasks
GET /api/v1/tasks/?overdue=true

# Search tasks by keyword
GET /api/v1/tasks/?search=authentication

# Filter by tags
GET /api/v1/tasks/?tags=security,backend

# Pagination and sorting
GET /api/v1/tasks/?skip=0&limit=10&sort_by=due_date&sort_desc=true
```

### Bulk Operations
```json
POST /api/v1/tasks/bulk-update
{
  "task_ids": [1, 2, 3],
  "updates": {
    "status": "in-progress",
    "priority": "high"
  }
}
```

### Status Transition Check
```bash
POST /api/v1/tasks/123/status-transition?new_status=completed
```

Response:
```json
{
  "task_id": 123,
  "current_status": "in-progress",
  "new_status": "completed",
  "is_allowed": true,
  "reason": null
}
```

### Statistics
```json
GET /api/v1/tasks/statistics

{
  "total_tasks": 150,
  "pending_tasks": 45,
  "in_progress_tasks": 30,
  "completed_tasks": 60,
  "cancelled_tasks": 10,
  "on_hold_tasks": 5,
  "overdue_tasks": 8,
  "tasks_by_priority": {
    "low": 30,
    "medium": 75,
    "high": 35,
    "critical": 10
  },
  "average_completion_time": 42.5
}
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- SQLite (for development)

### Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Testing

Run the comprehensive test suite:
```bash
pytest tests/ -v
```

### Test Coverage
- ✅ Task creation with all fields and dependencies
- ✅ Filtering, searching, pagination, and sorting
- ✅ Status transition validation
- ✅ Bulk operations
- ✅ Error handling and edge cases
- ✅ Dependency management
- ✅ API consistency and data integrity

## Architecture

The enhanced API follows a clean architecture pattern:

### Layers
- **Models**: SQLAlchemy ORM models with business logic
- **Schemas**: Pydantic validation and serialization
- **Routers**: FastAPI endpoints with comprehensive error handling
- **Database**: SQLite with relationship management

### Key Features
- **Status Workflow Enforcement**: Built into the model layer
- **Dependency Management**: Many-to-many relationships with validation
- **Comprehensive Error Handling**: Structured error responses
- **Logging**: Detailed logging for debugging and monitoring
- **Input Validation**: Robust Pydantic validators
- **Performance**: Optimized queries with eager loading

## Performance Optimizations

- **Database Indexing**: Optimized queries on frequently filtered fields
- **Eager Loading**: Prevents N+1 query problems
- **Pagination**: Limits data transfer for large datasets
- **Efficient Filtering**: SQLAlchemy query optimization
- **Response Serialization**: Efficient model-to-schema conversion

## Security Considerations

- **Input Validation**: All inputs validated and sanitized
- **SQL Injection Protection**: SQLAlchemy parameterized queries
- **Error Information**: Sanitized error messages
- **Rate Limiting**: Can be implemented at the FastAPI level
- **Authentication**: Ready for JWT/Session integration

## Extensibility

The API is designed for easy extension:

### Adding New Fields
1. Update the Task model
2. Update Pydantic schemas
3. Modify endpoints as needed

### Adding New Statuses
1. Update the TaskStatus enum
2. Update workflow transition logic
3. Update test cases

### Adding New Endpoints
1. Create new router functions
2. Add comprehensive validation
3. Include test coverage

## Monitoring & Debugging

- **Structured Logging**: All operations logged with context
- **Health Checks**: `/health` endpoint for monitoring
- **Error Tracking**: Detailed error responses with codes
- **Performance Metrics**: Can be integrated with monitoring tools

## Contributing

1. Follow the established code patterns
2. Add comprehensive tests for new features
3. Update documentation
4. Ensure all tests pass before submission

## License

This project is part of the AI-Assisted Development study comparing different development methodologies.