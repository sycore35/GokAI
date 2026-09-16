"""
GÖK SYSTEMS TECH — Settings & AI Provider Governance API
Manages platform runtime governance, default models, sandbox mode, safety thresholds,
and secure AI provider configurations with live connectivity testing.
Never leaks raw secrets to the client.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

from gokai.apps.backend.app.schemas.dtos import (
    SettingsResponse,
    SettingsUpdate,
    ProviderStatusItem,
    ProviderTestRequest,
    ProviderTestResponse,
    ProviderSaveRequest,
)
from gokai.apps.backend.app.core.config import settings, _GOKAI_ROOT
from gokai.packages.model_router import ModelRouter, PROVIDER_CATALOG
from gokai.packages.shared.logger import get_logger

logger = get_logger("settings_api")
router = APIRouter(prefix="/settings", tags=["Settings"])


def mask_secret(secret: str) -> str:
    """Masks a secret key for safe UI display."""
    if not secret:
        return ""
    clean = secret.strip()
    if len(clean) <= 8:
        return "••••••••"
    return f"{clean[:4]}••••••••{clean[-4:]}"


def update_env_file(key: str, value: str):
    """Safely updates or inserts a key=value pair in .env file."""
    env_path = _GOKAI_ROOT / ".env"
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    key_found = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
            new_lines.append(f'{key}="{value}"')
            key_found = True
        else:
            new_lines.append(line)

    if not key_found:
        new_lines.append(f'{key}="{value}"')

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


@router.get("", response_model=SettingsResponse)
def get_settings():
    """Returns safe platform governance settings."""
    providers = []
    if settings.GEMINI_API_KEY.strip():
        providers.append("gemini")
    if settings.OPENAI_API_KEY.strip():
        providers.append("openai")
    if settings.DEEPSEEK_API_KEY.strip():
        providers.append("deepseek")
    if settings.ANTHROPIC_API_KEY.strip():
        providers.append("anthropic")
    if settings.NVIDIA_API_KEY.strip():
        providers.append("nvidia")
    if settings.OPENROUTER_API_KEY.strip():
        providers.append("openrouter")
    if not providers:
        providers.append("mock (offline development)")

    docker_present = shutil.which("docker") is not None

    return SettingsResponse(
        app_name=settings.APP_NAME,
        app_env=settings.APP_ENV,
        debug=settings.DEBUG,
        default_provider=settings.DEFAULT_PROVIDER,
        default_model=settings.DEFAULT_MODEL,
        fallback_provider=settings.FALLBACK_PROVIDER,
        fallback_model=settings.FALLBACK_MODEL,
        autonomy_level=settings.AUTONOMY_LEVEL,
        max_debug_cycles=settings.MAX_DEBUG_CYCLES,
        max_agent_calls=settings.MAX_AGENT_CALLS,
        max_task_cost_usd=settings.MAX_TASK_COST_USD,
        sandbox_backend=settings.SANDBOX_BACKEND,
        sandbox_timeout_seconds=settings.SANDBOX_TIMEOUT_SECONDS,
        docker_available=docker_present,
        active_providers=providers
    )


@router.put("", response_model=SettingsResponse)
def update_settings(payload: SettingsUpdate):
    """Updates runtime governance parameters."""
    if payload.default_provider is not None:
        settings.DEFAULT_PROVIDER = payload.default_provider
        update_env_file("DEFAULT_PROVIDER", payload.default_provider)
    if payload.default_model is not None:
        settings.DEFAULT_MODEL = payload.default_model
        update_env_file("DEFAULT_MODEL", payload.default_model)
    if payload.fallback_provider is not None:
        settings.FALLBACK_PROVIDER = payload.fallback_provider
        update_env_file("FALLBACK_PROVIDER", payload.fallback_provider)
    if payload.fallback_model is not None:
        settings.FALLBACK_MODEL = payload.fallback_model
        update_env_file("FALLBACK_MODEL", payload.fallback_model)
    if payload.autonomy_level is not None:
        settings.AUTONOMY_LEVEL = payload.autonomy_level
        update_env_file("AUTONOMY_LEVEL", payload.autonomy_level)
    if payload.max_debug_cycles is not None:
        settings.MAX_DEBUG_CYCLES = payload.max_debug_cycles
        update_env_file("MAX_DEBUG_CYCLES", str(payload.max_debug_cycles))

    return get_settings()


@router.get("/providers", response_model=List[ProviderStatusItem])
def list_providers():
    """Lists all supported AI providers with configuration status, masked keys, and model catalogs."""
    items = []
    for prov_id, meta in PROVIDER_CATALOG.items():
        env_key = meta.get("env_key")
        raw_key = getattr(settings, env_key, "") if env_key else ""
        has_key = bool(raw_key and raw_key.strip())
        is_active = (prov_id == settings.DEFAULT_PROVIDER)
        status = "configured" if (has_key or prov_id == "mock") else "not_configured"

        # Determine active model for this provider
        active_model = settings.DEFAULT_MODEL if is_active else meta.get("default_model", "")

        items.append(ProviderStatusItem(
            provider=prov_id,
            display_name=meta.get("display_name", prov_id.capitalize()),
            status=status,
            has_key=has_key or prov_id == "mock",
            masked_key=mask_secret(raw_key),
            active_model=active_model,
            models=meta.get("models", [])
        ))
    return items


@router.post("/providers/test", response_model=ProviderTestResponse)
async def test_provider_connection(payload: ProviderTestRequest):
    """Tests live connection to a provider with either an entered key or saved key."""
    prov_meta = PROVIDER_CATALOG.get(payload.provider)
    if not prov_meta and payload.provider != "mock":
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {payload.provider}")

    # Use supplied key or fallback to configured key
    api_key = payload.api_key
    if not api_key:
        env_key = prov_meta.get("env_key") if prov_meta else None
        if env_key:
            api_key = getattr(settings, env_key, "")

    model = payload.model or (prov_meta.get("default_model") if prov_meta else "mock-engineer-v1")

    router_inst = ModelRouter()
    success, msg, latency = await router_inst.test_connection(
        provider_name=payload.provider,
        api_key=api_key,
        model=model
    )
    return ProviderTestResponse(
        success=success,
        message=msg,
        latency_ms=latency
    )


@router.post("/providers/save", response_model=SettingsResponse)
def save_provider_config(payload: ProviderSaveRequest):
    """Saves provider API key and/or default model configuration."""
    prov_meta = PROVIDER_CATALOG.get(payload.provider)
    if not prov_meta and payload.provider != "mock":
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {payload.provider}")

    # Update API key if provided
    if payload.api_key is not None and prov_meta:
        env_key = prov_meta.get("env_key")
        if env_key:
            setattr(settings, env_key, payload.api_key.strip())
            os.environ[env_key] = payload.api_key.strip()
            update_env_file(env_key, payload.api_key.strip())

    # Update active model if provided
    if payload.model:
        settings.DEFAULT_MODEL = payload.model
        update_env_file("DEFAULT_MODEL", payload.model)

    # Set as default provider
    settings.DEFAULT_PROVIDER = payload.provider
    update_env_file("DEFAULT_PROVIDER", payload.provider)

    logger.info(f"Updated AI provider configuration for '{payload.provider}' (Model: '{settings.DEFAULT_MODEL}')")
    return get_settings()


@router.delete("/providers/{provider}", response_model=SettingsResponse)
def remove_provider_key(provider: str):
    """Clears API key for specified provider."""
    prov_meta = PROVIDER_CATALOG.get(provider)
    if not prov_meta:
        raise HTTPException(status_code=400, detail="Unknown provider")

    env_key = prov_meta.get("env_key")
    if env_key:
        setattr(settings, env_key, "")
        os.environ[env_key] = ""
        update_env_file(env_key, "")

    # If this was default provider, fallback to next available or mock
    if settings.DEFAULT_PROVIDER == provider:
        settings.DEFAULT_PROVIDER = "mock"
        settings.DEFAULT_MODEL = "mock-engineer-v1"
        update_env_file("DEFAULT_PROVIDER", "mock")
        update_env_file("DEFAULT_MODEL", "mock-engineer-v1")

    logger.info(f"Removed API key for provider '{provider}'")
    return get_settings()
