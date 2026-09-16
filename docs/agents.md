# GÖKAI Agent System Specification

> **GÖK SYSTEMS TECH** — Multi-Agent Engineering Core  
> **Status:** Standardized Architecture Specification  

---

## 1. Agent Architecture Philosophy

In GökAI, agents are not chat personas. They are **stateful, specialized, autonomous software engineering micro-workers**. Each agent is bounded by strict capabilities, tool access permissions, model preferences, and validation contracts.

Agents do not communicate via conversational free-text. All inter-agent data exchange occurs through **Structured Agent Envelopes (`AgentMessage`)** validated with Pydantic schemas.

---

## 2. Base Agent Interface (`BaseAgent`)

Every agent implementation inherits from the abstract base interface:

```python
from abc import ABC, abstractmethod
from typing import Any, List, Optional
from pydantic import BaseModel, Field
from gokai.packages.shared.models import (
    AgentMessage,
    AgentRunResult,
    Artifact,
    TaskContext
)

class AgentPermissions(BaseModel):
    can_read_filesystem: bool = True
    can_write_filesystem: bool = False
    can_execute_terminal: bool = False
    can_access_browser: bool = False
    can_make_network_requests: bool = False
    can_access_database: bool = False

class BaseAgent(ABC):
    """Abstract Base Class for all GökAI Specialist Agents."""
    
    name: str
    description: str
    system_prompt: str
    allowed_tools: List[str]
    permissions: AgentPermissions
    preferred_model_family: str  # e.g., "reasoning", "coding", "fast", "multimodal"
    
    @abstractmethod
    async def execute(
        self,
        task_context: TaskContext,
        input_message: Optional[AgentMessage] = None
    ) -> AgentRunResult:
        """Executes the specialized agent workflow and returns a validated result."""
        pass
    
    @abstractmethod
    def get_system_prompt(self, context: TaskContext) -> str:
        """Generates the localized system prompt injected with skills and memory."""
        pass
```

---

## 3. Specialist Agent Roles

### 3.1. Orchestrator Agent (`orchestrator`)
* **Purpose:** Central coordinator, planner, and task decomposition engine.
* **Responsibilities:**
  - Analyzes raw user prompts into formal technical requirements.
  - Constructs the execution DAG (`TaskPlan` with dependent `TaskStep` items).
  - Selects appropriate specialist agents and routes work items.
  - Coordinates the **Self-Healing Loop** (Test $\to$ Fail $\to$ Debug $\to$ Retest).
  - Handles Human-in-the-Loop gates (Approval for dangerous actions).
* **Allowed Tools:** `task_planner`, `dependency_resolver`, `state_transition_tool`.
* **Permissions:** Read memory, read task state, mutate orchestrator state. No direct filesystem writes or terminal execution.

### 3.2. Research Agent (`researcher`)
* **Purpose:** External technical discovery, official documentation scraping, and API exploration.
* **Responsibilities:**
  - Searches technical knowledge bases, official framework docs, and library release notes.
  - Mitigates hallucinations by verifying actual library versions and signatures.
  - Treats all external web content as **untrusted data** (Prompt Injection Defense).
  - Emits structured `ResearchArtifact` (findings, sources, confidence scores).
* **Allowed Tools:** `web_search`, `url_fetcher`, `doc_parser`.
* **Permissions:** Network access enabled. Filesystem write disabled.

### 3.3. Developer Agent (`developer`)
* **Purpose:** Code generation, file creation, project scaffolding, and refactoring.
* **Responsibilities:**
  - First inspects existing workspace structure and imports before generating code.
  - Generates production-ready, typed, documented source code across full-stack languages.
  - Produces unified diffs or atomic file writes to avoid destroying unrelated files.
  - Generates configuration (`.env.example`, `package.json`, `requirements.txt`, Dockerfiles).
* **Allowed Tools:** `file_writer`, `file_reader`, `file_editor`, `directory_lister`, `code_search`.
* **Permissions:** Read/Write within project workspace only. No terminal execution without Orchestrator approval.

### 3.4. Test Agent (`tester`)
* **Purpose:** Multi-level automated verification and quality assurance.
* **Responsibilities:**
  - Generates and executes test suites: Unit, Integration, API, Build, and Static Analysis.
  - Captures test exit codes, standard output, and structured tracebacks.
  - Asserts that endpoints, CLI tools, and libraries execute as specified.
  - Emits structured `TestReportArtifact` detailing passed/failed assertions.
