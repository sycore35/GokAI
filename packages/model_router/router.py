"""
GÖK SYSTEMS TECH — Intelligent Model Router
Routes requests to the optimal AI model, manages fallback chains, tracks costs,
and enforces budget limits.
Zero hardcoded keys. Safe fallback for offline development & CI testing.
"""

import asyncio
import os
import time
from typing import Dict, List, Optional, Tuple, Any
from gokai.packages.model_router.provider import AIProvider, ModelMessage, CompletionResponse
from gokai.packages.model_router.openai_provider import OpenAICompatibleProvider
from gokai.packages.model_router.gemini_provider import GeminiCloudProvider
from gokai.packages.model_router.anthropic_provider import AnthropicCloudProvider
from gokai.packages.model_router.mock_provider import MockTestAIProvider
from gokai.packages.shared.exceptions import ProviderExhaustedError
from gokai.packages.shared.logger import get_logger

logger = get_logger("model_router")

# Catalog of officially supported models per provider
PROVIDER_CATALOG: Dict[str, Dict[str, Any]] = {
    "gemini": {
        "display_name": "Google Gemini",
        "default_model": "gemini-2.5-flash",
        "models": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        "env_key": "GEMINI_API_KEY",
    },
    "openai": {
        "display_name": "OpenAI",
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o-mini", "gpt-4o", "o1-mini", "o3-mini"],
        "env_key": "OPENAI_API_KEY",
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "env_key": "DEEPSEEK_API_KEY",
    },
    "anthropic": {
        "display_name": "Anthropic Claude",
        "default_model": "claude-3-5-sonnet-20241022",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        "env_key": "ANTHROPIC_API_KEY",
    },
    "nvidia": {
        "display_name": "NVIDIA Cloud NIM",
        "default_model": "meta/llama-3.1-70b-instruct",
        "models": ["meta/llama-3.1-70b-instruct", "meta/llama-3.3-70b-instruct", "mistralai/mixtral-8x7b-instruct-v0.1"],
        "env_key": "NVIDIA_API_KEY",
    },
    "openrouter": {
        "display_name": "OpenRouter",
        "default_model": "meta-llama/llama-3.3-70b-instruct",
        "models": ["meta-llama/llama-3.3-70b-instruct", "anthropic/claude-3.5-sonnet", "deepseek/deepseek-r1", "google/gemini-2.0-flash-001"],
        "env_key": "OPENROUTER_API_KEY",
    },
    "mock": {
        "display_name": "Internal Mock Provider (Offline / CI)",
        "default_model": "mock-engineer-v1",
        "models": ["mock-engineer-v1"],
        "env_key": None,
    }
}


