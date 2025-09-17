from __future__ import annotations

import logging
import re
from typing import Any

log = logging.getLogger(__name__)


def sanitize_input(value: str) -> str:
    if not isinstance(value, str):
        return ""

    sanitized = re.sub(r'[<>"\']', "", value)
    sanitized = sanitized[:2000]
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized


def validate_tool_params(params: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, raw_value in params.items():
        if isinstance(raw_value, str):
            clean[key] = sanitize_input(raw_value)
        elif isinstance(raw_value, int | float | bool):
            clean[key] = raw_value
        elif isinstance(raw_value, list):
            clean[key] = [sanitize_input(str(item)) for item in raw_value[:10]]
    return clean