* **Allowed Tools:** `terminal_executor`, `file_reader`, `test_runner`.
* **Permissions:** Read filesystem, execute sandboxed test runners (`pytest`, `npm test`).

### 3.5. Debugger Agent (`debugger`)
* **Purpose:** Autonomous root-cause analysis and automated patch synthesis.
* **Responsibilities:**
  - Ingests test failures, compiler errors, runtime tracebacks, and exit codes.
  - Pinpoints root cause (syntax error, missing dependency, broken import, wrong port).
  - Formulates isolated patch hypotheses and applies minimal corrective code edits.
  - Triggers re-testing cycle (enforces `MAX_DEBUG_CYCLES = 5` to prevent infinite loops).
* **Allowed Tools:** `traceback_analyzer`, `file_reader`, `file_editor`, `diff_patcher`.
* **Permissions:** Read/Write within workspace, read test logs.

### 3.6. Design & UI Agent (`designer`)
* **Purpose:** Frontend visual validation, layout hierarchy, and responsive UI auditing.
* **Responsibilities:**
  - Audits visual aesthetics, typography, accessibility (WCAG), and responsive layouts.
  - Uses Playwright browser automation to launch applications, navigate, and capture screenshots.
  - Detects frontend runtime console errors, unhandled promise rejections, and broken assets.
  - Conducts visual verification of rendered pages against user prompt intentions.
* **Allowed Tools:** `browser_navigate`, `browser_screenshot`, `browser_dom_read`, `browser_console_logs`.
* **Permissions:** Browser control, localhost network requests.

### 3.7. Security Agent (`security`)
* **Purpose:** Static application security testing (SAST) and vulnerability detection.
* **Responsibilities:**
  - Scans workspace for hardcoded API keys, database credentials, and secrets.
  - Detects vulnerabilities: SQL Injection, Command Injection, Path Traversal, XSS, CSRF, Insecure Deserialization, CORS misconfigurations.
  - Evaluates third-party dependency vulnerabilities.
  - Halts task execution and alerts user if a `CRITICAL` vulnerability is identified.
* **Allowed Tools:** `secret_scanner`, `ast_security_analyzer`, `dependency_auditor`.
* **Permissions:** Read-only access to workspace files.

### 3.8. Documentation Agent (`documenter`)
* **Purpose:** Production documentation, architecture guides, and API specifications.
* **Responsibilities:**
  - Generates comprehensive `README.md`, setup guides, and environment instructions.
  - Produces OpenAPI/Swagger specifications, architecture markdown docs, and changelogs.
  - Prepares long-form technical guides, manuals, and technical outlines.
* **Allowed Tools:** `file_writer`, `file_reader`, `markdown_formatter`.
* **Permissions:** Read/Write within project workspace.

### 3.9. Reviewer Agent (`reviewer`)
* **Purpose:** Final comprehensive quality audit and acceptance verification.
* **Responsibilities:**
  - Audits the completed project against the initial user request.
  - Validates that all requested features are implemented and running.
  - Verifies that all test suites passed and no security alerts remain open.
  - Produces the final executive `ProjectReviewReport` for user signoff.
* **Allowed Tools:** `workspace_auditor`, `report_generator`.
* **Permissions:** Read-only workspace access.

---

## 4. Structured Agent Communication Protocol

Agents exchange structured messages wrapped in the `AgentMessage` envelope:

```json
{
  "message_id": "msg_89f72b10",
  "task_id": "task_48291a0c",
  "project_id": "proj_finance_tracker",
  "timestamp": "2026-09-13T21:55:00Z",
  "from_agent": "developer",
  "to_agent": "tester",
  "message_type": "artifact_ready",
  "payload": {
    "artifact_id": "art_backend_main",
    "artifact_type": "code",
    "file_path": "backend/app/main.py",
    "summary": "FastAPI application entrypoint with JWT auth and portfolio router.",
    "ready_for_testing": true
  },
  "metadata": {
    "model_used": "gemini-2.5-pro",
    "tokens_consumed": 2410,
    "step_index": 3
  }
}
```

### Message Types
* `task_directive`: Work assignment from Orchestrator to specialist.
* `artifact_ready`: Deliverable produced and available for review/testing.
* `test_result`: Execution outcome (pass/fail, logs, metrics).
* `debug_request`: Diagnostic package sent to Debugger.
* `patch_applied`: Fix applied, requesting regression test.
* `security_alert`: Vulnerability detected requiring remediation.
* `task_completion`: Final deliverable ready for Reviewer.
