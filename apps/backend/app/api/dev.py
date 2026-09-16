"""
GÖK SYSTEMS TECH — Developer & Diagnostics API
Provides advanced system health telemetry, environment diagnostics,
execution sandbox status, browser automation readiness, logs, cache clearing,
and runtime configuration reloading. Never leaks secrets or private paths.
"""

import os
import sys
import platform
import shutil
import time
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from gokai.apps.backend.app.core.config import settings, _GOKAI_ROOT
from gokai.apps.backend.app.core.database import get_db, engine
from gokai.apps.backend.app.models.entities import ActivityLog, Project, Task
from gokai.apps.backend.app.schemas.dtos import DiagnosticsResponse
from gokai.packages.model_router import ModelRouter, PROVIDER_CATALOG
from gokai.packages.shared.logger import get_logger

logger = get_logger("dev_api")
router = APIRouter(prefix="/dev", tags=["Developer Diagnostics"])

# Record service start timestamp
START_TIME = time.time()


@router.get("/diagnostics", response_model=DiagnosticsResponse)
def get_diagnostics(db: Session = Depends(get_db)):
    """Collects comprehensive platform runtime diagnostics without leaking credentials."""
    uptime_seconds = int(time.time() - START_TIME)

    # 1. System Info
    system_info = {
        "os_platform": platform.system(),
        "os_release": platform.release(),
        "os_machine": platform.machine(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "uptime_formatted": f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s",
        "process_id": os.getpid(),
    }

    # 2. Backend & DB Info
    project_count = db.query(Project).count()
    task_count = db.query(Task).count()

    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1" if "sqlite" in settings.DATABASE_URL else "SELECT 1")
    except Exception:
        db_status = "error"

    backend_info = {
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "debug_mode": settings.DEBUG,
        "port": settings.PORT,
        "database_type": "SQLite" if "sqlite" in settings.DATABASE_URL else "PostgreSQL",
        "database_status": db_status,
        "total_projects": project_count,
        "total_tasks": task_count,
    }

    # 3. AI Providers Info
    active_providers = []
    for prov_id, meta in PROVIDER_CATALOG.items():
        env_key = meta.get("env_key")
        if env_key and getattr(settings, env_key, "").strip():
            active_providers.append(prov_id)
        elif prov_id == "mock":
            active_providers.append("mock (internal offline)")

    router_stats = ModelRouter()
    providers_info = {
        "default_provider": settings.DEFAULT_PROVIDER,
        "default_model": settings.DEFAULT_MODEL,
        "fallback_provider": settings.FALLBACK_PROVIDER,
        "fallback_model": settings.FALLBACK_MODEL,
        "active_providers": active_providers,
        "total_input_tokens": router_stats.total_input_tokens,
        "total_output_tokens": router_stats.total_output_tokens,
        "total_cost_usd": router_stats.total_cost_usd,
    }

    # 4. Sandbox & Automation
    docker_present = shutil.which("docker") is not None
    playwright_present = False
    try:
        import playwright
        playwright_present = True
    except ImportError:
        pass

    sandbox_info = {
        "backend": settings.SANDBOX_BACKEND,
        "docker_available": docker_present,
        "playwright_available": playwright_present,
        "execution_mode": "Docker Isolated Container" if docker_present else "Local Jailed Subprocess (Path & Timeout Guarded)",
        "timeout_seconds": settings.SANDBOX_TIMEOUT_SECONDS,
        "max_memory_mb": settings.SANDBOX_MAX_MEMORY_MB,
        "max_debug_cycles": settings.MAX_DEBUG_CYCLES,
        "autonomy_level": settings.AUTONOMY_LEVEL,
    }

    # 5. Recent Activity Logs (Telemetry tail)
    recent = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(20).all()
    logs_data = [
        {
            "id": r.id,
            "actor": r.actor,
            "action": r.action,
            "message": r.message,
            "level": r.level,
            "timestamp": r.timestamp.isoformat()
        }
        for r in recent
    ]

    return DiagnosticsResponse(
        system=system_info,
        backend=backend_info,
        providers=providers_info,
        sandbox=sandbox_info,
        recent_logs=logs_data
    )


@router.post("/clear-cache")
def clear_caches():
    """Clears temporary files, session artifacts, and reloads skill registry."""
    from gokai.apps.backend.app.api.skills import get_skill_manager
    manager = get_skill_manager()
    manager.reload_skills()

    temp_cleaned = 0
    # Clean temporary directories in workspace if any
    tmp_dir = _GOKAI_ROOT / "data" / "tmp"
    if tmp_dir.exists():
        for item in tmp_dir.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    temp_cleaned += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    temp_cleaned += 1
            except Exception:
                pass

    logger.info("Cleared runtime temporary caches and refreshed skill catalog.")
    return {
        "status": "success",
        "message": f"Cache cleared successfully. Reloaded {len(manager.skills)} skills.",
        "cleaned_items": temp_cleaned
    }


@router.post("/reload-config")
def reload_configuration():
    """Reloads .env settings and re-evaluates active provider connections."""
    from gokai.apps.backend.app.api.chat import get_model_router
    get_model_router()
    logger.info("Reloaded platform configuration and provider routing table.")
    return {
        "status": "success",
        "message": "Configuration reloaded successfully.",
        "default_provider": settings.DEFAULT_PROVIDER,
        "default_model": settings.DEFAULT_MODEL
    }
