"""
GÖK SYSTEMS TECH — Agents Catalog API
"""

from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter(prefix="/agents", tags=["Agents"])

SPECIALIST_AGENTS = [
    {
        "name": "orchestrator",
        "title": "Autonomous Orchestrator",
        "role": "Coordinator & Planner",
        "description": "Decomposes complex requests into DAG tasks and manages self-healing verification cycles.",
        "allowed_tools": ["task_planner", "state_transition_tool"],
        "status": "ready"
    },
    {
        "name": "developer",
        "title": "Lead Software Developer",
        "role": "Code Generation & Architecture",
        "description": "Generates typed, production-ready code files across Python, Node, React, and databases.",
        "allowed_tools": ["read_file", "write_file", "list_files"],
        "status": "ready"
    },
    {
        "name": "tester",
        "title": "QA Test Engineer",
        "role": "Automated Verification",
        "description": "Generates and runs pytest / test suites inside isolated sandboxes to prove code works.",
        "allowed_tools": ["read_file", "write_file", "execute_command"],
        "status": "ready"
    },
    {
        "name": "debugger",
        "title": "Systems Debugger & Repair",
        "role": "Root Cause Analysis & Patching",
        "description": "Reads traceback logs, identifies root causes, and synthesizes minimal corrective diffs.",
        "allowed_tools": ["read_file", "write_file", "list_files"],
        "status": "ready"
    },
    {
        "name": "security",
        "title": "Application Security Auditor",
        "role": "Vulnerability & Secret Scanning",
        "description": "Performs static application security testing (SAST) and detects credentials/injection bugs.",
        "allowed_tools": ["read_file", "list_files"],
        "status": "ready"
    },
    {
        "name": "reviewer",
        "title": "Executive Code Reviewer",
        "role": "Final Quality Signoff",
        "description": "Audits delivered files against the user objective and generates signoff reports.",
        "allowed_tools": ["read_file", "list_files"],
        "status": "ready"
    },
    {
        "name": "researcher",
        "title": "Lead Technology Researcher",
        "role": "Documentation & Intelligence",
        "description": "Researches official library versions, schemas, and best practices.",
        "allowed_tools": ["read_file", "list_files"],
        "status": "ready"
    }
]


@router.get("", response_model=List[Dict[str, Any]])
def list_agents():
    return SPECIALIST_AGENTS
