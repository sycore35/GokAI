"""
GÖK SYSTEMS TECH — Unified AI Provider Protocol
Defines the standard interface that all cloud LLM adapters must implement.
"""

from typing import Protocol, List, Optional, AsyncGenerator
from pydantic import BaseModel, Field


class ModelMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None


class CompletionResponse(BaseModel):
    content: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    finish_reason: str = "stop"


class AIProvider(Protocol):
    """Protocol for external AI model cloud API integrations."""

    provider_name: str

    async def generate_completion(
        self,
        model: str,
        messages: List[ModelMessage],
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        timeout_seconds: float = 60.0
    ) -> CompletionResponse:
        """Executes non-streaming completion."""
        ...

    async def stream_completion(
        self,
        model: str,
        messages: List[ModelMessage],
        temperature: float = 0.2
    ) -> AsyncGenerator[str, None]:
        """Streams text chunks as they are emitted."""
        ...

    async def check_health(self) -> bool:
        """Verifies API key validity and network reachability."""
        ...
