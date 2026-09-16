# GÖKAI Model Router Specification

> **GÖK SYSTEMS TECH** — Multi-Provider AI Routing Core  
> **Status:** Standardized Architecture Specification  

---

## 1. Overview & Objectives

The **Model Router** is the intelligent gateway between GökAI's agents and cloud-hosted LLM APIs. GökAI **prohibits local LLM runtime dependencies** and instead leverages top-tier cloud model providers over standardized API interfaces.

### Core Objectives
1. **Provider Independence**: Zero lock-in to any single vendor (OpenAI, Google Gemini, DeepSeek, NVIDIA Cloud, Anthropic).
2. **Task-Specific Routing**: Match the right model tier to the right engineering task (reasoning vs. fast code generation vs. vision).
3. **Resilience & Fallback Chains**: Seamless automatic retry and secondary provider fallback during rate limits, outages, or HTTP errors.
4. **Economic & Resource Governance**: Fine-grained token counting, cost tracking, latency metrics, and hard budget enforcement.
5. **Secret Security**: Strict environment-variable isolation and automated masking of API credentials in all logs and outputs.

---

## 2. Multi-Provider Abstraction Architecture

```text
                               ┌────────────────────────┐
                               │     AGENT REQUEST      │
                               │  (Task, Context, Type) │
                               └───────────┬────────────┘
                                           │
                                           ▼
                               ┌────────────────────────┐
                               │   TASK CLASSIFIER &    │
                               │    ROUTER ENGINE       │
                               └───────────┬────────────┘
                                           │
                ┌──────────────────────────┼──────────────────────────┐
                ▼                          ▼                          ▼
       ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
       │   PRIMARY TIER  │        │  FALLBACK TIER  │        │   EMERGENCY     │
       │  (e.g., Gemini) │        │ (e.g., DeepSeek)│        │ (e.g., OpenAI)  │
       └────────┬────────┘        └────────┬────────┘        └────────┬────────┘
                │                          │                          │
                └──────────────────────────┼──────────────────────────┘
                                           │
                                           ▼
                               ┌────────────────────────┐
                               │   UNIFIED PROVIDER     │
                               │       INTERFACE        │
                               └───────────┬────────────┘
                                           │
                 ┌─────────────────────────┼─────────────────────────┐
                 ▼                         ▼                         ▼
         ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
         │ GeminiClient  │         │ OpenAIClient  │         │ DeepSeekClient│
         └───────────────┘         └───────────────┘         └───────────────┘
```

### 2.1. Provider Protocol Interface (`AIProvider`)

All provider implementations conform to the unified asynchronous protocol:

```python
from typing import AsyncGenerator, Protocol, List, Optional
from pydantic import BaseModel

class ModelMessage(BaseModel):
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None

class CompletionResponse(BaseModel):
    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    estimated_cost_usd: float
    finish_reason: str

class AIProvider(Protocol):
    """Unified protocol for external AI cloud providers."""
    
    provider_name: str
    
    async def generate_completion(
        self,
        model: str,
        messages: List[ModelMessage],
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        timeout_seconds: float = 60.0
    ) -> CompletionResponse: ...
    
    async def stream_completion(
        self,
        model: str,
        messages: List[ModelMessage],
        temperature: float = 0.2
    ) -> AsyncGenerator[str, None]: ...
    
    async def check_health(self) -> bool: ...
```

---

## 3. Dynamic Model Matrix

The Model Router dynamically categorizes tasks into specialized capabilities:

| Capability Tier | Typical Tasks | Primary Candidates | Fallback Candidates | Max Latency |
| :--- | :--- | :--- | :--- | :--- |
| **Reasoning & Planning** | Architecture design, task DAG, debugging complex crashes | `gemini-2.5-pro`, `o3-mini`, `deepseek-r1` | `claude-3-7-sonnet`, `gpt-4o` | 90s |
| **High-Volume Coding** | Scaffolding, writing endpoints, creating test suites | `deepseek-coder-v2`, `gemini-2.5-flash`, `gpt-4o` | `qwen-2.5-coder-32b` | 45s |
| **Fast Summaries & Routing**| Task classification, skill matching, commit summaries | `gemini-2.5-flash`, `gpt-4o-mini` | `deepseek-chat` | 10s |
| **Multimodal / Vision** | UI screenshot audit, layout inspection, design review | `gemini-2.5-flash`, `gpt-4o` | `claude-3-5-sonnet` | 30s |

---

## 4. Resilience & Fallback Engine

If a provider fails due to network disconnection, HTTP 429 (Rate Limit), or HTTP 5xx (Server Error), the Model Router triggers an exponential backoff retry and subsequent provider failover:

```python
class ModelRouter:
    async def execute_with_fallback(
        self,
        task_type: str,
        messages: List[ModelMessage]
    ) -> CompletionResponse:
        route_config = self.get_route(task_type)
        last_exception = None
        
        for provider_name, model_name in route_config.chain:
            provider = self.get_provider(provider_name)
            for attempt in range(route_config.max_retries_per_provider):
                try:
                    return await provider.generate_completion(
                        model=model_name,
                        messages=messages,
                        timeout_seconds=route_config.timeout
                    )
                except (RateLimitError, ProviderServerError, NetworkError) as e:
                    last_exception = e
                    await asyncio.sleep(2 ** attempt * 0.5)  # Exponential backoff
            # Failed all retries for this provider -> fallback to next in chain
            
        raise AllProvidersExhaustedError(f"Routing failed: {last_exception}")
```

---

## 5. Cost Tracking & Governance

Each completion computes estimated financial costs based on current pricing tables:

$$\text{Cost} = (\text{Input Tokens} \times \text{Price}_{\text{in}}) + (\text{Output Tokens} \times \text{Price}_{\text{out}})$$

### Hard Budget Enforcements:
- `MAX_TASK_COST_USD` (Default: $2.00): Halts task execution and queries user for confirmation if exceeded.
- `MAX_DAILY_COST_USD` (Default: $25.00): Prevents runaway automated development loops.
- `MAX_AGENT_CALLS_PER_TASK` (Default: 50): Hard ceiling preventing infinite agent loops.

---

## 6. Secret Security & Redaction

- **Environment-Only Secrets**: API keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `NVIDIA_API_KEY`) are read strictly from `.env` or system environment variables.
- **Log Masking**: Any string matching known key patterns (e.g., `sk-[a-zA-Z0-9]{32,}`, `AIza[0-9A-Za-z-_]{35}`) is automatically scrubbed to `[REDACTED_API_KEY]` prior to writing to logs or emitting over WebSockets.
