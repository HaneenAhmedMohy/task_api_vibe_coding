from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_task():
    response = client.post("/tasks", json={
        "title": "Buy groceries",
        "description": "Milk and eggs",
        "priority": "high"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy groceries"
    assert data["status"] == "pending"

def test_get_tasks():
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_task():
    response = client.put("/tasks/1", json={
        "status": "completed"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

def test_filter_tasks_by_status():
    response = client.get("/tasks?status=completed")
    assert response.status_code == 200
    for task in response.json():
        assert task["status"] == "completed"

def test_delete_task():
    response = client.delete("/tasks/1")
    assert response.status_code == 204
