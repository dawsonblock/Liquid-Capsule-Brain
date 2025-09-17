from __future__ import annotations

import logging
import re
from typing import Any


log = logging.getLogger(__name__)


_TAG_PATTERN = re.compile(r"[<>\"']")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def sanitize_input(raw_value: str) -> str:
    """Return a normalized, sanitized representation of ``raw_value``."""

    if not isinstance(raw_value, str):
        return ""

    cleaned = _TAG_PATTERN.sub("", raw_value)
    cleaned = cleaned[:2000]
    cleaned = _WHITESPACE_PATTERN.sub(" ", cleaned).strip()
    return cleaned


def validate_tool_params(params: dict[str, Any]) -> dict[str, Any]:
    """Sanitize user-provided tool parameters while preserving primitives."""

    sanitized: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_input(value)
        elif isinstance(value, (int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, list):
            sanitized[key] = [sanitize_input(str(item)) for item in value[:10]]
        else:
            log.debug("Dropping unsupported tool parameter %s=%r", key, value)
    return sanitized
