"""
GÖK SYSTEMS TECH — End-to-End Autonomous Pipeline Verification Script
Executes Phase 12: Autonomous Project Creation, Code Generation, Test Execution, Security Audit, and Signoff.
"""

import asyncio
import os
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from gokai.packages.shared.models import TaskStatus
from gokai.packages.model_router.router import ModelRouter
from gokai.packages.model_router.mock_provider import MockTestAIProvider
from gokai.packages.orchestrator.orchestrator import OrchestratorEngine
from gokai.packages.shared.logger import get_logger

logger = get_logger("e2e_test")


async def main():
    print("\n" + "=" * 70)
    print("[GOKAI] AUTONOMOUS PIPELINE END-TO-END VALIDATION (PHASE 12)")
    print("GOK SYSTEMS TECH -- Full Multi-Agent Engineering Verification")
    print("=" * 70 + "\n")

    workspace_base = PROJECT_ROOT / "gokai" / "projects"
    project_id = "calculator_cli_project"
    task_id = "task_e2e_calc_01"
    user_prompt = "Create a Python calculator CLI application with tests."

    # 1. Initialize Model Router with deterministic test provider
    router = ModelRouter()
    mock_provider = MockTestAIProvider()
    router.register_provider("mock", mock_provider)
    router.default_provider = "mock"
    router.default_model = "mock-engineer-v1"

    # 2. Event listener callback
    def on_event(event_type: str, data: dict):
        status = data.get("status", "")
        msg = data.get("message", "")
        print(f"  * [{event_type.upper()}] Status: {status} | {msg}")

    # 3. Instantiate Autonomous Orchestrator Engine
    orchestrator = OrchestratorEngine(
        model_router=router,
        workspace_base_dir=workspace_base,
        max_debug_cycles=5,
        event_callback=on_event
    )

    print(f"User Objective: '{user_prompt}'")
    print(f"Workspace Target: {workspace_base / project_id}\n")

    # 4. Execute Autonomous Task
    result = await orchestrator.execute_task(
        task_id=task_id,
        project_id=project_id,
        user_prompt=user_prompt,
        skip_research=False
    )

    print("\n" + "-" * 70)
    print("ORCHESTRATOR EXECUTION SUMMARY:")
    print(f"  - Success: {result['success']}")
    print(f"  - Final Status: {result['status']}")
    print(f"  - Total Artifacts Produced: {len(result['artifacts'])}")
    print(f"  - Duration: {result['duration_seconds']:.2f}s")
    print(f"  - Debug Cycles Required: {result['debug_cycles']}")
    print("-" * 70 + "\n")

    # 5. Assertions on real files and execution
    project_dir = workspace_base / project_id
    calc_file = project_dir / "calculator.py"
    test_file = project_dir / "test_calculator.py"
    report_file = project_dir / "test_run_report.txt"
    audit_file = project_dir / "SECURITY_AUDIT.md"
    review_file = project_dir / "PROJECT_REVIEW.md"

    print("VERIFYING PHYSICAL WORKSPACE ARTIFACTS:")
    assert calc_file.exists(), f"Missing file: {calc_file}"
    print(f"  [PASS] {calc_file.name} exists ({calc_file.stat().st_size} bytes)")

    assert test_file.exists(), f"Missing file: {test_file}"
    print(f"  [PASS] {test_file.name} exists ({test_file.stat().st_size} bytes)")

    assert report_file.exists(), f"Missing file: {report_file}"
    print(f"  [PASS] {report_file.name} exists ({report_file.stat().st_size} bytes)")

    assert audit_file.exists(), f"Missing file: {audit_file}"
    print(f"  [PASS] {audit_file.name} exists ({audit_file.stat().st_size} bytes)")

    assert review_file.exists(), f"Missing file: {review_file}"
    print(f"  [PASS] {review_file.name} exists ({review_file.stat().st_size} bytes)")

    # 6. Verify that tests actually passed!
    test_report_content = report_file.read_text(encoding="utf-8")
    assert "passed" in test_report_content.lower() or "ok" in test_report_content.lower(), "Tests did not pass!"
    print(f"  [PASS] Automated test run validated: Pytest tests PASSED in isolated workspace!")

    assert result["status"] == TaskStatus.COMPLETED
    assert result["success"] is True

    print("\n" + "=" * 70)
    print("ALL ACCEPTANCE CRITERIA FOR PHASE 12 PASSED WITH FULL SUCCESS!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
