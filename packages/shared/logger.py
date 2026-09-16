"""
GÖK SYSTEMS TECH — GökAI Structured & Redacting Logger
Filters API keys and sensitive tokens before writing to logs.
"""

import logging
import re
import sys
from typing import Any

# Regex patterns for common API keys
SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE),
    re.compile(r"nvapi-[a-zA-Z0-9-_]{30,}", re.IGNORECASE),
]


class RedactingFormatter(logging.Formatter):
    """Custom logging formatter that masks sensitive secrets."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        redacted = original
        for pattern in SECRET_PATTERNS:
            redacted = pattern.sub("[REDACTED_API_KEY]", redacted)
        return redacted


def get_logger(name: str = "gokai") -> logging.Logger:
    """Returns a pre-configured logger with secret redaction."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = RedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
