"""Input sanitisation helpers for tool invocations."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any

logger = logging.getLogger(__name__)

_DANGEROUS_CHARS = re.compile(r"[<>\"']")
_WHITESPACE_RE = re.compile(r"\s+")


def sanitize_input(value: str) -> str:
    """Return a sanitised representation of ``value``.

    Strings are truncated to a reasonable size and stripped of characters that
    commonly lead to HTML or command-injection issues.
    """

    if not isinstance(value, str):
        logger.warning("sanitize_input expected str, received %s", type(value))
        return ""

    cleaned = _DANGEROUS_CHARS.sub("", value)
    cleaned = cleaned[:2000]
    cleaned = _WHITESPACE_RE.sub(" ", cleaned)
    return cleaned.strip()


def validate_tool_params(params: Mapping[str, Any]) -> dict[str, Any]:
    """Clean a mapping of tool parameters.

    Strings are sanitised, primitive numeric and boolean values are forwarded
    unchanged, and sequences are truncated to a sensible length with each item
    normalised to a string representation.
    """

    clean_params: dict[str, Any] = {}

    for key, value in params.items():
        if isinstance(value, str):
            clean_params[key] = sanitize_input(value)
        elif isinstance(value, (int | float | bool)):
            clean_params[key] = value
        elif isinstance(value, Sequence) and not isinstance(
            value, str | bytes | bytearray
        ):
            clean_params[key] = [sanitize_input(str(item)) for item in value[:10]]
        else:
            logger.debug("Dropping unsupported parameter %s", key)

    return clean_params
