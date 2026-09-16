"""
FastAPI TODO Tests
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_and_get_todo():
    # Test GET empty list
    resp = client.get("/todos")
    assert resp.status_code == 200
    assert resp.json() == []

    # Test POST new todo
    payload = {"id": 1, "title": "Implement GökAI", "completed": True}
    create_resp = client.post("/todos", json=payload)
    assert create_resp.status_code == 201
    assert create_resp.json()["title"] == "Implement GökAI"

    # Test GET by ID
    get_resp = client.get("/todos/1")
    assert get_resp.status_code == 200
    assert get_resp.json()["completed"] is True

def test_not_found():
    resp = client.get("/todos/999")
    assert resp.status_code == 404
