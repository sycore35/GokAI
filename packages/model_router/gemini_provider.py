"""
GÖK SYSTEMS TECH — Google Gemini Cloud API Adapter
Provides independent cloud inference via standard Google Generative Language REST APIs.
Zero Antigravity SDK or local agent dependency.
"""

import time
import httpx
from typing import List, Optional, AsyncGenerator
from gokai.packages.model_router.provider import AIProvider, ModelMessage, CompletionResponse
from gokai.packages.shared.logger import get_logger

logger = get_logger("gemini_provider")


class GeminiCloudProvider:
    """Independent adapter for Google Gemini REST API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.provider_name = "gemini"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_completion(
        self,
        model: str,
        messages: List[ModelMessage],
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        timeout_seconds: float = 60.0
    ) -> CompletionResponse:
        start_time = time.perf_counter()

        # Format Gemini contents payload
        contents = []
        system_instruction = None

        for m in messages:
            if m.role == "system":
                system_instruction = {"parts": [{"text": m.content}]}
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": m.content}]
                })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        candidates = data.get("candidates", [])
        if not candidates:
            content = ""
            finish_reason = "empty"
        else:
            first = candidates[0]
            parts = first.get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts)
            finish_reason = first.get("finishReason", "stop")

        usage = data.get("usageMetadata", {})
        in_tokens = usage.get("promptTokenCount", 0)
        out_tokens = usage.get("candidatesTokenCount", 0)

        # Standard Gemini Flash estimation ($0.075/M in, $0.30/M out)
        estimated_cost = (in_tokens * 0.000000075) + (out_tokens * 0.0000003)

        return CompletionResponse(
            content=content,
            provider=self.provider_name,
            model=model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            latency_ms=latency_ms,
            estimated_cost_usd=estimated_cost,
            finish_reason=finish_reason
        )

    async def stream_completion(
        self,
        model: str,
        messages: List[ModelMessage],
        temperature: float = 0.2
    ) -> AsyncGenerator[str, None]:
        # Fallback to standard completion chunking for reliable transport
        resp = await self.generate_completion(model, messages, temperature)
        yield resp.content

    async def check_health(self) -> bool:
        if not self.api_key:
            return False
        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                return resp.status_code == 200
        except Exception:
            return False
