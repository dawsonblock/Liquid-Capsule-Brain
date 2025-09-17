"""Planning utilities for generating tool hints."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

_NEWS_KEYWORDS = {"latest", "current", "recent", "news"}
_MATH_KEYWORDS = {"calculate", "compute", "math"}


async def plan_once(query: str) -> dict[str, Any]:
    """Generate a single planning response for the supplied ``query``.

    The planner inspects the text and produces tool hints that downstream
    components can use to decide whether to invoke capabilities such as
    local search or a calculator.  The latency of the planning step is also
    recorded to aid in monitoring.
    """

    start = time.perf_counter()
    tool_hints: list[dict[str, str]] = []

    try:
        lower_query = query.lower()

        if any(keyword in lower_query for keyword in _NEWS_KEYWORDS):
            tool_hints.append(
                {
                    "tool": "local_search",
                    "query": query,
                    "priority": "high",
                }
            )

        if any(keyword in lower_query for keyword in _MATH_KEYWORDS):
            tool_hints.append(
                {
                    "tool": "calculator",
                    "expression": query,
                    "priority": "medium",
                }
            )

        await asyncio.sleep(0.05)

        return {
            "tool_hints": tool_hints,
            "reasoning_steps": "direct_response" if not tool_hints else "tool_assisted",
            "confidence": 0.8,
            "lat_ms": (time.perf_counter() - start) * 1000,
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Planning failed")
        return {
            "tool_hints": [],
            "reasoning_steps": "fallback",
            "lat_ms": (time.perf_counter() - start) * 1000,
            "error": str(exc),
        }
