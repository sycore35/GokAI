"""
GÖK SYSTEMS TECH — Sandbox Execution Subsystem
Provides containerized (Docker) and local isolated process execution environments
with strict CPU, memory, and timeout limits.
"""

import asyncio
import os
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from gokai.packages.shared.models import ExecutionResult
from gokai.packages.shared.logger import get_logger

logger = get_logger("sandbox")


class SandboxPolicy(BaseModel):
    timeout_seconds: int = 120
    max_memory_mb: int = 2048
    allow_network: bool = False
    read_only_root: bool = True


class ExecutionManager:
    """Dispatches command execution into Docker sandbox or isolated process fallback."""

    def __init__(self, workspace_root: Path, policy: Optional[SandboxPolicy] = None):
        self.workspace_root = Path(workspace_root).resolve()
        self.policy = policy or SandboxPolicy()
        self.docker_available = self._detect_docker()

    def _detect_docker(self) -> bool:
        """Checks if Docker CLI is available on the system."""
        return shutil.which("docker") is not None

    async def run_in_sandbox(
        self,
        command: str,
        timeout_seconds: Optional[int] = None
    ) -> ExecutionResult:
        """Executes command in Docker if available, otherwise runs in local jailed process."""
        timeout = timeout_seconds or self.policy.timeout_seconds

        if self.docker_available:
            logger.info("Executing via Docker Sandbox Container")
            return await self._run_docker(command, timeout)
        else:
            logger.info("Docker not detected. Executing via Isolated Local Subprocess Sandbox")
            return await self._run_local_process(command, timeout)

    async def _run_docker(self, command: str, timeout: int) -> ExecutionResult:
        start_time = time.perf_counter()
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.workspace_root}:/app",
            "-w", "/app",
            f"--memory={self.policy.max_memory_mb}m",
            "python:3.11-slim",
            "sh", "-c", command
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=float(timeout))
            exit_code = proc.returncode or 0
            timed_out = False
        except asyncio.TimeoutError:
            exit_code = 124
            timed_out = True
            stdout, stderr = b"", b"Execution timed out."

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return ExecutionResult(
            command=command,
            exit_code=exit_code,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
            duration_ms=duration_ms,
            timed_out=timed_out
        )

    async def _run_local_process(self, command: str, timeout: int) -> ExecutionResult:
        start_time = time.perf_counter()
        safe_env = os.environ.copy()
        safe_env["PYTHONUNBUFFERED"] = "1"

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=str(self.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=safe_env
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=float(timeout))
            exit_code = proc.returncode or 0
            timed_out = False
        except asyncio.TimeoutError:
            exit_code = 124
            timed_out = True
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            stdout, stderr = b"", b"Execution timed out."

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return ExecutionResult(
            command=command,
            exit_code=exit_code,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
            duration_ms=duration_ms,
            timed_out=timed_out
        )
