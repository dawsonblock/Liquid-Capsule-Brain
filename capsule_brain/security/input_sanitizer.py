"""Utilities for cleaning user-supplied input before tool execution."""
from __future__ import annotations

import logging
import re
from typing import Any

log = logging.getLogger(__name__)

_SANITIZE_PATTERN = re.compile(r"[<>\"']")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def sanitize_input(value: str) -> str:
    if not isinstance(value, str):
        return ""
    cleaned = _SANITIZE_PATTERN.sub("", value)
    cleaned = cleaned[:2000]
    cleaned = _WHITESPACE_PATTERN.sub(" ", cleaned).strip()
    return cleaned


def validate_tool_params(params: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, str):
            clean[key] = sanitize_input(value)
        elif isinstance(value, int | float | bool):
            clean[key] = value
        elif isinstance(value, list):
            clean[key] = [sanitize_input(str(item)) for item in value[:10]]
        else:
            log.debug("Dropping unsupported param %s=%r", key, value)
    return clean
