"""Heuristic planning helpers for Capsule Brain."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

log = logging.getLogger(__name__)

NEWS_HINT_KEYWORDS = ("latest", "current", "recent", "news")
MATH_HINT_KEYWORDS = ("calculate", "compute", "math")


async def plan_once(query: str) -> dict[str, Any]:
    """Produce a simple tool-selection plan based on the incoming query."""

    start = time.perf_counter()
    tool_hints: list[dict[str, str]] = []
    lower_query = query.lower()

    if any(keyword in lower_query for keyword in NEWS_HINT_KEYWORDS):
        tool_hints.append({"tool": "local_search", "query": query, "priority": "high"})

    if any(keyword in lower_query for keyword in MATH_HINT_KEYWORDS):
        tool_hints.append({"tool": "calculator", "expression": query, "priority": "medium"})

    try:
        await asyncio.sleep(0.05)
        return {
            "tool_hints": tool_hints,
            "reasoning_steps": "direct_response" if not tool_hints else "tool_assisted",
            "confidence": 0.8,
            "lat_ms": (time.perf_counter() - start) * 1000,
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        log.exception("Planning failed: %s", exc)
        return {
            "tool_hints": [],
            "reasoning_steps": "fallback",
            "lat_ms": (time.perf_counter() - start) * 1000,
            "error": str(exc),
        }
