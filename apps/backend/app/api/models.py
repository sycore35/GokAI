"""
GÖK SYSTEMS TECH — Models & Cost Tracking API
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from gokai.apps.backend.app.core.config import settings

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("/status", response_model=Dict[str, Any])
def get_model_status():
    providers = []
    if settings.GEMINI_API_KEY:
        providers.append({"name": "gemini", "model": "gemini-2.5-flash", "status": "active"})
    if settings.OPENAI_API_KEY:
        providers.append({"name": "openai", "model": "gpt-4o-mini", "status": "active"})
    if settings.DEEPSEEK_API_KEY:
        providers.append({"name": "deepseek", "model": "deepseek-chat", "status": "active"})
    if settings.NVIDIA_API_KEY:
        providers.append({"name": "nvidia", "model": "meta/llama-3.1-70b-instruct", "status": "active"})

    return {
        "default_provider": settings.DEFAULT_PROVIDER,
        "default_model": settings.DEFAULT_MODEL,
        "available_providers": providers
    }