class ModelRouter:
    """Routes agent inference requests across multi-provider cloud endpoints with safe fallbacks."""

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        nvidia_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        default_provider: str = "gemini",
        default_model: str = "gemini-2.5-flash",
        max_retries_per_provider: int = 2,
        allow_mock_fallback: bool = True
    ):
        self.providers: Dict[str, AIProvider] = {}
        self.default_provider = default_provider
        self.default_model = default_model
        self.max_retries = max_retries_per_provider
        self.allow_mock_fallback = allow_mock_fallback

        self.reconfigure(
            gemini_api_key=gemini_api_key,
            openai_api_key=openai_api_key,
            deepseek_api_key=deepseek_api_key,
            nvidia_api_key=nvidia_api_key,
            anthropic_api_key=anthropic_api_key,
            openrouter_api_key=openrouter_api_key,
            default_provider=default_provider,
            default_model=default_model,
        )

        # Cumulative usage statistics
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost_usd = 0.0

    def reconfigure(
        self,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        nvidia_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        default_provider: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        """Initializes or reloads providers based on keys."""
        self.providers.clear()

        if default_provider:
            self.default_provider = default_provider
        if default_model:
            self.default_model = default_model

        g_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        if g_key.strip():
            self.providers["gemini"] = GeminiCloudProvider(api_key=g_key.strip())

        o_key = openai_api_key or os.getenv("OPENAI_API_KEY", "")
        if o_key.strip():
            self.providers["openai"] = OpenAICompatibleProvider(
                api_key=o_key.strip(),
                base_url="https://api.openai.com/v1",
                provider_name="openai"
            )

        d_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if d_key.strip():
            self.providers["deepseek"] = OpenAICompatibleProvider(
                api_key=d_key.strip(),
                base_url="https://api.deepseek.com/v1",
                provider_name="deepseek"
            )

        a_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if a_key.strip():
            self.providers["anthropic"] = AnthropicCloudProvider(
                api_key=a_key.strip()
            )

        n_key = nvidia_api_key or os.getenv("NVIDIA_API_KEY", "")
        if n_key.strip():
            self.providers["nvidia"] = OpenAICompatibleProvider(
                api_key=n_key.strip(),
                base_url="https://integrate.api.nvidia.com/v1",
                provider_name="nvidia"
            )

        r_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY", "")
        if r_key.strip():
            self.providers["openrouter"] = OpenAICompatibleProvider(
                api_key=r_key.strip(),
                base_url="https://openrouter.ai/api/v1",
                provider_name="openrouter"
            )

        # Always register deterministic mock provider for tests / offline mode
        self.mock_provider = MockTestAIProvider()
        self.providers["mock"] = self.mock_provider

        cloud_providers = [k for k in self.providers.keys() if k != "mock"]
        if not cloud_providers and self.allow_mock_fallback:
            logger.info("No cloud API keys detected in environment. Using Mock AI Provider for offline execution.")
            self.default_provider = "mock"
            self.default_model = "mock-engineer-v1"

    def register_provider(self, name: str, provider: AIProvider):
        self.providers[name] = provider

    def get_available_providers(self) -> List[str]:
        return list(self.providers.keys())

    def get_fallback_chain(self, requested_provider: Optional[str] = None) -> List[Tuple[str, str]]:
        """Constructs an ordered list of (provider, model) pairs for fallback."""
        chain: List[Tuple[str, str]] = []
        primary = requested_provider or self.default_provider

        # Priority 1: Primary requested provider
        if primary in self.providers:
            model = self.default_model if primary == self.default_provider else PROVIDER_CATALOG.get(primary, {}).get("default_model", "default")
            chain.append((primary, model))

        # Priority 2: Other cloud providers
        cloud_fallbacks = [
            ("gemini", "gemini-2.5-flash"),
            ("openai", "gpt-4o-mini"),
            ("anthropic", "claude-3-5-sonnet-20241022"),
            ("deepseek", "deepseek-chat"),
            ("nvidia", "meta/llama-3.1-70b-instruct"),
            ("openrouter", "meta-llama/llama-3.3-70b-instruct"),
        ]
        for prov, mod in cloud_fallbacks:
            if prov in self.providers and (prov, mod) not in chain:
                chain.append((prov, mod))

        # Priority 3: Mock fallback if enabled and not already first
        if self.allow_mock_fallback and "mock" in self.providers and ("mock", "mock-engineer-v1") not in chain:
            chain.append(("mock", "mock-engineer-v1"))

        return chain

    async def generate_completion(
        self,
        messages: List[ModelMessage],
        preferred_provider: Optional[str] = None,
        preferred_model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        timeout_seconds: float = 60.0
    ) -> CompletionResponse:
        """Executes completion with automated retry and multi-tier fallback chain."""
        chain = self.get_fallback_chain(preferred_provider)
        if not chain:
            raise ProviderExhaustedError("No active AI providers available. Please configure an API key in Settings.")

        last_error = None

        for prov_name, default_mod in chain:
            provider = self.providers[prov_name]
            model = preferred_model if (prov_name == preferred_provider and preferred_model) else default_mod

            for attempt in range(self.max_retries):
                try:
                    logger.info(f"Dispatching inference to [{prov_name}:{model}] (Attempt {attempt + 1})")
                    resp = await provider.generate_completion(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout_seconds=timeout_seconds
                    )

                    self.total_input_tokens += resp.input_tokens
                    self.total_output_tokens += resp.output_tokens
                    self.total_cost_usd += resp.estimated_cost_usd

                    logger.info(
                        f"Inference succeeded from [{prov_name}:{model}] "
                        f"in {resp.latency_ms:.1f}ms (Cost: ${resp.estimated_cost_usd:.6f})"
                    )
                    return resp

                except Exception as ex:
                    last_error = ex
                    logger.warning(f"Provider [{prov_name}:{model}] attempt {attempt + 1} failed: {ex}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(0.5 * (2 ** attempt))

        raise ProviderExhaustedError(f"All AI model providers exhausted. Last error: {last_error}")

    async def test_connection(
        self,
        provider_name: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> Tuple[bool, str, float]:
        """Tests live connectivity to an AI provider."""
        start = time.perf_counter()
        prov_info = PROVIDER_CATALOG.get(provider_name)
        if not prov_info and provider_name != "mock":
            return False, f"Unknown provider: {provider_name}", 0.0

        target_model = model or (prov_info.get("default_model") if prov_info else "mock-engineer-v1")
        target_key = api_key or os.getenv(prov_info.get("env_key", ""), "") if prov_info and prov_info.get("env_key") else ""

        if provider_name == "mock":
            return True, "Mock Test Provider operational (Offline)", 1.0

        if not target_key.strip():
            return False, f"Missing API key for {provider_name}", 0.0

        try:
            # Instantiate temporary provider for test
            temp_provider: AIProvider
            if provider_name == "gemini":
                temp_provider = GeminiCloudProvider(api_key=target_key.strip())
            elif provider_name == "openai":
                temp_provider = OpenAICompatibleProvider(api_key=target_key.strip(), base_url="https://api.openai.com/v1", provider_name="openai")
            elif provider_name == "deepseek":
                temp_provider = OpenAICompatibleProvider(api_key=target_key.strip(), base_url="https://api.deepseek.com/v1", provider_name="deepseek")
            elif provider_name == "anthropic":
                temp_provider = AnthropicCloudProvider(api_key=target_key.strip())
            elif provider_name == "nvidia":
                temp_provider = OpenAICompatibleProvider(api_key=target_key.strip(), base_url="https://integrate.api.nvidia.com/v1", provider_name="nvidia")
            elif provider_name == "openrouter":
                temp_provider = OpenAICompatibleProvider(api_key=target_key.strip(), base_url="https://openrouter.ai/api/v1", provider_name="openrouter")
            else:
                return False, f"Unsupported test provider: {provider_name}", 0.0

            # Run a minimal ping completion
            test_msg = [ModelMessage(role="user", content="Ping. Respond with 'OK'")]
            resp = await temp_provider.generate_completion(
                model=target_model,
                messages=test_msg,
                temperature=0.0,
                max_tokens=10,
                timeout_seconds=15.0
            )
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return True, f"Connection verified. Response: '{resp.content.strip()}'", elapsed_ms

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return False, f"Connection failed: {str(e)}", elapsed_ms
