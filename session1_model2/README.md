# Task Management API

A RESTful API built with FastAPI for managing tasks, built following best practices with proper error handling, validation, and documentation.

## Features

- ✅ CRUD operations for tasks
- ✅ Task filtering by status and priority
- ✅ Search functionality
- ✅ Pagination support
- ✅ Proper HTTP status codes
- ✅ Comprehensive error handling
- ✅ Auto-generated OpenAPI documentation
- ✅ Pydantic validation
- ✅ SQLAlchemy ORM with SQLite

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python run.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload
```

3. The API will be available at:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Tasks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/tasks` | Get all tasks with optional filtering |
| POST | `/api/v1/tasks` | Create a new task |
| GET | `/api/v1/tasks/{id}` | Get a specific task |
| PUT | `/api/v1/tasks/{id}` | Update a task |
| DELETE | `/api/v1/tasks/{id}` | Delete a task |

### Additional Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/tasks/count` | Get total count of tasks with filters |
| GET | `/api/v1/tasks/status/list` | Get available task statuses |
| GET | `/api/v1/tasks/priority/list` | Get available task priorities |

## Task Model

```json
{
  "id": 1,
  "title": "Complete project documentation",
  "description": "Write comprehensive documentation",
  "status": "pending",
  "priority": "medium",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": null
}
```

### Task Statuses

- `pending` - Task is not started
- `in-progress` - Task is currently being worked on
- `completed` - Task is finished

### Task Priorities

- `low` - Low priority task
- `medium` - Medium priority task
- `high` - High priority task

## Usage Examples

### Create a Task

```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Complete project documentation",
       "description": "Write comprehensive documentation for the new API endpoints",
       "priority": "high"
     }'
```

### Get All Tasks

```bash
curl "http://localhost:8000/api/v1/tasks"
```

### Get Tasks with Filters

```bash
# Filter by status
curl "http://localhost:8000/api/v1/tasks?status=pending"

# Filter by priority
curl "http://localhost:8000/api/v1/tasks?priority=high"

# Search tasks
curl "http://localhost:8000/api/v1/tasks?search=documentation"

# Pagination
curl "http://localhost:8000/api/v1/tasks?skip=0&limit=10"
```

### Update a Task

```bash
curl -X PUT "http://localhost:8000/api/v1/tasks/1" \
     -H "Content-Type: application/json" \
     -d '{
       "status": "in-progress",
       "description": "Updated description"
     }'
```

### Delete a Task

```bash
curl -X DELETE "http://localhost:8000/api/v1/tasks/1"
```

## Query Parameters

### GET /api/v1/tasks

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of tasks to skip |
| `limit` | integer | 100 | Maximum number of tasks to return (1-1000) |
| `status` | string | - | Filter by task status |
| `priority` | string | - | Filter by task priority |
| `search` | string | - | Search in title and description |

## HTTP Status Codes

- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request (validation error)
- `404` - Not Found
- `500` - Internal Server Error

## Error Response Format

```json
{
  "detail": "Error message description"
}
```

## Project Structure

```
session1_model2/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py         # Enum definitions
│   │   ├── database.py      # Database configuration
│   │   └── task.py          # SQLAlchemy Task model
│   ├── routers/
│   │   ├── __init__.py
│   │   └── tasks.py         # Task endpoints
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── base.py          # Base validators and mixins
│   │   └── task.py          # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   └── task_service.py  # Business logic layer
│   └── exceptions/
│       ├── __init__.py
│       └── task_exceptions.py  # Custom exceptions
├── run.py                   # Startup script
├── requirements.txt         # Dependencies
├── .gitignore
└── README.md
```

## Database

The API uses SQLite as the default database. The database file (`task_management.db`) will be created automatically when the application starts.

## License

This project is for educational purposes.