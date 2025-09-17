"""Input sanitisation helpers for Capsule Brain."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_SANITIZE_PATTERN = re.compile(r"[<>\"']")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def sanitize_input(raw_value: str) -> str:
    """Return a cleaned version of ``raw_value`` safe for downstream use."""

    if not isinstance(raw_value, str):
        logger.debug("sanitize_input received non-string input: %r", raw_value)
        return ""

    trimmed = _SANITIZE_PATTERN.sub("", raw_value)
    trimmed = trimmed[:2000]
    return _WHITESPACE_PATTERN.sub(" ", trimmed).strip()


def _sanitize_sequence(values: list[Any]) -> list[str]:
    """Sanitise a sequence of values by converting them to strings."""

    return [sanitize_input(str(value)) for value in values[:10]]


def validate_tool_params(params: dict[str, Any]) -> dict[str, Any]:
    """Sanitise tool invocation parameters.

    Strings are cleaned using :func:`sanitize_input`, booleans and numeric types
    are passed through untouched, and short lists are sanitised element-wise.
    """

    clean: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, str):
            clean[key] = sanitize_input(value)
        elif isinstance(value, int | float | bool):
            clean[key] = value
        elif isinstance(value, list):
            clean[key] = _sanitize_sequence(value)

    return clean
