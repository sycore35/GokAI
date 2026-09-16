---
name: python-engineering
description: Python best practices, type hints, and clean code
when_to_use: "Use when creating Python scripts, CLI tools, libraries, or backend code"
tags: ["python", "cli", "backend", "scripting"]
---

# Python Engineering Guidelines

1. Always use Python 3.11+ type hints (e.g. `list[str]`, `dict[str, Any]`, `Optional[T]`).
2. Write clean docstrings on public functions and classes.
3. Handle exceptions specifically; avoid bare `except:`.
4. Use standard library modules (`pathlib`, `argparse`, `dataclasses`, `logging`) whenever external libraries are not strictly required.
5. Create comprehensive unit tests using `pytest` or `unittest`.
