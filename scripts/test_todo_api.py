"""
GÖK SYSTEMS TECH — FastAPI TODO Verification Test
Validates Phase 12 part 2: Generating and testing a real FastAPI API with automated HTTP assertions.
"""

import sys
import subprocess
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from gokai.packages.tools.jailed_fs import JailedFileSystem
from gokai.packages.tools.terminal import SandboxedTerminal
import asyncio


async def run_todo_test():
    print("\n" + "=" * 70)
    print("[GOKAI] FASTAPI TODO API VERIFICATION TEST (PHASE 12 PART 2)")
    print("=" * 70 + "\n")

    workspace = PROJECT_ROOT / "gokai" / "projects" / "fastapi_todo_project"
    fs = JailedFileSystem(workspace)
    terminal = SandboxedTerminal(workspace)

    # 1. Generate FastAPI TODO App
    todo_code = '''"""
FastAPI TODO Application
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="GökAI TODO API")

class TodoItem(BaseModel):
    id: int
    title: str
    completed: bool = False

todos_db: dict[int, TodoItem] = {}

@app.get("/todos", response_model=List[TodoItem])
def get_todos():
    return list(todos_db.values())

@app.post("/todos", response_model=TodoItem, status_code=201)
def create_todo(item: TodoItem):
    if item.id in todos_db:
        raise HTTPException(status_code=400, detail="Item already exists")
    todos_db[item.id] = item
    return item

@app.get("/todos/{todo_id}", response_model=TodoItem)
def get_todo(todo_id: int):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todos_db[todo_id]
'''
    fs.write_file("main.py", todo_code)
    print("  [PASS] main.py written to workspace")

    # 2. Generate FastAPI TestClient test suite
    test_code = '''"""
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
'''
    fs.write_file("test_todo.py", test_code)
    print("  [PASS] test_todo.py written to workspace")

    # 3. Execute Pytest on the FastAPI application
    py_exe = sys.executable
    cmd = f'"{py_exe}" -m pytest test_todo.py -v'
    print(f"  * Running automated test suite: {cmd}")
    res = await terminal.execute_command(cmd)

    print("\n" + "-" * 70)
    print("TEST EXECUTION OUTPUT:")
    print(res.stdout)
    print("-" * 70)

    assert res.exit_code == 0, f"Tests failed with exit code {res.exit_code}:\n{res.stderr}"
    assert "2 passed" in res.stdout, "Expected 2 tests to pass"

    print("\n" + "=" * 70)
    print("FASTAPI TODO API FULLY VERIFIED WITH 100% TEST PASS RATE!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_todo_test())
