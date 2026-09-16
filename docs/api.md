# GÖKAI API Gateway Specification

> **GÖK SYSTEMS TECH** — Unified REST & Real-Time Protocol  
> **Status:** Standardized Architecture Specification  

---

## 1. Overview & Transport Protocols

The **GökAI API Gateway** is built on high-performance **FastAPI (Python 3.11+)** with full async architecture. It serves two distinct communication channels to the frontend:
1. **RESTful HTTP API**: Standard CRUD operations for projects, tasks, models, skills, configurations, and exports.
2. **Real-Time Event Streaming (SSE / WebSockets)**: Low-latency streaming of agent execution steps, live token counters, terminal output streams, and human-in-the-loop interactive approvals.

---

## 2. API Endpoint Matrix

### 2.1. Projects (`/api/projects`)
* `GET /api/projects`: List all user projects with summary metadata.
* `POST /api/projects`: Create a new project (name, description, default tech stack).
* `GET /api/projects/{project_id}`: Retrieve detailed project info, stats, and settings.
* `DELETE /api/projects/{project_id}`: Safely delete project and workspace directory.
* `GET /api/projects/{project_id}/files`: Recursive directory and file tree explorer.
* `GET /api/projects/{project_id}/files/content?path={file_path}`: Read individual file content.
* `POST /api/projects/{project_id}/files/content`: Save modified file content.
* `GET /api/projects/{project_id}/export`: Download full project workspace as a structured `.zip` bundle (with sensitive keys omitted).

### 2.2. Tasks & Orchestration (`/api/tasks`)
* `GET /api/tasks?project_id={project_id}`: List tasks for a project.
* `POST /api/tasks`: Submit a natural language directive (creates and enqueues a new `Task`).
* `GET /api/tasks/{task_id}`: Retrieve task status, step DAG, logs, and artifacts.
* `POST /api/tasks/{task_id}/pause`: Temporarily pause task execution.
* `POST /api/tasks/{task_id}/resume`: Resume paused task execution.
* `POST /api/tasks/{task_id}/cancel`: Abort task, terminate container sandbox processes, and retain partial artifacts.
* `POST /api/tasks/{task_id}/retry`: Re-trigger failed task from the last successful checkpoint.
* `POST /api/tasks/{task_id}/approve`: Respond to an approval request (`ALLOW`, `DENY`, `EDIT`).

### 2.3. Real-Time Streaming (`/api/tasks/{task_id}/stream`)
* **WebSocket (`ws://.../api/tasks/{task_id}/ws`)** or **Server-Sent Events (`GET /api/tasks/{task_id}/sse`)**:
  - Event `task_step_started`: Step name, assigned agent, timestamp.
  - Event `agent_thinking`: Model inference token streaming.
  - Event `tool_call`: Tool name, arguments (jailed path, sandboxed command).
  - Event `terminal_output`: Live stdout/stderr chunks from running test/build.
  - Event `approval_required`: Interactivity prompt payload.
  - Event `task_completed`: Final review summary and artifact manifest.

### 2.4. Agents & Capability Catalog (`/api/agents`)
* `GET /api/agents`: List all 9 specialist agents, their capabilities, and current status.
* `GET /api/agents/{agent_name}`: Retrieve agent schema, allowed tools, and prompt template.

### 2.5. Skills Registry (`/api/skills`)
* `GET /api/skills`: List installed skills.
* `POST /api/skills/install`: Upload and validate a new custom skill package (ZIP or folder).
* `GET /api/skills/{skill_name}`: View skill details, documentation, and tags.

### 2.6. Models & Cost Management (`/api/models`)
* `GET /api/models`: List configured providers (Gemini, OpenAI, DeepSeek, NVIDIA) and availability.
* `GET /api/models/usage`: Aggregated token consumption, latency benchmarks, and USD cost reports.

### 2.7. System Settings & Health (`/api/settings`, `/api/health`)
* `GET /api/settings`: Retrieve application settings (autonomy mode, budget limits, theme).
* `PATCH /api/settings`: Update settings and API key configurations.
* `GET /api/health`: Health status of Backend, Database, Execution Sandbox, and Model APIs.
