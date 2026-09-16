"""
GÖK SYSTEMS TECH — Central Autonomous Orchestrator Engine
Coordinates task planning, multi-agent dispatch, verification, and the self-healing debug loop.
Integrated with hierarchical project Memory and modular domain Skills.
"""

import asyncio
import time
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path

from gokai.packages.shared.models import (
    TaskStatus,
    AgentRole,
    TaskStep,
    TaskContext,
    Artifact,
    AgentRunResult,
)
from gokai.packages.shared.exceptions import (
    MaxCyclesExceededError,
    GokAIException,
)
from gokai.packages.shared.logger import get_logger
from gokai.packages.model_router.router import ModelRouter
from gokai.packages.tools.tool_registry import ToolRegistry
from gokai.packages.memory.memory_manager import MemoryManager
from gokai.packages.skills.skill_manager import SkillManager
from gokai.packages.orchestrator.state_machine import TaskStateMachine

from gokai.packages.agents.developer import DeveloperAgent
from gokai.packages.agents.tester import TesterAgent
from gokai.packages.agents.debugger import DebuggerAgent
from gokai.packages.agents.reviewer import ReviewerAgent
from gokai.packages.agents.security import SecurityAgent
from gokai.packages.agents.researcher import ResearchAgent

logger = get_logger("orchestrator")


