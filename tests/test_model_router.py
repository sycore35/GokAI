"""
Tests for ModelRouter, multi-provider fallback chains, and mock provider integration.
"""

import asyncio
import pytest
from gokai.packages.model_router.router import ModelRouter
from gokai.packages.model_router.provider import ModelMessage
from gokai.packages.model_router.mock_provider import MockTestAIProvider


def test_model_router_fallback_and_completion():
    async def _run():
        router = ModelRouter(allow_mock_fallback=True)
        assert "mock" in router.get_available_providers()

        messages = [
            ModelMessage(role="user", content="Create a python calculator CLI")
        ]

        resp = await router.generate_completion(messages=messages)
        assert resp is not None
        assert resp.provider == "mock"
        assert "calculator.py" in resp.content
        assert resp.latency_ms > 0
        assert router.total_input_tokens > 0

    asyncio.run(_run())


def test_model_router_custom_provider_registration():
    router = ModelRouter(allow_mock_fallback=False)
    custom_mock = MockTestAIProvider()
    router.register_provider("custom", custom_mock)
    assert "custom" in router.get_available_providers()
