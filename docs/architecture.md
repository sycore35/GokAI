# GÖKAI Architecture Specification

> **GÖK SYSTEMS TECH** — Autonomous Multi-Agent AI Software Engineering Platform  
> **Version:** 1.0.0-draft  
> **Status:** Approved Architectural Blueprint  

---

## 1. Executive Summary & Philosophy

**GökAI** is a production-grade, autonomous multi-agent AI software engineering platform engineered by **GÖK SYSTEMS TECH**. It translates natural language user directives into fully functional, tested, verified, and maintainable software systems.

Unlike simplistic code completion tools or mock demonstration interfaces, GökAI operates on an industrial engineering lifecycle:

$$\text{ANALYZE} \longrightarrow \text{PLAN} \longrightarrow \text{RESEARCH} \longrightarrow \text{IMPLEMENT} \longrightarrow \text{RUN} \longrightarrow \text{TEST} \longrightarrow \text{DEBUG} \longrightarrow \text{REVIEW} \longrightarrow \text{DELIVER}$$

### Core Tenet: Complete Runtime Independence
GökAI is engineered to be **100% independent of Google Antigravity or any proprietary IDE runtime**. 
- Antigravity serves strictly as the development workbench used to build GökAI.
- When deployed or executed by end-users, GökAI runs as an independent local or server system consisting of its own Web UI, FastAPI backend, autonomous Orchestrator, multi-agent pool, sandboxed execution environment, hierarchical memory, and multi-provider AI gateway.

---

## 2. High-Level Architecture Diagram

