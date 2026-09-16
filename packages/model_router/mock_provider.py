"""
GÖK SYSTEMS TECH — Mock AI Provider for Automated Testing & CI
Simulates cloud model completion specifically for unit and integration testing.
Zero API cost, deterministic outputs.
"""

import sys
from pathlib import Path
from typing import List, Optional, AsyncGenerator

# Ensure gokai package root is in sys.path
_current = Path(__file__).resolve()
for parent in _current.parents:
    if (parent / "gokai").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

try:
    from gokai.packages.model_router.provider import AIProvider, ModelMessage, CompletionResponse
except ImportError:
    from packages.model_router.provider import AIProvider, ModelMessage, CompletionResponse


class MockTestAIProvider(AIProvider):
    """Deterministic AI provider for testing orchestration pipelines without cloud API credits."""

    provider_name = "mock_test_provider"

    def __init__(self):
        self.call_count = 0

    async def generate_completion(
        self,
        model: str,
        messages: List[ModelMessage],
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        timeout_seconds: float = 60.0
    ) -> CompletionResponse:
        self.call_count += 1
        prompt = messages[-1].content if messages else ""

        # Deterministic responses for testing
        if "calculator" in prompt.lower():
            content = (
                "=== FILE: calculator.py ===\n"
                "```python\n"
                "class Calculator:\n"
                "    def add(self, a: float, b: float) -> float:\n"
                "        return a + b\n\n"
                "    def subtract(self, a: float, b: float) -> float:\n"
                "        return a - b\n\n"
                "    def multiply(self, a: float, b: float) -> float:\n"
                "        return a * b\n\n"
                "    def divide(self, a: float, b: float) -> float:\n"
                "        if b == 0:\n"
                "            raise ValueError('Cannot divide by zero')\n"
                "        return a / b\n"
                "```\n\n"
                "=== FILE: test_calculator.py ===\n"
                "```python\n"
                "import pytest\n"
                "from calculator import Calculator\n\n"
                "def test_calculator_operations():\n"
                "    calc = Calculator()\n"
                "    assert calc.add(2, 3) == 5\n"
                "    assert calc.subtract(10, 4) == 6\n"
                "    assert calc.multiply(3, 7) == 21\n"
                "    assert calc.divide(8, 2) == 4\n\n"
                "def test_divide_by_zero():\n"
                "    calc = Calculator()\n"
                "    with pytest.raises(ValueError):\n"
                "        calc.divide(5, 0)\n"
                "```\n"
            )
        elif "todo" in prompt.lower() or "fastapi" in prompt.lower():
            content = (
                "=== FILE: main.py ===\n"
                "```python\n"
                "from fastapi import FastAPI, HTTPException\n"
                "from pydantic import BaseModel\n"
                "from typing import List, Optional\n\n"
                "app = FastAPI(title='Todo API')\n\n"
                "class TodoItem(BaseModel):\n"
                "    id: int\n"
                "    title: str\n"
                "    completed: bool = False\n\n"
                "todos: List[TodoItem] = []\n\n"
                "@app.get('/todos', response_model=List[TodoItem])\n"
                "def list_todos():\n"
                "    return todos\n\n"
                "@app.post('/todos', response_model=TodoItem, status_code=201)\n"
                "def create_todo(item: TodoItem):\n"
                "    todos.append(item)\n"
                "    return item\n"
                "```\n\n"
                "=== FILE: test_main.py ===\n"
                "```python\n"
                "import pytest\n"
                "from fastapi.testclient import TestClient\n"
                "from main import app\n\n"
                "client = TestClient(app)\n\n"
                "def test_create_and_list_todos():\n"
                "    res = client.post('/todos', json={'id': 1, 'title': 'Test Todo', 'completed': False})\n"
                "    assert res.status_code == 201\n"
                "    list_res = client.get('/todos')\n"
                "    assert list_res.status_code == 200\n"
                "    assert len(list_res.json()) >= 1\n"
                "```\n"
            )
        else:
            content = (
                "=== FILE: main.py ===\n"
                "```python\n"
                "def main():\n"
                "    print('Hello from GökAI Autonomous Platform')\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
                "```\n\n"
                "=== FILE: test_main.py ===\n"
                "```python\n"
                "from main import main\n\n"
                "def test_main():\n"
                "    main()\n"
                "    assert True\n"
                "```\n"
            )

        return CompletionResponse(
            content=content,
            provider="mock",
            model="mock-engineer-v1",
            input_tokens=150,
            output_tokens=320,
            latency_ms=12.5,
            estimated_cost_usd=0.0001,
            finish_reason="stop"
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
        return True


if __name__ == "__main__":
    import asyncio

    async def _test():
        provider = MockTestAIProvider()
        msg = ModelMessage(role="user", content="Create a python calculator")
        res = await provider.generate_completion("mock", [msg])
        print("Mock Provider Test Succeeded:")
        print(f"Provider: {res.provider} | Model: {res.model} | Latency: {res.latency_ms:.1f}ms")
        print(f"Content preview: {res.content[:80]}...")

    asyncio.run(_test())
