# GÖKAI V1 — Autonomous Multi-Agent AI Software Engineering Platform

> **GÖK SYSTEMS TECH — Enterprise Autonomous Engineering Core**  
> **Version:** 1.0.0 (GökAI V1)  
> **Status:** Production-Ready Independent Release  
> **License:** MIT  

---

## 🌟 What is GökAI?

**GökAI** is a standalone, fully autonomous multi-agent AI software engineering platform. It transforms natural language objectives into verified, production-grade codebases by orchestrating specialized AI agents across the entire software development lifecycle:

1. **Planning & Architecture Decomposition**: Generates structured Directed Acyclic Graph (DAG) task execution plans.
2. **Specialist Multi-Agent Execution**: Deploys dedicated Researcher, Developer, Tester, Debugger, Security, and Reviewer agents.
3. **Isolated Sandboxing**: Executes code and bash commands within safe, jailed environments (`JailedFileSystem` preventing directory escape, `SandboxedTerminal` enforcing timeouts and resource limits, and optional Docker container isolation).
4. **Self-Healing Test-Driven Debugger**: Executes actual test runners (`pytest`, `unittest`, `npm test`), intercepts failure stack traces, and iterates through automated self-repair cycles until test suites pass.
5. **Security & Vulnerability Auditing**: Automatically inspects source code for hardcoded secrets, injection vectors, and OWASP vulnerabilities.
6. **Delivery & Package Export**: Bundles deliverables into clean, exportable ZIP archives.

### 🛑 100% Independent Runtime
GökAI is **100% runtime-independent of Google Antigravity or any external proprietary IDE**. It operates completely standalone on Windows, macOS, and Linux.

---

## 🏗️ System Architecture

```text
                               ┌───────────────────────────────┐
                               │          USER PROMPT          │
                               └───────────────┬───────────────┘
                                               │
                                               ▼
                               ┌───────────────────────────────┐
                               │     GÖKAI REACT 19 WEB UI     │
                               │  (Dashboard, Chat, D-Menu)    │
                               └───────────────┬───────────────┘
                                               │ HTTP REST / SSE
                                               ▼
                               ┌───────────────────────────────┐
                               │   FASTAPI API GATEWAY (8000)  │
                               └───────────────┬───────────────┘
                                               │
                                               ▼
                               ┌───────────────────────────────┐
                               │      ORCHESTRATOR ENGINE      │
                               │  (Task DAG & State Machine)   │
                               └───────┬───────┬───────┬───────┘
                                       │       │       │
                      ┌────────────────┘       │       └────────────────┐
                      ▼                        ▼                        ▼
         ┌─────────────────────────┐ ┌───────────────────┐ ┌────────────────────────┐
         │      MODEL ROUTER       │ │   DOMAIN SKILLS   │ │  HIERARCHICAL MEMORY   │
         │ (Gemini, OpenAI, Claude,│ │ (FastAPI, Python, │ │ (Tier 1: Truths/Ports  │
         │  DeepSeek, Nvidia, Mock)│ │  React, Security) │ │  Tier 2: Decisions     │
         └────────────┬────────────┘ └─────────┬─────────┘ │  Tier 3: Milestones    │
                      │                        │           │  Tier 4: Task History) │
                      ▼                        ▼           └────────────┬───────────┘
         ┌──────────────────────────────────────────────────────────────▼───────────┐
         │                          SPECIALIST AGENT POOL                           │
         │  • Developer Agent  • Tester Agent  • Debugger Agent (Self-Healing Loop) │
         │  • Security Agent   • Reviewer Agent • Researcher Agent                  │
         └─────────────────────────────────────┬────────────────────────────────────┘
                                               │
                                               ▼
         ┌──────────────────────────────────────────────────────────────────────────┐
         │                     ISOLATED EXECUTION JAILED LAYER                      │
         │  • JailedFileSystem (Path-traversal proof, CRUD, edit, diffs, ZIP)       │
         │  • SandboxedTerminal (Process timeout, resource limits, exit inspection) │
         │  • Headless BrowserTool (DOM / Console verification)                     │
         │  • Docker Container Sandbox (Optional automated detection)               │
         └─────────────────────────────────────┬────────────────────────────────────┘
                                               │
                                               ▼
         ┌──────────────────────────────────────────────────────────────────────────┐
         │                        ISOLATED PROJECT WORKSPACE                        │
         │                       `gokai/projects/{project_id}/`                     │
         └──────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Core Features

- **Multi-Agent DAG Orchestrator**: Automatically translates ambiguous user prompts into verifiable task steps with dependency resolution.
- **Self-Healing Debugger**: If tests fail, the Debugger Agent analyzes the traceback, inspects the source code, and writes a targeted fix before re-running the test suite.
- **Interactive AI Chat System**: Dedicated engineering conversation view with project-aware context, file & image attachment support, message history, and retry capabilities.
- **Modular Skills Subsystem**: Graphical UI to create, edit, delete, and toggle domain engineering skills with YAML frontmatter validation.
- **Multi-Provider AI Routing**: Native support for Google Gemini, OpenAI, Anthropic Claude, DeepSeek, NVIDIA Cloud NIM, and OpenRouter, with live connection testing and an internal Mock provider for offline testing.
- **Guarded File System**: Prevents path traversals (`../`) and unauthorized host filesystem modifications.
- **Developer Diagnostics ("D" Menu)**: Pressing `D` opens instant system telemetry, process health, cache cleaning, and backend log streaming.
- **Bilingual & Dual-Theme UI**: Built-in English and Turkish localization with Dark, Light, and System theme modes.
- **One-Click Native Launchers**: Native execution scripts for Windows (`Run-Windows.bat`), macOS (`Run-macOS.command`), and Linux (`run-linux.sh`).

---

## 💻 Requirements

- **Python**: 3.10 or newer (tested with Python 3.11, 3.12, and 3.13).
- **Node.js**: 18 or newer (with `npm`).
- **Operating System**: Windows 10/11, macOS (Intel & Apple Silicon), or modern Linux (Ubuntu, Debian, Fedora, Arch).
- **Optional**: Docker (if container isolation mode is preferred over local jailed processes).

---

## 🚀 One-Click Quick Start

### Windows
Double-click:
```text
Run-Windows.bat
```
*The launcher verifies dependencies, initializes `.env`, starts the backend and frontend servers, and opens your browser at `http://localhost:3000`.*