```text
                                 ┌────────────────────────┐
                                 │       END USER         │
                                 └───────────┬────────────┘
                                             │
                                             ▼
                                 ┌────────────────────────┐
                                 │     GÖKAI WEB UI       │
                                 │  Next.js 15 / React 19 │
                                 │  Tailwind CSS / Radix  │
                                 └───────────┬────────────┘
                                             │ HTTP REST + SSE / WebSockets
                                             ▼
                     ┌────────────────────────────────────────────────┐
                     │              API GATEWAY (FastAPI)              │
                     │  Auth, Rate Limits, Project & Task Endpoints   │
                     └───────────────────────┬────────────────────────┘
                                             │
                                             ▼
                     ┌────────────────────────────────────────────────┐
                     │            ORCHESTRATOR ENGINE                 │
                     │  Task Decomposition (DAG), State Machine,      │
                     │  Dependency Resolver, Human-in-the-Loop Gates  │
                     └───────┬───────────────────────────────┬────────┘
                             │                               │
            ┌────────────────┴───────────────┐               │
            ▼                                ▼               ▼
┌───────────────────────┐        ┌───────────────────────┐ ┌───────────────────────┐
│     AGENT RUNTIME     │        │     MODEL ROUTER      │ │   MEMORY & DATABASE   │
│  - Researcher         │        │  - Provider Router    │ │  - Level 1: Facts     │
│  - Developer          │◄──────►│  - Gemini / OpenAI /  │ │  - Level 2: Decisions │
│  - Tester             │        │    DeepSeek / NVIDIA  │ │  - Level 3: History   │
│  - Debugger           │        │  - Token / Cost Track │ │  - Level 4: Tasks     │
│  - UI / Design (PW)   │        │  - Fallback & Retry   │ │  - SQLite / Postgres  │
│  - Security           │        └───────────────────────┘ └───────────────────────┘
│  - Reviewer / Docs    │
└───────────┬───────────┘
            │ Tool Calls
            ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          TOOL REGISTRY & BUS                           │
│  FileSystemTool (Jailed)  |  TerminalTool (Sandboxed)  |  BrowserTool  │
│  WebSearchTool (Anti-Inj) |  CodeSearchTool            |  DiffEngine   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       ISOLATED EXECUTION LAYER                         │
│   Docker Sandbox Container  (Fallback: OS Process Jail w/ Quotas)      │
│   Strict CPU/RAM limits, Timeout Guard, No Host Path Traversal         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        PROJECT WORKSPACE STORE                         │
│   /workspace/projects/{project_id}/ (Source, Tests, Snapshots, ZIP)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Subsystems

### 3.1. API Gateway & Web Interface
- **Frontend (`apps/frontend`)**: Built with React, TypeScript, and modern component architecture (Next.js / Vite). Provides real-time activity streams, interactive task graphs, code editors with syntax highlighting, diff visualizers, browser screenshot previews, and cost/token analytics.
- **Backend (`apps/backend`)**: Asynchronous FastAPI service offering clean RESTful endpoints, SSE (Server-Sent Events) and WebSocket channels for streaming agent progress, token usage, logs, and interactive approval gates.

### 3.2. Orchestrator Engine (`packages/orchestrator`)
The Orchestrator is the central executive brain:
1. Deconstructs ambiguous user tasks into a Directed Acyclic Graph (DAG) of actionable subtasks (`TaskStep`).
2. Dispatches subtasks to specialized agents based on capability matrices.
3. Enforces deterministic state transitions (`QUEUED` $\to$ `PLANNING` $\to$ `EXECUTING` $\to$ `TESTING` $\to$ `DEBUGGING` $\to$ `REVIEWING` $\to$ `COMPLETED`).
4. Implements the **Self-Healing Loop**: when tests or builds fail, it routes diagnostic evidence to the Debugger Agent, applies minimal targeted patches, and re-triggers tests until passing (up to a configurable maximum cycle count, e.g., 5).

### 3.3. Multi-Provider Model Router (`packages/model_router`)
Abstracts AI inference across diverse cloud model providers:
- Supports OpenAI, Google Gemini, DeepSeek, NVIDIA Cloud, and generic OpenAI-compatible APIs.
- Routes tasks dynamically:
  - Complex reasoning & architecture $\to$ Frontier reasoning models.
  - High-volume code generation $\to$ Code-specialized models.
  - Fast summarization & classification $\to$ Low-latency, cost-effective models.
  - UI visual inspection $\to$ Vision-enabled multimodal models.
- Tracks input/output tokens, latency, cost per invocation, and handles automatic fallback if a primary provider experiences downtime or rate limits.

### 3.4. Agent Runtime (`packages/agents`)
Autonomous specialists adhering to a strict `BaseAgent` interface. Agents do not exchange free-form chatter; they interact via structured, type-validated JSON envelopes containing artifacts, status flags, and structured logs.

### 3.5. Tool Registry & Jailed Execution (`packages/tools` & `packages/sandbox`)
- Every tool is managed by a centralized `ToolRegistry` with granular permission checks (`filesystem.read`, `filesystem.write`, `terminal.execute`, `browser.open`, `network.request`).
- Code execution is executed within an isolated Docker sandbox container (with an OS-level isolated subprocess fallback for machines without Docker). Host filesystem access outside the project workspace is strictly prohibited.

### 3.6. Hierarchical Memory & Project State (`packages/memory`)
Prevents context window saturation through 4 distinct abstraction tiers:
1. **Level 1 — Project Facts**: Core stack, framework versions, ports, and architectural conventions.
2. **Level 2 — Architectural Decisions**: Explicit technical choices and recorded trade-offs.
3. **Level 3 — Significant Evolution**: Changelogs, schema migrations, and structural modifications.
4. **Level 4 — Task Summaries**: Compact history of completed tasks and test results.

---

## 4. Key Architectural Guarantees

1. **Deterministic Verification**: No task is marked `COMPLETED` based on LLM declaration alone. It requires passing build scripts, successful automated tests, or validated visual screenshots.
2. **Zero Auto-GitHub**: No remote repository commits or pushes occur automatically. GökAI generates full project source trees, local git histories (optional), and clean ZIP export packages.
3. **Secret Redaction**: API keys and environment variables are strictly managed in local configuration and filtered from all agent prompt logs, activity streams, and client-facing responses.
4. **Stateful Artifacts**: Every code file, test report, research summary, and screenshot is recorded as a versioned `Artifact` associated with the project and task.
