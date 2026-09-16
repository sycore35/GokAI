"""
GÖK SYSTEMS TECH — GökAI Backend Main Application
High-performance asynchronous FastAPI service.
Zero Antigravity runtime dependency.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gokai.apps.backend.app.core.config import settings
from gokai.apps.backend.app.core.database import Base, engine, run_migrations
from gokai.apps.backend.app.api import (
    health,
    projects,
    tasks,
    agents,
    skills,
    models,
    memory,
    settings as settings_api,
    activity,
    chat,
    dev,
)
from gokai.packages.shared.logger import get_logger

logger = get_logger("main_app")

# Initialize and migrate database schema
run_migrations()

app = FastAPI(
    title="GökAI API Gateway",
    description="Autonomous Multi-Agent AI Software Engineering Platform — GÖK SYSTEMS TECH",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api")
app.include_router(activity.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(dev.router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "detail": str(exc)}
    )


@app.get("/")
def root_status():
    return {
        "platform": "GÖKAI",
        "organization": "GÖK SYSTEMS TECH",
        "status": "online",
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gokai.apps.backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
