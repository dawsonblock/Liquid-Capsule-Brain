"""Input sanitisation helpers for request and tool payloads."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any

log = logging.getLogger(__name__)

_SANITIZE_PATTERN = re.compile(r"[<>'\"]")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def sanitize_input(raw: str | Any) -> str:
    """Strip dangerous characters and collapse whitespace from user input."""

    if not isinstance(raw, str):
        raw = str(raw)
    cleaned = _SANITIZE_PATTERN.sub("", raw)
    cleaned = cleaned[:2000]
    return _WHITESPACE_PATTERN.sub(" ", cleaned).strip()


def _coerce_sequence(values: Sequence[Any]) -> list[str]:
    return [sanitize_input(str(item)) for item in values[:10]]


def validate_tool_params(params: Mapping[str, Any]) -> dict[str, Any]:
    """Ensure tool parameters contain safe, bounded values."""

    clean: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, str):
            clean[key] = sanitize_input(value)
        elif isinstance(value, int | float | bool):
            clean[key] = value
        elif isinstance(value, Sequence) and not isinstance(value, (str | bytes | bytearray)):
            clean[key] = _coerce_sequence(value)
        else:  # pragma: no cover - log unexpected types for observability
            log.debug("Dropping unsupported tool parameter %s=%r", key, value)
    return clean
