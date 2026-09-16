"""
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
