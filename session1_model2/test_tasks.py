from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    response = client.post("/api/v1/tasks", json={
        "title": "Buy groceries",
        "description": "Milk and eggs",
        "priority": "high"
    })
    return response.json()


@pytest.fixture
def multiple_tasks():
    """Create multiple tasks for testing filters."""
    tasks_data = [
        {"title": "Task 1", "status": "pending", "priority": "high"},
        {"title": "Task 2", "status": "completed", "priority": "medium"},
        {"title": "Task 3", "status": "in-progress", "priority": "low"},
        {"title": "Task 4", "status": "completed", "priority": "high"}
    ]

    task_ids = []
    for task_data in tasks_data:
        response = client.post("/api/v1/tasks", json=task_data)
        task_ids.append(response.json()["id"])

    return task_ids


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_task():
    """Test creating a new task."""
    response = client.post("/api/v1/tasks", json={
        "title": "Buy groceries",
        "description": "Milk and eggs",
        "priority": "high"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy groceries"
    assert data["description"] == "Milk and eggs"
    assert data["status"] == "pending"
    assert data["priority"] == "high"
    assert "id" in data
    assert "created_at" in data


def test_create_task_with_invalid_status():
    """Test creating a task with invalid status."""
    response = client.post("/api/v1/tasks", json={
        "title": "Invalid task",
        "status": "invalid_status"
    })
    assert response.status_code == 422


def test_create_task_with_invalid_priority():
    """Test creating a task with invalid priority."""
    response = client.post("/api/v1/tasks", json={
        "title": "Invalid task",
        "priority": "invalid_priority"
    })
    assert response.status_code == 422


def test_create_task_empty_title():
    """Test creating a task with empty title."""
    response = client.post("/api/v1/tasks", json={
        "title": "",
        "priority": "medium"
    })
    assert response.status_code == 422


def test_get_tasks():
    """Test getting all tasks."""
    # Create a task first
    client.post("/api/v1/tasks", json={
        "title": "Test task",
        "priority": "medium"
    })

    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
    assert len(tasks) > 0


def test_get_task_by_id():
    """Test getting a specific task."""
    # Create a task first
    create_response = client.post("/api/v1/tasks", json={
        "title": "Test task by ID",
        "priority": "medium"
    })
    task_id = create_response.json()["id"]

    # Get the task
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Test task by ID"


def test_get_nonexistent_task():
    """Test getting a non-existent task."""
    response = client.get("/api/v1/tasks/99999")
    assert response.status_code == 404


def test_update_task():
    """Test updating a task."""
    # Create a task first
    create_response = client.post("/api/v1/tasks", json={
        "title": "Original task",
        "priority": "high"
    })
    task_id = create_response.json()["id"]

    # Update the task
    response = client.put(f"/api/v1/tasks/{task_id}", json={
        "status": "completed"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["title"] == "Original task"  # Should remain unchanged


def test_update_task_multiple_fields():
    """Test updating multiple fields of a task."""
    # Create a task first
    create_response = client.post("/api/v1/tasks", json={
        "title": "Original title",
        "description": "Original description",
        "status": "pending",
        "priority": "low"
    })
    task_id = create_response.json()["id"]

    # Update multiple fields
    response = client.put(f"/api/v1/tasks/{task_id}", json={
        "title": "Updated title",
        "status": "in-progress",
        "priority": "high"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated title"
    assert data["status"] == "in-progress"
    assert data["priority"] == "high"


def test_update_nonexistent_task():
    """Test updating a non-existent task."""
    response = client.put("/api/v1/tasks/99999", json={
        "status": "completed"
    })
    assert response.status_code == 404


def test_filter_tasks_by_status(multiple_tasks):
    """Test filtering tasks by status."""
    response = client.get("/api/v1/tasks?status=completed")
    assert response.status_code == 200
    tasks = response.json()
    for task in tasks:
        assert task["status"] == "completed"


def test_filter_tasks_by_priority(multiple_tasks):
    """Test filtering tasks by priority."""
    response = client.get("/api/v1/tasks?priority=high")
    assert response.status_code == 200
    tasks = response.json()
    for task in tasks:
        assert task["priority"] == "high"


def test_filter_tasks_multiple_filters(multiple_tasks):
    """Test filtering tasks by multiple criteria."""
    response = client.get("/api/v1/tasks?status=completed&priority=high")
    assert response.status_code == 200
    tasks = response.json()
    for task in tasks:
        assert task["status"] == "completed"
        assert task["priority"] == "high"


def test_search_tasks(multiple_tasks):
    """Test searching tasks."""
    # Create a specific task for this test
    response = client.post("/api/v1/tasks", json={
        "title": "Searchable Task 1",
        "description": "This is a task for searching",
        "priority": "medium"
    })
    assert response.status_code == 201

    # Test searching by title
    response = client.get("/api/v1/tasks?search=Searchable Task 1")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) > 0
    found = any("Searchable Task 1" in task["title"] for task in tasks)
    assert found, "Should find task by title"

    # Test searching by description
    response = client.get("/api/v1/tasks?search=task for searching")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) > 0
    found = any(
        task.get("description") and "task for searching" in task["description"]
        for task in tasks
    )
    assert found, "Should find task by description"


def test_pagination():
    """Test task pagination."""
    # Create several tasks
    for i in range(5):
        client.post("/api/v1/tasks", json={
            "title": f"Pagination task {i}",
            "priority": "medium"
        })

    # Test pagination
    response = client.get("/api/v1/tasks?skip=0&limit=2")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) <= 2


def test_delete_task():
    """Test deleting a task."""
    # Create a task first
    create_response = client.post("/api/v1/tasks", json={
        "title": "Task to delete",
        "priority": "medium"
    })
    task_id = create_response.json()["id"]

    # Delete the task
    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204

    # Verify it's deleted
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 404


def test_delete_nonexistent_task():
    """Test deleting a non-existent task."""
    response = client.delete("/api/v1/tasks/99999")
    assert response.status_code == 404


def test_get_task_count():
    """Test getting task count."""
    # Create a few tasks
    client.post("/api/v1/tasks", json={"title": "Count task 1"})
    client.post("/api/v1/tasks", json={"title": "Count task 2"})

    response = client.get("/api/v1/tasks/count")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] >= 2


def test_get_status_list():
    """Test getting available statuses."""
    response = client.get("/api/v1/tasks/status/list")
    assert response.status_code == 200
    data = response.json()
    assert "statuses" in data
    assert "pending" in data["statuses"]
    assert "in-progress" in data["statuses"]
    assert "completed" in data["statuses"]


def test_get_priority_list():
    """Test getting available priorities."""
    response = client.get("/api/v1/tasks/priority/list")
    assert response.status_code == 200
    data = response.json()
    assert "priorities" in data
    assert "low" in data["priorities"]
    assert "medium" in data["priorities"]
    assert "high" in data["priorities"]


def test_task_timestamps():
    """Test that tasks have proper timestamps."""
    response = client.post("/api/v1/tasks", json={
        "title": "Timestamp test",
        "priority": "medium"
    })
    assert response.status_code == 201
    data = response.json()
    assert "created_at" in data
    assert "updated_at" in data
    assert data["created_at"] is not None

    # Update task and check updated_at
    task_id = data["id"]
    response = client.put(f"/api/v1/tasks/{task_id}", json={
        "status": "completed"
    })
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["updated_at"] is not None


def test_default_values():
    """Test default values for status and priority."""
    response = client.post("/api/v1/tasks", json={
        "title": "Default test"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["priority"] == "medium"