"""
GÖK SYSTEMS TECH — Anthropic Cloud AI Provider
Supports Claude 3.5 Sonnet, Claude 3.5 Haiku, and standard Anthropic /v1/messages APIs.
"""

import time
import httpx
from typing import List, Optional, AsyncGenerator
from gokai.packages.model_router.provider import AIProvider, ModelMessage, CompletionResponse
from gokai.packages.shared.logger import get_logger

logger = get_logger("anthropic_provider")


class AnthropicCloudProvider:
    """Adapter for Anthropic REST API endpoints."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com/v1",
        provider_name: str = "anthropic"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.provider_name = provider_name

    async def generate_completion(
        self,
        model: str,
        messages: List[ModelMessage],
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        timeout_seconds: float = 60.0
    ) -> CompletionResponse:
        start_time = time.perf_counter()
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        system_prompt = ""
        user_assistant_messages = []
        for m in messages:
            if m.role == "system":
                system_prompt += f"{m.content}\n"
            else:
                user_assistant_messages.append({
                    "role": m.role if m.role in ("user", "assistant") else "user",
                    "content": m.content
                })

        if not user_assistant_messages:
            user_assistant_messages.append({"role": "user", "content": "Hello"})

        payload = {
            "model": model or "claude-3-5-sonnet-20241022",
            "messages": user_assistant_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature
        }
        if system_prompt.strip():
            payload["system"] = system_prompt.strip()

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(f"{self.base_url}/messages", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = data.get("usage", {})
        in_tokens = usage.get("input_tokens", 0)
        out_tokens = usage.get("output_tokens", 0)

        # Cost estimation: $3.00/M in, $15.00/M out (Sonnet estimate)
        estimated_cost = (in_tokens * 0.000003) + (out_tokens * 0.000015)

        return CompletionResponse(
            content=content,
            provider=self.provider_name,
            model=model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            latency_ms=latency_ms,
            estimated_cost_usd=estimated_cost,
            finish_reason=data.get("stop_reason", "stop") or "stop"
        )

    async def stream_completion(
        self,
        model: str,
        messages: List[ModelMessage],
        temperature: float = 0.2
    ) -> AsyncGenerator[str, None]:
        resp = await self.generate_completion(model, messages, temperature)
        yield resp.content

    async def check_health(self) -> bool:
        if not self.api_key:
            return False
        try:
            # Send minimal validation request
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "claude-3-5-haiku-20241022",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 5
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{self.base_url}/messages", json=payload, headers=headers)
                return resp.status_code in (200, 400) # If status 200 or auth passed
        except Exception:
            return False
