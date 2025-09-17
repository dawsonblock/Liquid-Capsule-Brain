"""Utilities for sanitising user-provided input before tool execution."""

from __future__ import annotations

import logging
import re
from typing import Any

log = logging.getLogger(__name__)


def sanitize_input(raw_value: str) -> str:
    """Return a conservative sanitised representation of *raw_value*.

    The sanitisation trims whitespace, removes characters that are commonly used in
    HTML/script injection, and bounds the length so downstream systems do not need
    to implement defensive slicing repeatedly.
    """

    if not isinstance(raw_value, str):
        return ""

    scrubbed = re.sub(r'[<>"\']', "", raw_value)
    truncated = scrubbed[:2000]
    normalised = re.sub(r"\s+", " ", truncated).strip()
    return normalised


def _coerce_sequence(values: list[Any] | tuple[Any, ...] | set[Any]) -> list[str]:
    return [sanitize_input(str(value)) for value in values]


def validate_tool_params(params: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *params* with any string-like values sanitised."""

    cleaned: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, str):
            cleaned[key] = sanitize_input(value)
        elif isinstance(value, int | float | bool):
            cleaned[key] = value
        elif isinstance(value, list | tuple | set):
            truncated = list(value)[:10]
            cleaned[key] = _coerce_sequence(truncated)

    return cleaned
