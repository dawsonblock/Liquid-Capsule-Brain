import logging
import re
from collections.abc import Mapping
from typing import Any

log = logging.getLogger(__name__)


def sanitize_input(raw: str) -> str:
    if not isinstance(raw, str):
        return ""

    cleaned = re.sub(r"[<>\"']", "", raw)
    cleaned = cleaned[:2000]
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def validate_tool_params(params: Mapping[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_input(value)
        elif isinstance(value, int | float | bool):
            sanitized[key] = value
        elif isinstance(value, list):
            sanitized[key] = [sanitize_input(str(item)) for item in value[:10]]
    return sanitized
