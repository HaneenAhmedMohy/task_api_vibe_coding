You are implementing a RESTful Task Management API using Python and FastAPI.

IMPORTANT:
- Follow Test-Driven Development.
- The implementation MUST make the following tests pass.
- Do NOT change the tests.
- Use SQLite for persistence.
- Use proper HTTP status codes.
- Include input validation and error handling.

Task Model Requirements:
- id (int)
- title (string, required)
- description (string, optional)
- status (pending | in-progress | completed)
- priority (low | medium | high)
- created_at (timestamp)

API Requirements:
- POST /tasks
- GET /tasks
- GET /tasks?status=&priority=
- PUT /tasks/{id}
- DELETE /tasks/{id}

Here are the tests:

@test-tasks.py  

Now:
1. Create all required files
2. Implement the API so ALL tests pass
3. Use clean, readable, maintainable code

---------------------------------------------

## Answer:

I'll implement a RESTful Task Management API using Python and FastAPI following Test-Driven Development. Let me start by creating a todo list to track the implementation.
Update Todos

Examine the test file to understand requirements

Create session1_model1 folder structure

Create database models for Task

Implement Pydantic schemas for request/response

Create database configuration

Implement POST /tasks endpoint

Implement GET /tasks endpoint

Implement GET /tasks with query parameters

Implement PUT /tasks/{id} endpoint

Implement DELETE /tasks/{id} endpoint

Create main FastAPI application

Create requirements.txt file

Run tests to verify implementation