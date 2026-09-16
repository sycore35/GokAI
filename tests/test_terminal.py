"""
Tests for SandboxedTerminal.
"""

import asyncio
import tempfile
import sys
from pathlib import Path
from gokai.packages.tools.terminal import SandboxedTerminal


def test_terminal_successful_execution():
    async def _run():
        with tempfile.TemporaryDirectory() as tmpdir:
            term = SandboxedTerminal(Path(tmpdir))
            py_exe = sys.executable

            result = await term.execute_command(f'"{py_exe}" -c "print(\'GOKAI_OK\')"')
            assert result.exit_code == 0
            assert "GOKAI_OK" in result.stdout
            assert not result.timed_out
            assert result.duration_ms > 0

    asyncio.run(_run())


def test_terminal_timeout():
    async def _run():
        with tempfile.TemporaryDirectory() as tmpdir:
            term = SandboxedTerminal(Path(tmpdir), default_timeout_seconds=1)
            py_exe = sys.executable

            # Run a command that sleeps 3s with a 1s timeout
            result = await term.execute_command(f'"{py_exe}" -c "import time; time.sleep(3)"', timeout_seconds=1)
            assert result.timed_out is True
            assert result.exit_code == 124

    asyncio.run(_run())
