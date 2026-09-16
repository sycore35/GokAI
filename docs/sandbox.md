# GÖKAI Sandbox & Execution Architecture

> **GÖK SYSTEMS TECH** — Safe Execution Core  
> **Status:** Standardized Architecture Specification  

---

## 1. Overview & Objectives

GökAI generates, builds, and executes real software across Python, Node.js, Go, Rust, and shell environments. Executing untrusted, newly generated code directly on a host machine poses risks of accidental filesystem corruption, resource exhaustion, or infinite loops.

The **Sandbox Subsystem** provides strict process isolation, resource bounding, and output capture for every executable action.

### Key Capabilities:
1. **Primary Isolation: Docker Container Sandbox** — Spins up ephemeral containers with strict CPU, memory, and filesystem isolation.
2. **Fallback Isolation: Local Process Sandbox** — When Docker is unavailable, creates isolated subprocesses with working-directory jails, strict timeouts, memory limits, and process-tree termination.
3. **Execution Bounding** — Hard limits on runtime execution seconds, memory consumption, disk write quotas, and network egress.
4. **Structured I/O Capture** — Captures standard output, standard error, exit codes, process duration, and resource utilization.

---

## 2. Sandbox Architecture Diagram

```text
                           ┌────────────────────────────┐
                           │      AGENT TOOL CALL       │
                           │ (e.g. pytest / npm run dev)│
                           └─────────────┬──────────────┘
                                         │
                                         ▼
                           ┌────────────────────────────┐
                           │     EXECUTION MANAGER      │
                           │  - Health & Backend Check  │
                           │  - Policy Verification     │
                           └─────────────┬──────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
       ┌────────────────────────┐                  ┌────────────────────────┐
       │     DOCKER BACKEND     │                  │ LOCAL PROCESS BACKEND  │
       │   (Primary Strategy)   │                  │  (Fallback Strategy)   │
       └───────────┬────────────┘                  └───────────┬────────────┘
                   │                                           │
                   ▼                                           ▼
       ┌────────────────────────┐                  ┌────────────────────────┐
       │ - Read-Only Root FS    │                  │ - Workspace Chroot/CWD │
       │ - Mounted /workspace   │                  │ - Process Tree Group   │
       │ - Non-Root User        │                  │ - Safe Environment Map │
       │ - CPU Quota: 2 cores   │                  │ - JobObject / cgroups  │
       │ - RAM Quota: 2048 MB   │                  │ - Subprocess Timeout   │
       │ - Internal Network Only│                  │ - Output Truncator     │
       └───────────┬────────────┘                  └───────────┬────────────┘
                   │                                           │
                   └─────────────────────┬─────────────────────┘
                                         │
                                         ▼
                           ┌────────────────────────────┐
                           │    EXECUTION RESULT OBJ    │
                           │ - Exit Code (0, 1, 137...) │
                           │ - Stdout / Stderr          │
                           │ - Execution Time (ms)      │
                           │ - Memory Peak (MB)         │
                           └────────────────────────────┘
```

---

## 3. Sandbox Configuration & Limits

```python
from pydantic import BaseModel, Field

class SandboxConfig(BaseModel):
    backend: str = "auto"  # "docker", "local_process", or "auto"
    docker_image: str = "gokai/sandbox-runner:latest"
    max_execution_timeout_seconds: int = 120
    max_memory_mb: int = 2048
    max_cpu_cores: float = 2.0
    network_enabled: bool = False
    max_output_bytes: int = 1024 * 1024 * 5  # 5 MB max output capture
```

---

## 4. Primary Strategy: Docker Sandbox

When Docker is installed and running, each project or task executes within an isolated container:

1. **Volume Binding**: Only `/workspace/projects/{project_id}/` is mounted into the container at `/app`. No host root directories (`C:\`, `/`, `/etc`) are accessible.
2. **User Namespace**: Executed as a non-privileged user (`uid=1000, gid=1000`).
3. **Resource Capping**:
   ```bash
   docker run --rm \
     --network none \
     --cpus="2.0" \
     --memory="2048m" \
     --volume "/path/to/project:/app:rw" \
     --workdir "/app" \
     gokai/sandbox-runner:latest \
     timeout 60 pytest
   ```
4. **Instant Teardown**: Containers are created on-demand and removed (`--rm`) immediately upon process completion, preventing orphaned processes.

---

## 5. Fallback Strategy: Local Process Jail

For lightweight environments where Docker daemon is not active:

1. **Working Directory Lockdown**: Commands execute strictly with `cwd=workspace_dir`.
2. **Environment Variable Sanitization**: The host system environment (`PATH`, `USER`, sensitive keys) is stripped. Only safe, minimal variables are passed.
3. **Process Tree Termination**: On Windows, processes are assigned to a Win32 `JobObject` (or process groups `os.setsid` on Unix). If a timeout fires, all child processes spawned by build scripts or web servers are forcefully terminated, preventing zombie processes.
4. **Non-Blocking Streaming**: Output buffers are consumed asynchronously to prevent deadlocks from full stdout pipe buffers.
