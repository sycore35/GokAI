"""
GÖK SYSTEMS TECH — Tasks API Endpoints, WebSocket & SSE Real-Time Streaming
Coordinates task execution with OrchestratorEngine and streams live updates to the UI.
Supports: List, Create, Get, Cancel, Retry, SSE Stream, WebSocket Stream.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from gokai.apps.backend.app.core.database import get_db, SessionLocal
from gokai.apps.backend.app.core.config import settings
from gokai.apps.backend.app.models.entities import (
    Task,
    Project,
    Artifact as DbArtifact,
    TaskStep,
    ActivityLog,
    AgentRun,
)
from gokai.apps.backend.app.schemas.dtos import TaskCreate, TaskResponse
from gokai.packages.orchestrator.orchestrator import OrchestratorEngine
from gokai.packages.model_router.router import ModelRouter
from gokai.packages.shared.logger import get_logger

logger = get_logger("tasks_api")
router = APIRouter(prefix="/tasks", tags=["Tasks"])

# In-memory pub/sub queues for live SSE streams per task
active_streams: Dict[str, List[asyncio.Queue]] = {}
# Active WebSocket connections per task
active_websockets: Dict[str, List[WebSocket]] = {}
# Running orchestrators for cancellation support
active_orchestrators: Dict[str, OrchestratorEngine] = {}


def broadcast_task_event(task_id: str, event_type: str, data: Dict[str, Any]):
    """Pushes event payload to all subscribed SSE queues and WebSockets."""
    # SSE Queues
    if task_id in active_streams:
        for q in active_streams[task_id]:
            q.put_nowait({"type": event_type, "data": data})

    # WebSockets
    if task_id in active_websockets:
        dead_ws = []
        payload_str = json.dumps({"type": event_type, "data": data})
        for ws in active_websockets[task_id]:
            try:
                asyncio.create_task(ws.send_text(payload_str))
            except Exception:
                dead_ws.append(ws)
        for ws in dead_ws:
            active_websockets[task_id].remove(ws)


async def run_orchestrator_background(task_id: str, project_id: str, user_prompt: str, skip_research: bool):
    """Background worker executing OrchestratorEngine."""
    db = SessionLocal()
    try:
        model_router = ModelRouter(
            gemini_api_key=settings.GEMINI_API_KEY,
            openai_api_key=settings.OPENAI_API_KEY,
            deepseek_api_key=settings.DEEPSEEK_API_KEY,
            nvidia_api_key=settings.NVIDIA_API_KEY,
            default_provider=settings.DEFAULT_PROVIDER,
            default_model=settings.DEFAULT_MODEL,
            allow_mock_fallback=True
        )

        orchestrator = OrchestratorEngine(
            model_router=model_router,
            workspace_base_dir=settings.PROJECTS_DIR,
            skills_dir=settings.SKILLS_DIR,
            max_debug_cycles=settings.MAX_DEBUG_CYCLES,
            event_callback=lambda et, d: broadcast_task_event(task_id, et, d)
        )
        active_orchestrators[task_id] = orchestrator

        # Record activity
        db.add(ActivityLog(
            project_id=project_id,
            task_id=task_id,
            actor="orchestrator",
            action="TASK_STARTED",
            message=f"Starting objective: {user_prompt[:100]}",
            level="INFO"
        ))
        db.commit()

        result = await orchestrator.execute_task(
            task_id=task_id,
            project_id=project_id,
            user_prompt=user_prompt,
            skip_research=skip_research
        )

        # Update database with results
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = str(result.get("status", "COMPLETED"))
            task.estimated_cost_usd = result.get("total_cost_usd", 0.0)
            task.total_tokens = result.get("total_tokens", 0)
            task.debug_cycles = result.get("debug_cycles", 0)
            if not result.get("success"):
                task.error = result.get("error", "Task execution failure")

            # Persist generated artifacts
            for art_data in result.get("artifacts", []):
                art = DbArtifact(
                    id=art_data.get("id"),
                    project_id=project_id,
                    task_id=task_id,
                    type=str(art_data.get("type", "file")),
                    name=art_data.get("name", "file"),
                    path=art_data.get("path", "file"),
                    content=art_data.get("content", ""),
                    created_by=art_data.get("created_by", "orchestrator"),
                    metadata_json=json.dumps(art_data.get("metadata", {}))
                )
                db.add(art)

            # Persist agent execution traces
            for trace in result.get("agent_traces", []):
                agent_run = AgentRun(
                    task_id=task_id,
                    agent_name=trace.get("agent_name", "agent"),
                    status="SUCCESS" if trace.get("success") else "FAILED",
                    summary=trace.get("summary", ""),
                    duration_ms=trace.get("duration_ms", 0.0),
                    input_tokens=trace.get("input_tokens", 0),
                    output_tokens=trace.get("output_tokens", 0),
                    cost_usd=trace.get("cost_usd", 0.0),
                    errors=json.dumps(trace.get("errors", []))
                )
                db.add(agent_run)

            db.add(ActivityLog(
                project_id=project_id,
                task_id=task_id,
                actor="orchestrator",
                action="TASK_FINISHED",
                message=f"Task {task.status} in {result.get('duration_seconds', 0.0):.1f}s",
                level="SUCCESS" if task.status == "COMPLETED" else "ERROR"
            ))
            db.commit()

        broadcast_task_event(task_id, "task_finished", result)

    except Exception as ex:
        logger.error(f"Task execution failed with exception: {ex}")
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "FAILED"
            task.error = str(ex)
            db.add(ActivityLog(
                project_id=project_id,
                task_id=task_id,
                actor="orchestrator",
                action="TASK_FAILED",
                message=f"Exception: {str(ex)[:200]}",
                level="ERROR"
            ))
            db.commit()
        broadcast_task_event(task_id, "task_failed", {"error": str(ex)})
    finally:
        active_orchestrators.pop(task_id, None)
        db.close()


@router.get("", response_model=List[TaskResponse])
def list_tasks(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Task)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    return query.order_by(Task.created_at.desc()).all()


@router.post("", response_model=TaskResponse, status_code=202)
def create_and_start_task(
    payload: TaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task = Task(
        project_id=payload.project_id,
        user_prompt=payload.user_prompt,
        status="PLANNING"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Launch autonomous orchestrator in background
    background_tasks.add_task(
        run_orchestrator_background,
        task.id,
        project.id,
        payload.user_prompt,
        payload.skip_research
    )

    return task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/cancel")
def cancel_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_id in active_orchestrators:
        active_orchestrators[task_id].cancel_task(task_id)

    task.status = "CANCELLED"
    db.commit()
    broadcast_task_event(task_id, "task_cancelled", {"task_id": task_id})
    return {"status": "CANCELLED", "task_id": task_id}


@router.post("/{task_id}/retry", response_model=TaskResponse, status_code=202)
def retry_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "PLANNING"
    task.error = None
    db.commit()
    db.refresh(task)

    background_tasks.add_task(
        run_orchestrator_background,
        task.id,
        task.project_id,
        task.user_prompt,
        False
    )

    return task


@router.get("/{task_id}/stream")
async def stream_task_sse(task_id: str):
    """Server-Sent Events (SSE) streaming endpoint for live execution progress."""
    q: asyncio.Queue = asyncio.Queue()
    if task_id not in active_streams:
        active_streams[task_id] = []
    active_streams[task_id].append(q)

    async def event_generator():
        try:
            while True:
                msg = await q.get()
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("type") in ("task_finished", "task_failed", "task_cancelled"):
                    break
        finally:
            if task_id in active_streams and q in active_streams[task_id]:
                active_streams[task_id].remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.websocket("/{task_id}/ws")
async def task_websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for bidirectional real-time task streaming."""
    await websocket.accept()
    if task_id not in active_websockets:
        active_websockets[task_id] = []
    active_websockets[task_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Can receive cancel / query commands from client
            if data == "cancel":
                if task_id in active_orchestrators:
                    active_orchestrators[task_id].cancel_task(task_id)
    except WebSocketDisconnect:
        if task_id in active_websockets and websocket in active_websockets[task_id]:
            active_websockets[task_id].remove(websocket)
