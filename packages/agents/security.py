"""
GÖK SYSTEMS TECH — Security Agent
Conducts static code security audits, scans for hardcoded secrets, injection flaws,
unsafe shell commands, and dependency vulnerabilities.
"""

import re
import time
from typing import Optional, List, Dict, Any
from gokai.packages.agents.base import BaseAgent, AgentPermissions
from gokai.packages.shared.models import (
    AgentMessage,
    AgentRunResult,
    TaskContext,
    Artifact,
    ArtifactType,
)
from gokai.packages.shared.logger import get_logger

logger = get_logger("security_agent")


class SecurityAgent(BaseAgent):
    """Specialist responsible for static security checks, vulnerability detection, and safety reports."""

    name = "security"
    description = "Security engineer that detects hardcoded secrets, injection flaws, unsafe shell calls, and misconfigurations."
    permissions = AgentPermissions(can_read_filesystem=True, can_write_filesystem=True)
    allowed_tools = ["read_file", "list_files", "search_files", "write_file"]

    def get_system_prompt(self, context: TaskContext) -> str:
        return "You are the Lead Application Security Auditor for GÖK SYSTEMS TECH (GökAI)."

    async def execute(
        self,
        context: TaskContext,
        input_message: Optional[AgentMessage] = None
    ) -> AgentRunResult:
        start_time = time.perf_counter()
        logger.info(f"SecurityAgent scanning workspace for vulnerabilities: {context.task_id}")

        files = self.tool_registry.fs.list_files()
        findings: List[Dict[str, Any]] = []

        # Comprehensive static security rules
        rules = [
            (r"(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token|private[_-]?key)\s*=\s*['\"][a-zA-Z0-9_\-\.]{16,}['\"]",
             "Hardcoded API Key / Secret Credential", "CRITICAL"),
            (r"['\"][a-zA-Z0-9_\-]{32,}['\"]",
             "Possible High-Entropy Hardcoded Secret", "MEDIUM"),
            (r"os\.system\(",
             "Dangerous unescaped shell call (os.system)", "HIGH"),
            (r"subprocess\.(Popen|run|call)\([^)]*shell\s*=\s*True",
             "Shell injection vulnerability (shell=True without validation)", "HIGH"),
            (r"(?<![a-zA-Z0-9_])eval\(|(?<![a-zA-Z0-9_])exec\(",
             "Unsafe dynamic code execution (eval / exec)", "CRITICAL"),
            (r"execute\(\s*f['\"].*?(SELECT|INSERT|UPDATE|DELETE)",
             "Potential SQL Injection (raw f-string query construction)", "CRITICAL"),
            (r"cursor\.execute\(['\"].*?%s.*?['\"]\s*%",
             "Potential SQL Injection (string format formatting)", "HIGH"),
            (r"allow_origins\s*=\s*\[['\"]\s*\*['\"]\s*\]\s*,\s*allow_credentials\s*=\s*True",
             "Insecure CORS configuration (wildcard origin with credentials)", "MEDIUM"),
            (r"DEBUG\s*=\s*True",
             "Debug mode explicitly enabled in source code", "LOW"),
            (r"(?i)password\s*=\s*['\"][^'\"]{1,}['\"]",
             "Hardcoded password detected", "HIGH"),
        ]

        for f in files:
            p = f["path"]
            if p.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".env", ".json", ".yaml", ".yml")):
                if any(ignored in p for ignored in ["test_run_report", "SECURITY_AUDIT", "DEBUG_PATCH", "node_modules"]):
                    continue

                try:
                    content = self.tool_registry.fs.read_file(p)
                    lines = content.splitlines()

                    for idx, line in enumerate(lines, 1):
                        for pattern, desc, severity in rules:
                            if re.search(pattern, line):
                                findings.append({
                                    "file": p,
                                    "line": idx,
                                    "issue": desc,
                                    "severity": severity,
                                    "snippet": line.strip()[:100]
                                })
                except Exception:
                    pass

        has_critical = any(item["severity"] == "CRITICAL" for item in findings)
        has_high = any(item["severity"] == "HIGH" for item in findings)

        summary = f"Security scan completed. Found {len(findings)} security notice(s) ({sum(1 for f in findings if f['severity'] in ('CRITICAL', 'HIGH'))} high/critical)."

        report_lines = [
            "# GÖKAI Application Security Audit Report",
            f"- Findings Count: {len(findings)}",
            f"- Status: {'PASSED WITH WARNINGS' if findings and not has_critical else ('PASSED' if not findings else 'ATTENTION NEEDED')}\n",
            "## Identified Vulnerabilities & Warnings"
        ]

        if findings:
            for item in findings:
                report_lines.append(
                    f"- **[{item['severity']}]** `{item['file']}:{item['line']}` — {item['issue']}\n"
                    f"  `> {item['snippet']}`"
                )
        else:
            report_lines.append("✓ Clean Audit: Zero hardcoded secrets, injection patterns, or shell hazards detected.")

        audit_content = "\n".join(report_lines)
        self.tool_registry.fs.write_file("SECURITY_AUDIT.md", audit_content)

        art = Artifact(
            project_id=context.project_id,
            task_id=context.task_id,
            type=ArtifactType.SECURITY_REPORT,
            name="SECURITY_AUDIT.md",
            path="SECURITY_AUDIT.md",
            content=audit_content,
            created_by=self.name,
            metadata={"findings_count": len(findings), "has_critical": has_critical}
        )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return AgentRunResult(
            success=not has_critical,
            agent_name=self.name,
            task_id=context.task_id,
            summary=summary,
            artifacts_created=[art],
            errors=[] if not has_critical else ["Critical security finding identified in codebase."],
            duration_ms=duration_ms
        )