class OrchestratorEngine:
    """Master controller executing multi-agent software engineering workflows."""

    def __init__(
        self,
        model_router: ModelRouter,
        workspace_base_dir: Path,
        skills_dir: Optional[Path] = None,
        max_debug_cycles: int = 5,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        self.model_router = model_router
        self.workspace_base_dir = Path(workspace_base_dir).resolve()
        self.max_debug_cycles = max_debug_cycles
        self.event_callback = event_callback

        # Initialize domain skill manager
        s_dir = Path(skills_dir) if skills_dir else (self.workspace_base_dir.parent / "skills")
        self.skill_manager = SkillManager(s_dir)

        # Cancelled task flags
        self.cancelled_tasks: set[str] = set()

    def cancel_task(self, task_id: str):
        """Flags task for immediate cancellation."""
        self.cancelled_tasks.add(task_id)
        self._emit_event("status_changed", {"status": TaskStatus.CANCELLED, "message": "Task cancelled by user."})

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emits real-time event for UI streaming (SSE / WebSockets)."""
        logger.info(f"EVENT [{event_type}]: {data.get('message', '')}")
        if self.event_callback:
            try:
                self.event_callback(event_type, data)
            except Exception as ex:
                logger.warning(f"Event callback error: {ex}")

    def _check_cancelled(self, task_id: str):
        if task_id in self.cancelled_tasks:
            raise GokAIException(f"Task '{task_id}' was cancelled.")

    async def execute_task(
        self,
        task_id: str,
        project_id: str,
        user_prompt: str,
        skip_research: bool = False
    ) -> Dict[str, Any]:
        """Executes the full autonomous engineering lifecycle for a task."""
        project_dir = self.workspace_base_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        tool_registry = ToolRegistry(project_dir)

        # Initialize project memory
        memory_db_path = project_dir / ".gokai_memory.db"
        memory = MemoryManager(memory_db_path)

        # Load existing project facts and decisions into context
        existing_facts = memory.get_entries(project_id, tier=1)
        existing_decisions = [d["content"] for d in memory.get_entries(project_id, tier=2)]

        # Match relevant domain skills
        matched_skills = self.skill_manager.match_skills(user_prompt)
        skill_names = [s.name for s in matched_skills]
        logger.info(f"Matched skills for task: {skill_names}")

        # Initialize specialist agents bound to this workspace
        dev_agent = DeveloperAgent(self.model_router, tool_registry)
        test_agent = TesterAgent(self.model_router, tool_registry)
        dbg_agent = DebuggerAgent(self.model_router, tool_registry)
        sec_agent = SecurityAgent(self.model_router, tool_registry)
        rev_agent = ReviewerAgent(self.model_router, tool_registry)
        res_agent = ResearchAgent(self.model_router, tool_registry)

        context = TaskContext(
            task_id=task_id,
            project_id=project_id,
            user_prompt=user_prompt,
            workspace_path=str(project_dir),
            facts=existing_facts,
            decisions=existing_decisions,
            active_skills=skill_names
        )

        all_artifacts: List[Artifact] = []
        agent_traces: List[Dict[str, Any]] = []
        total_tokens = 0
        total_cost = 0.0
        start_time = time.perf_counter()

        # Step 1: PLANNING
        self._check_cancelled(task_id)
        current_status = TaskStatus.QUEUED
        TaskStateMachine.validate_transition(current_status, TaskStatus.PLANNING)
        current_status = TaskStatus.PLANNING
        self._emit_event("status_changed", {
            "status": current_status,
            "message": "Planning engineering workflow & matching skills...",
            "skills": skill_names
        })

        # Step 2: RESEARCH (Optional based on prompt complexity)
        if not skip_research and len(user_prompt.split()) > 4:
            self._check_cancelled(task_id)
            TaskStateMachine.validate_transition(current_status, TaskStatus.RESEARCHING)
            current_status = TaskStatus.RESEARCHING
            self._emit_event("status_changed", {"status": current_status, "message": "Researching architecture and dependencies..."})

            res_result = await res_agent.execute(context)
            agent_traces.append(res_result.model_dump())
            all_artifacts.extend(res_result.artifacts_created)
            total_tokens += res_result.input_tokens + res_result.output_tokens
            total_cost += res_result.cost_usd

        # Step 3: CODING
        self._check_cancelled(task_id)
        TaskStateMachine.validate_transition(current_status, TaskStatus.CODING)
        current_status = TaskStatus.CODING
        self._emit_event("status_changed", {"status": current_status, "message": "Developer Agent generating files..."})

        dev_result = await dev_agent.execute(context)
        agent_traces.append(dev_result.model_dump())
        all_artifacts.extend(dev_result.artifacts_created)
        total_tokens += dev_result.input_tokens + dev_result.output_tokens
        total_cost += dev_result.cost_usd

        if not dev_result.success:
            current_status = TaskStatus.FAILED
            self._emit_event("status_changed", {"status": current_status, "message": "Code generation failed."})
            return {
                "success": False,
                "status": current_status,
                "artifacts": [a.model_dump() for a in all_artifacts],
                "error": "Developer failed to produce code files."
            }

        # Step 4: TESTING & SELF-HEALING DEBUG LOOP
        self._check_cancelled(task_id)
        TaskStateMachine.validate_transition(current_status, TaskStatus.TESTING)
        current_status = TaskStatus.TESTING
        self._emit_event("status_changed", {"status": current_status, "message": "Test Agent executing test suite..."})

        test_result = await test_agent.execute(context)
        agent_traces.append(test_result.model_dump())
        all_artifacts.extend(test_result.artifacts_created)
        total_tokens += test_result.input_tokens + test_result.output_tokens
        total_cost += test_result.cost_usd

        debug_cycle = 0
        while not test_result.success and debug_cycle < self.max_debug_cycles:
            self._check_cancelled(task_id)
            debug_cycle += 1
            logger.warning(f"Tests failed! Entering Self-Healing Debug Loop #{debug_cycle}/{self.max_debug_cycles}")

            TaskStateMachine.validate_transition(current_status, TaskStatus.DEBUGGING)
            current_status = TaskStatus.DEBUGGING
            self._emit_event("status_changed", {
                "status": current_status,
                "message": f"Debugger fixing test failure (Cycle {debug_cycle}/{self.max_debug_cycles})..."
            })

            context.recent_errors = test_result.errors
            dbg_result = await dbg_agent.execute(context)
            agent_traces.append(dbg_result.model_dump())
            all_artifacts.extend(dbg_result.artifacts_created)
            total_tokens += dbg_result.input_tokens + dbg_result.output_tokens
            total_cost += dbg_result.cost_usd

            # Re-test
            TaskStateMachine.validate_transition(current_status, TaskStatus.TESTING)
            current_status = TaskStatus.TESTING
            self._emit_event("status_changed", {"status": current_status, "message": f"Re-running tests after patch (Cycle {debug_cycle})..."})

            test_result = await test_agent.execute(context)
            agent_traces.append(test_result.model_dump())
            all_artifacts.extend(test_result.artifacts_created)
            total_tokens += test_result.input_tokens + test_result.output_tokens
            total_cost += test_result.cost_usd

        if not test_result.success:
            logger.error("Self-healing exceeded max debug cycles.")
            current_status = TaskStatus.FAILED
            self._emit_event("status_changed", {"status": current_status, "message": "Task failed after reaching max debug cycles."})
            return {
                "success": False,
                "status": current_status,
                "debug_cycles": debug_cycle,
                "artifacts": [a.model_dump() for a in all_artifacts],
                "error": "Failed to resolve test failures within cycle limits."
            }

        # Step 5: SECURITY AUDIT
        self._check_cancelled(task_id)
        self._emit_event("status_changed", {"status": current_status, "message": "Security Agent auditing codebase..."})
        sec_result = await sec_agent.execute(context)
        agent_traces.append(sec_result.model_dump())
        all_artifacts.extend(sec_result.artifacts_created)

        # Step 6: REVIEW
        self._check_cancelled(task_id)
        TaskStateMachine.validate_transition(current_status, TaskStatus.REVIEWING)
        current_status = TaskStatus.REVIEWING
        self._emit_event("status_changed", {"status": current_status, "message": "Reviewer Agent producing final signoff..."})

        rev_result = await rev_agent.execute(context)
        agent_traces.append(rev_result.model_dump())
        all_artifacts.extend(rev_result.artifacts_created)
        total_tokens += rev_result.input_tokens + rev_result.output_tokens
        total_cost += rev_result.cost_usd

        # Step 7: PERSIST OUTCOME IN PROJECT MEMORY
        memory.add_task_summary(project_id, f"Completed objective: {user_prompt} ({len(all_artifacts)} artifacts)")
        if debug_cycle > 0:
            memory.add_decision(project_id, f"Auto-repaired test failures across {debug_cycle} debug cycle(s).")

        # Step 8: COMPLETE
        TaskStateMachine.validate_transition(current_status, TaskStatus.COMPLETED)
        current_status = TaskStatus.COMPLETED
        duration_s = time.perf_counter() - start_time

        self._emit_event("status_changed", {
            "status": current_status,
            "message": f"Task COMPLETED successfully in {duration_s:.1f}s!",
            "artifacts_count": len(all_artifacts),
            "cost_usd": total_cost,
        })

        return {
            "success": True,
            "status": current_status,
            "duration_seconds": duration_s,
            "debug_cycles": debug_cycle,
            "artifacts": [a.model_dump() for a in all_artifacts],
            "agent_traces": agent_traces,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
        }
