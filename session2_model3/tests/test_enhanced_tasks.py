import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json

from app.main import app
from app.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority

client = TestClient(app)


@pytest.fixture
def db_session():
    """Create a test database session"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Base

    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Override the dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal()

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "priority": "high",
        "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "assigned_to": "test@example.com",
        "estimated_hours": 8,
        "tags": ["test", "sample"]
    }


class TestTaskCreation:
    """Test task creation endpoints"""

    def test_create_basic_task(self, db_session, sample_task_data):
        """Test creating a basic task"""
        response = client.post("/api/v1/tasks/", json=sample_task_data)

        assert response.status_code == 201
        data = response.json()

        assert data["title"] == sample_task_data["title"]
        assert data["description"] == sample_task_data["description"]
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        assert data["assigned_to"] == sample_task_data["assigned_to"]
        assert data["estimated_hours"] == sample_task_data["estimated_hours"]
        assert set(data["tags"]) == set(sample_task_data["tags"])
        assert data["progress_percentage"] == 0.0
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_task_with_dependencies(self, db_session, sample_task_data):
        """Test creating a task with dependencies"""
        # First create a dependency task
        dep_task = Task(
            title="Dependency Task",
            description="This is a dependency",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.HIGH
        )
        db_session.add(dep_task)
        db_session.commit()

        # Create task with dependency
        sample_task_data["dependency_ids"] = [dep_task.id]
        response = client.post("/api/v1/tasks/", json=sample_task_data)

        assert response.status_code == 201
        data = response.json()
        assert len(data["dependencies"]) == 1
        assert data["dependencies"][0]["id"] == dep_task.id
        assert data["is_ready_to_start"] == True  # Dependency is completed

    def test_create_task_invalid_dependencies(self, db_session, sample_task_data):
        """Test creating a task with non-existent dependencies"""
        sample_task_data["dependency_ids"] = [999]
        response = client.post("/api/v1/tasks/", json=sample_task_data)

        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_create_task_invalid_tags(self, db_session, sample_task_data):
        """Test creating a task with too many tags"""
        sample_task_data["tags"] = [f"tag{i}" for i in range(25)]
        response = client.post("/api/v1/tasks/", json=sample_task_data)

        assert response.status_code == 422
        assert "Maximum 20 unique tags" in str(response.json())


class TestTaskRetrieval:
    """Test task retrieval endpoints"""

    @pytest.fixture
    def sample_tasks(self, db_session):
        """Create sample tasks for testing"""
        tasks = [
            Task(
                title="Task 1",
                description="First task",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                due_date=datetime.utcnow() + timedelta(days=1),
                assigned_to="user1@example.com",
                tags_list=["urgent", "backend"]
            ),
            Task(
                title="Task 2",
                description="Second task",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.MEDIUM,
                due_date=datetime.utcnow() - timedelta(days=1),  # Overdue
                assigned_to="user2@example.com",
                tags_list=["frontend", "ui"]
            ),
            Task(
                title="Task 3",
                description="Third task",
                status=TaskStatus.COMPLETED,
                priority=TaskPriority.LOW,
                tags_list=["documentation"]
            )
        ]

        for task in tasks:
            db_session.add(task)
        db_session.commit()

        return tasks

    def test_get_all_tasks(self, sample_tasks):
        """Test retrieving all tasks"""
        response = client.get("/api/v1/tasks/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Check that tasks have all expected fields
        for task in data:
            assert "id" in task
            assert "title" in task
            assert "status" in task
            assert "progress_percentage" in task
            assert "tags" in task
            assert isinstance(task["tags"], list)

    def test_filter_tasks_by_status(self, sample_tasks):
        """Test filtering tasks by status"""
        response = client.get("/api/v1/tasks/?status=pending")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "pending"

    def test_filter_tasks_by_priority(self, sample_tasks):
        """Test filtering tasks by priority"""
        response = client.get("/api/v1/tasks/?priority=high")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["priority"] == "high"

    def test_filter_tasks_by_assignee(self, sample_tasks):
        """Test filtering tasks by assignee"""
        response = client.get("/api/v1/tasks/?assigned_to=user1@example.com")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["assigned_to"] == "user1@example.com"

    def test_filter_tasks_by_tags(self, sample_tasks):
        """Test filtering tasks by tags"""
        response = client.get("/api/v1/tasks/?tags=frontend")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "frontend" in data[0]["tags"]

    def test_search_tasks(self, sample_tasks):
        """Test searching tasks"""
        response = client.get("/api/v1/tasks/?search=Second")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Second" in data[0]["title"]

    def test_filter_overdue_tasks(self, sample_tasks):
        """Test filtering overdue tasks"""
        response = client.get("/api/v1/tasks/?overdue=true")

        assert response.status_code == 200
        data = response.json()
        # Should include the overdue task (Task 2)
        overdue_tasks = [t for t in data if t["id"] == sample_tasks[1].id]
        assert len(overdue_tasks) == 1

    def test_pagination(self, sample_tasks):
        """Test task pagination"""
        response = client.get("/api/v1/tasks/?skip=1&limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_sort_tasks(self, sample_tasks):
        """Test task sorting"""
        response = client.get("/api/v1/tasks/?sort_by=title&sort_desc=false")

        assert response.status_code == 200
        data = response.json()
        titles = [task["title"] for task in data]
        assert titles == sorted(titles)

    def test_get_task_statistics(self, sample_tasks):
        """Test getting task statistics"""
        response = client.get("/api/v1/tasks/statistics")

        assert response.status_code == 200
        data = response.json()

        assert data["total_tasks"] == 3
        assert data["pending_tasks"] == 1
        assert data["in_progress_tasks"] == 1
        assert data["completed_tasks"] == 1
        assert data["overdue_tasks"] == 1
        assert "tasks_by_priority" in data
        assert data["tasks_by_priority"]["high"] == 1


class TestTaskUpdate:
    """Test task update endpoints"""

    @pytest.fixture
    def existing_task(self, db_session):
        """Create an existing task for testing updates"""
        task = Task(
            title="Original Task",
            description="Original description",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM
        )
        db_session.add(task)
        db_session.commit()
        return task

    def test_update_task_title(self, existing_task):
        """Test updating task title"""
        update_data = {"title": "Updated Task Title"}
        response = client.put(f"/api/v1/tasks/{existing_task.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Task Title"
        assert data["description"] == "Original description"  # Unchanged

    def test_update_task_status_valid_transition(self, existing_task):
        """Test updating task status with valid transition"""
        update_data = {"status": "in-progress"}
        response = client.put(f"/api/v1/tasks/{existing_task.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in-progress"
        assert data["progress_percentage"] == 50.0

    def test_update_task_status_invalid_transition(self, existing_task):
        """Test updating task status with invalid transition"""
        update_data = {"status": "completed"}  # Can't go from pending to completed directly
        response = client.put(f"/api/v1/tasks/{existing_task.id}", json=update_data)

        assert response.status_code == 400
        assert "Cannot transition" in response.json()["detail"]

    def test_update_task_with_tags(self, existing_task):
        """Test updating task tags"""
        update_data = {"tags": ["new", "tags", "here"]}
        response = client.put(f"/api/v1/tasks/{existing_task.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert set(data["tags"]) == {"new", "tags", "here"}

    def test_complete_task_sets_completed_at(self, existing_task):
        """Test that completing a task sets the completed_at timestamp"""
        # First transition to in-progress
        client.put(f"/api/v1/tasks/{existing_task.id}", json={"status": "in-progress"})

        # Then complete
        response = client.put(f"/api/v1/tasks/{existing_task.id}", json={"status": "completed"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress_percentage"] == 100.0
        assert data["completed_at"] is not None


class TestBulkOperations:
    """Test bulk operation endpoints"""

    @pytest.fixture
    def multiple_tasks(self, db_session):
        """Create multiple tasks for bulk operations"""
        tasks = [
            Task(title="Task 1", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM),
            Task(title="Task 2", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM),
            Task(title="Task 3", status=TaskStatus.IN_PROGRESS, priority=TaskPriority.HIGH),
        ]

        for task in tasks:
            db_session.add(task)
        db_session.commit()

        return tasks

    def test_bulk_update_status(self, multiple_tasks):
        """Test bulk updating task status"""
        task_ids = [task.id for task in multiple_tasks[:2]]
        bulk_data = {
            "task_ids": task_ids,
            "updates": {"status": "on-hold"}
        }

        response = client.post("/api/v1/tasks/bulk-update", json=bulk_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for task in data:
            assert task["status"] == "on-hold"

    def test_bulk_update_invalid_status_transition(self, multiple_tasks):
        """Test bulk update with invalid status transition"""
        task_ids = [task.id for task in multiple_tasks[:2]]
        bulk_data = {
            "task_ids": task_ids,
            "updates": {"status": "completed"}  # Can't go from pending to completed
        }

        response = client.post("/api/v1/tasks/bulk-update", json=bulk_data)

        assert response.status_code == 400
        assert "cannot transition" in response.json()["detail"]

    def test_bulk_update_nonexistent_tasks(self, multiple_tasks):
        """Test bulk update with non-existent task IDs"""
        bulk_data = {
            "task_ids": [999, 1000],
            "updates": {"priority": "high"}
        }

        response = client.post("/api/v1/tasks/bulk-update", json=bulk_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestStatusTransitions:
    """Test status transition validation"""

    @pytest.fixture
    def test_task(self, db_session):
        """Create a test task for transition testing"""
        task = Task(
            title="Test Task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM
        )
        db_session.add(task)
        db_session.commit()
        return task

    def test_check_valid_status_transition(self, test_task):
        """Test checking a valid status transition"""
        response = client.post(
            f"/api/v1/tasks/{test_task.id}/status-transition?new_status=in-progress"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_allowed"] == True
        assert data["current_status"] == "pending"
        assert data["new_status"] == "in-progress"
        assert data["reason"] is None

    def test_check_invalid_status_transition(self, test_task):
        """Test checking an invalid status transition"""
        response = client.post(
            f"/api/v1/tasks/{test_task.id}/status-transition?new_status=completed"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_allowed"] == False
        assert data["reason"] is not None
        assert "Cannot transition" in data["reason"]

    def test_check_transition_nonexistent_task(self):
        """Test checking status transition for non-existent task"""
        response = client.post(
            "/api/v1/tasks/999/status-transition?new_status=in-progress"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestTaskDependencies:
    """Test task dependency functionality"""

    def test_task_dependency_blocking(self, db_session):
        """Test that incomplete dependencies block task"""
        # Create a dependent task
        dependency = Task(
            title="Dependency",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH
        )
        db_session.add(dependency)
        db_session.commit()

        # Create a task that depends on the above
        main_task = Task(
            title="Main Task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM
        )
        db_session.add(main_task)
        db_session.commit()

        # Add dependency relationship
        main_task.dependencies.append(dependency)
        db_session.commit()

        response = client.get(f"/api/v1/tasks/{main_task.id}")
        data = response.json()

        assert data["is_ready_to_start"] == False
        assert len(data["dependencies"]) == 1
        assert data["dependencies"][0]["status"] == "pending"

    def test_delete_task_with_dependents_fails(self, db_session):
        """Test that deleting a task with dependents fails"""
        # Create two tasks
        task1 = Task(title="Task 1", status=TaskStatus.PENDING)
        task2 = Task(title="Task 2", status=TaskStatus.PENDING)

        db_session.add(task1)
        db_session.add(task2)
        db_session.commit()

        # Make task2 depend on task1
        task2.dependencies.append(task1)
        db_session.commit()

        # Try to delete task1 (should fail)
        response = client.delete(f"/api/v1/tasks/{task1.id}")

        assert response.status_code == 400
        assert "depend on it" in response.json()["detail"]


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_get_nonexistent_task(self):
        """Test getting a non-existent task"""
        response = client.get("/api/v1/tasks/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_nonexistent_task(self):
        """Test updating a non-existent task"""
        response = client.put("/api/v1/tasks/999", json={"title": "New Title"})

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_nonexistent_task(self):
        """Test deleting a non-existent task"""
        response = client.delete("/api/v1/tasks/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_create_task_invalid_data(self, db_session):
        """Test creating a task with invalid data"""
        invalid_data = {
            "title": "",  # Empty title
            "estimated_hours": -5,  # Negative hours
        }

        response = client.post("/api/v1/tasks/", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_invalid_query_parameters(self, db_session):
        """Test invalid query parameters"""
        response = client.get("/api/v1/tasks/?limit=1001")  # Over limit

        assert response.status_code == 422

    def test_invalid_status_value(self, db_session):
        """Test invalid status value in update"""
        response = client.put("/api/v1/tasks/1", json={"status": "invalid_status"})

        assert response.status_code == 422


class TestAPIConsistency:
    """Test API consistency and data integrity"""

    def test_task_count_consistency(self, db_session):
        """Test that task count endpoint matches actual count"""
        # Create some tasks
        for i in range(5):
            task = Task(title=f"Task {i}", status=TaskStatus.PENDING)
            db_session.add(task)

        db_session.commit()

        # Check count
        count_response = client.get("/api/v1/tasks/count")
        tasks_response = client.get("/api/v1/tasks/")

        assert count_response.status_code == 200
        assert tasks_response.status_code == 200

        count = count_response.json()["total"]
        tasks = tasks_response.json()

        assert count == len(tasks)
        assert count == 5

    def test_datetime_consistency(self, db_session):
        """Test datetime field consistency"""
        before_create = datetime.utcnow()

        task_data = {
            "title": "Time Test Task",
            "description": "Testing timestamps"
        }

        response = client.post("/api/v1/tasks/", json=task_data)
        assert response.status_code == 201

        data = response.json()

        # Parse timestamps
        created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))

        # Check that timestamps are reasonable
        assert created_at >= before_create
        assert updated_at >= created_at
        assert data["completed_at"] is None  # Not completed yet


if __name__ == "__main__":
    pytest.main([__file__])