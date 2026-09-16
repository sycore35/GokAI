"""
GÖK SYSTEMS TECH — Backend Settings & Configuration
Loads environment variables and configuration using Pydantic Settings.
"""

from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine GökAI project root dynamically
_CURRENT_FILE = Path(__file__).resolve()
# Find the directory named 'gokai'
_GOKAI_ROOT = None
for p in [_CURRENT_FILE.parent, *_CURRENT_FILE.parents]:
    if p.name == "gokai" or (p / "packages").exists() and (p / "apps").exists():
        _GOKAI_ROOT = p
        break

if not _GOKAI_ROOT:
    _GOKAI_ROOT = _CURRENT_FILE.parents[4]


class Settings(BaseSettings):
    APP_NAME: str = "GökAI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Base workspace directory for generated projects
    PROJECTS_DIR: Path = _GOKAI_ROOT / "projects"
    SKILLS_DIR: Path = _GOKAI_ROOT / "skills"
    DATA_DIR: Path = _GOKAI_ROOT / "data"

    # Database
    DATABASE_URL: str = f"sqlite:///{(_GOKAI_ROOT / 'gokai.db').as_posix()}"

    # Model Provider Keys
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    NVIDIA_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    # Defaults
    DEFAULT_PROVIDER: str = "gemini"
    DEFAULT_MODEL: str = "gemini-2.5-flash"
    FALLBACK_PROVIDER: str = "openai"
    FALLBACK_MODEL: str = "gpt-4o-mini"
    MOCK_AI: bool = False

    # Safety & Autonomy Limits
    AUTONOMY_LEVEL: str = "balanced"
    MAX_AGENT_CALLS: int = 50
    MAX_DEBUG_CYCLES: int = 5
    MAX_TASK_COST_USD: float = 2.0
    MAX_DAILY_COST_USD: float = 25.0

    # Sandbox
    SANDBOX_BACKEND: str = "auto"
    SANDBOX_TIMEOUT_SECONDS: int = 120
    SANDBOX_MAX_MEMORY_MB: int = 2048

    # Network / CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=str(_GOKAI_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure directories exist
settings.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
settings.SKILLS_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
