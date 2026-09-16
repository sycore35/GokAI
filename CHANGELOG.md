# Changelog — GökAI Platform

All notable changes to the **GökAI** platform will be documented in this file.

---

## [1.0.0] — GökAI V1 Release (2026-09)

### 🌟 Core Release Highlights
- **100% Independent Runtime**: Completely standalone platform runnable on Windows, macOS, and Linux with zero external IDE dependencies.
- **Multi-Agent Orchestrator**: Fully autonomous pipeline coordinating 7 specialist agents:
  - **Orchestrator Agent**: Decomposes natural language objectives into verifiable Directed Acyclic Graph (DAG) task steps.
  - **Developer Agent**: Writes production-grade source code with framework adherence and type safety.
  - **Tester Agent**: Executes real unit/integration tests (`pytest`, `unittest`, `npm test`) and collects exit codes, stdout, and tracebacks.
  - **Debugger Agent**: Automated self-healing loop that parses test failures, diagnoses root causes, and applies verified patches (up to configured max debug cycles).
  - **Security Auditor**: Scans source code for vulnerabilities (hardcoded secrets, path traversals, insecure subprocess calls, OWASP top 10).
  - **Reviewer Agent**: Conducts automated code quality, formatting, and design pattern reviews.
  - **Researcher Agent**: Inspects workspace dependencies, requirements, and library ecosystem before code generation.
- **Intelligent Model Router**:
  - Out-of-the-box support for Google Gemini, OpenAI, DeepSeek, Anthropic Claude, NVIDIA Cloud NIM, and OpenRouter.
  - Automated multi-tier fallback chain ensuring uninterrupted generation.
  - Internal deterministic Mock Provider for zero-config offline development and CI testing.
  - Live connectivity testing with real-time latency measurement in UI.
- **Interactive AI Chat System**:
  - Dedicated interactive engineering chat view.
  - Project-aware context injection (workspace files, architecture decisions, memory facts).
  - Drag-and-drop and file picker for code and image attachments.
  - Conversation history persistence and retry capabilities.
- **Domain Skills Management**:
  - Real graphical UI for browsing, creating, editing, and deleting domain skills.
  - Built-in vs. Custom skill categorization.
  - Real-time enable/disable toggles per skill.
  - YAML frontmatter validation.
- **Isolated Execution Sandboxing**:
  - Path-traversal-proof `JailedFileSystem` preventing directory escape.
  - Process-jailed `SandboxedTerminal` with strict timeouts and resource limits.
  - Headless Browser Verification tool for web apps.
  - Optional Docker container isolation when Docker daemon is detected.
- **Developer Diagnostics ("D" Menu)**:
  - Global keyboard shortcut (`D`) opening live system telemetry.
  - Host platform, Python runtime, database health, and process statistics.
  - One-click temporary cache cleaning and runtime configuration reloading.
  - Live backend activity log tail.
- **Cross-Platform Native Launchers**:
  - `Run-Windows.bat`: One-click native launcher for Windows with dependency verification and auto-browser launch.
  - `Run-macOS.command`: Native executable launcher for macOS Finder.
  - `run-linux.sh`: Native shell script for Linux workstations.
- **Modern UI & Localization**:
  - Full Dark, Light, and System theme support with instant persistence.
  - Comprehensive English (`en`) and Turkish (`tr`) bilingual localization.
