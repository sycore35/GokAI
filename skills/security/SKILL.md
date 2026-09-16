---
name: secure-coding-standards
description: OWASP Top 10 prevention, secret handling, and input sanitization
when_to_use: "Use when creating APIs, database layers, auth flows, or handling user inputs"
tags: ["security", "owasp", "auth", "secrets", "validation", "sanitization"]
---

# Secure Coding Guidelines

1. Never hardcode API keys, database passwords, or JWT secrets in source code; always use `.env` or system environment variables.
2. Never concatenate user input directly into shell commands (`shell=True`) or SQL queries.
3. Use parameterized queries or ORM models (SQLAlchemy, Prisma) to prevent SQL injection.
4. Validate and sanitize all incoming payloads with Pydantic or schema validators.
5. Confine all file system reads and writes to authorized project directory boundaries.