### macOS
Double-click in Finder:
```text
Run-macOS.command
```
*(If prompted regarding execution permissions on fresh git clones, run `chmod +x Run-macOS.command` once in Terminal).*

### Linux
Run in terminal:
```bash
chmod +x run-linux.sh
./run-linux.sh
```

---

## 🛠️ Manual Development Setup

If you prefer to start the servers manually:

### 1. Configure Environment
```bash
cp .env.example .env
```
Open `.env` (or configure via **Settings** in the Web UI) and add your AI provider API key.

### 2. Install Backend & Run Tests
```bash
pip install -e .
python -m pytest gokai/tests -v
```

### 3. Start Backend Server
```bash
python -m uvicorn gokai.apps.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend API Gateway will be available at `http://localhost:8000` (Swagger docs at `/docs`).*

### 4. Start Frontend Web Interface
In another terminal:
```bash
cd gokai/apps/frontend
npm install
npm run dev -- --port 3000
```
*Frontend UI will be available at `http://localhost:3000`.*

---

## 🔑 AI Provider Configuration

GökAI supports multiple cloud AI model providers. You only need **one** active provider key to use the platform:

| Provider | Environment Variable | Default Model | Supported Models |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | `GEMINI_API_KEY` | `gemini-2.5-flash` | `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-pro` |
| **OpenAI** | `OPENAI_API_KEY` | `gpt-4o-mini` | `gpt-4o-mini`, `gpt-4o`, `o1-mini`, `o3-mini` |
| **Anthropic Claude** | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022` | `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022` |
| **DeepSeek** | `DEEPSEEK_API_KEY` | `deepseek-chat` | `deepseek-chat`, `deepseek-reasoner` |
| **NVIDIA NIM** | `NVIDIA_API_KEY` | `meta/llama-3.1-70b-instruct` | `meta/llama-3.1-70b-instruct`, `meta/llama-3.3-70b-instruct` |
| **OpenRouter** | `OPENROUTER_API_KEY` | `meta-llama/llama-3.3-70b-instruct` | Multiple community & commercial models |
| **Internal Mock** | *(None required)* | `mock-engineer-v1` | Deterministic offline model for local test runs & CI |

> 🔒 **Security Notice**: Never commit real API keys into git. All keys in `.env.example` and repository code are safe empty placeholders. You can securely enter, test, and save your API keys directly from the **Settings** screen in the Web UI.

---

## 🧠 Domain Skills System

Skills provide modular domain engineering knowledge to agents during code generation:
- **Built-in Skills**: Shipped core guidelines (`python`, `fastapi`, `react`, `security`).
- **Custom Skills**: Create custom skills directly from the **Skills** tab in the Web UI. Specify the name, description, trigger condition (`when_to_use`), search tags, and markdown instructions.
- **Enable / Disable**: Toggle any skill on or off in real-time.

---

## 🛡️ Security & Sandboxing

GökAI executes generated code using defense-in-depth isolation:
- **JailedFileSystem**: Restricts all file reads, writes, edits, and deletions strictly inside the project's sandbox directory (`gokai/projects/{project_id}/`). Attempts to traverse directories (`../`) or access host operating system roots are immediately blocked.
- **SandboxedTerminal**: Spawns command execution under strict timeouts (default 120s) and memory caps.
- **Docker Isolation**: If Docker is installed and running, tasks can run inside temporary container sandboxes.

---

## 📦 Project Export

Every generated workspace can be exported as a standalone ZIP bundle from the **Projects & Files** tab. The export includes all source code, unit tests, configurations, and documentation created during the autonomous engineering cycle.

---

## 🗺️ Roadmap

- [x] **V1.0.0**: Autonomous multi-agent pipeline, self-healing debugger, AI chat, skills manager, multi-provider model routing, cross-platform launchers.
- [ ] **V1.1.0**: Git branch & pull request integration for GitHub and GitLab.
- [ ] **V1.2.0**: WebAssembly-based local in-browser code execution sandbox.
- [ ] **V1.3.0**: Distributed multi-node agent execution.

---

## 📄 License

GökAI is released under the **MIT License**.
