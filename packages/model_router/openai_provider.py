"""
GÖK SYSTEMS TECH — OpenAI-Compatible Cloud AI Provider
Supports OpenAI, DeepSeek, NVIDIA Cloud, and standard /v1/chat/completions APIs.
"""

import time
import httpx
from typing import List, Optional, AsyncGenerator
from gokai.packages.model_router.provider import AIProvider, ModelMessage, CompletionResponse
from gokai.packages.shared.logger import get_logger

logger = get_logger("openai_provider")


class OpenAICompatibleProvider:
    """Adapter for OpenAI-compatible REST API endpoints."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        provider_name: str = "openai"
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
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        choice = data["choices"][0]
        content = choice["message"]["content"] or ""
        usage = data.get("usage", {})
        in_tokens = usage.get("prompt_tokens", 0)
        out_tokens = usage.get("completion_tokens", 0)

        # Estimate cost (rough benchmark: $0.15/M in, $0.60/M out for standard models)
        estimated_cost = (in_tokens * 0.00000015) + (out_tokens * 0.0000006)

        return CompletionResponse(
            content=content,
            provider=self.provider_name,
            model=model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            latency_ms=latency_ms,
            estimated_cost_usd=estimated_cost,
            finish_reason=choice.get("finish_reason", "stop")
        )

    async def stream_completion(
        self,
        model: str,
        messages: List[ModelMessage],
        temperature: float = 0.2
    ) -> AsyncGenerator[str, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_url}/chat/completions", json=payload, headers=headers) as resp:
                resp.raise_for_status()
                import json
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        body = line[6:].strip()
                        if body == "[DONE]":
                            break
                        try:
                            chunk = json.loads(body)
                            delta = chunk["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue

    async def check_health(self) -> bool:
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                return resp.status_code == 200
        except Exception:
            return False
