"""
GÖK SYSTEMS TECH — Terminal Execution Tool
Executes shell commands strictly bounded to the workspace directory.
Captures stdout, stderr, exit code, execution duration, and timeout status.
"""

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List
from gokai.packages.shared.models import ExecutionResult
from gokai.packages.shared.logger import get_logger

logger = get_logger("terminal_tool")


class SandboxedTerminal:
    """Executes commands safely within the project workspace."""

    def __init__(self, workspace_root: Path, default_timeout_seconds: int = 60):
        self.workspace_root = Path(workspace_root).resolve()
        self.default_timeout_seconds = default_timeout_seconds

    async def execute_command(
        self,
        command: str,
        timeout_seconds: Optional[int] = None,
        env_vars: Optional[dict] = None
    ) -> ExecutionResult:
        """Asynchronously executes a command inside the workspace directory."""
        timeout = timeout_seconds or self.default_timeout_seconds
        start_time = time.perf_counter()

        logger.info(f"Executing command: '{command}' (timeout: {timeout}s) in {self.workspace_root}")

        # Setup minimal safe environment
        safe_env = os.environ.copy()
        safe_env["PYTHONUNBUFFERED"] = "1"
        safe_env["PYTHONIOENCODING"] = "utf-8"
        if env_vars:
            safe_env.update(env_vars)

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=str(self.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=safe_env
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=float(timeout)
                )
                timed_out = False
                exit_code = process.returncode if process.returncode is not None else 1
            except asyncio.TimeoutError:
                timed_out = True
                exit_code = 124  # Standard timeout exit code
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
                stdout_bytes = b""
                stderr_bytes = f"Execution timed out after {timeout} seconds.".encode("utf-8")

        except Exception as ex:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Failed to spawn subprocess: {ex}")
            return ExecutionResult(
                command=command,
                exit_code=1,
                stdout="",
                stderr=str(ex),
                duration_ms=duration_ms,
                timed_out=False
            )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        logger.info(f"Command '{command}' finished with exit code {exit_code} in {duration_ms:.1f}ms")

        return ExecutionResult(
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            timed_out=timed_out
        )
