"""
GÖK SYSTEMS TECH — System Health Check Endpoint
"""

import shutil
from fastapi import APIRouter
from gokai.apps.backend.app.schemas.dtos import HealthResponse
from gokai.apps.backend.app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def get_system_health():
    """Returns platform runtime status, active providers, and sandbox capabilities."""
    providers = []
    if settings.GEMINI_API_KEY.strip():
        providers.append("gemini")
    if settings.OPENAI_API_KEY.strip():
        providers.append("openai")
    if settings.DEEPSEEK_API_KEY.strip():
        providers.append("deepseek")
    if settings.NVIDIA_API_KEY.strip():
        providers.append("nvidia")

    # If no cloud keys set, mock provider is available
    if not providers:
        providers.append("mock (offline development)")

    docker_present = shutil.which("docker") is not None

    return HealthResponse(
        status="healthy",
        version="1.0.0-alpha",
        database="connected",
        active_providers=providers,
        docker_available=docker_present,
        workspace_directory=str(settings.PROJECTS_DIR)
    )
