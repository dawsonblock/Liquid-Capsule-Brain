"""Planning utilities for selecting tools for a query."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

_TOOL_HINT_KEYWORDS: dict[str, list[str]] = {
    "local_search": ["latest", "current", "recent", "news"],
    "calculator": ["calculate", "compute", "math"],
}


async def plan_once(query: str) -> dict[str, Any]:
    """Generate a simple planning response for the provided ``query``.

    The implementation is intentionally lightweight: it inspects the query for
    a handful of keywords and decides whether any built-in tools should be
    suggested.  A small artificial delay is added to simulate work being done.
    """

    start = time.perf_counter()
    try:
        tool_hints: list[dict[str, Any]] = []
        lower_query = query.lower()

        if any(keyword in lower_query for keyword in _TOOL_HINT_KEYWORDS["local_search"]):
            tool_hints.append(
                {
                    "tool": "local_search",
                    "query": query,
                    "priority": "high",
                }
            )

        if any(keyword in lower_query for keyword in _TOOL_HINT_KEYWORDS["calculator"]):
            tool_hints.append(
                {
                    "tool": "calculator",
                    "expression": query,
                    "priority": "medium",
                }
            )

        await asyncio.sleep(0.05)

        reasoning_steps = "direct_response" if not tool_hints else "tool_assisted"
        return {
            "tool_hints": tool_hints,
            "reasoning_steps": reasoning_steps,
            "confidence": 0.8,
            "lat_ms": (time.perf_counter() - start) * 1000,
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Planning failed: %s", exc)
        return {
            "tool_hints": [],
            "reasoning_steps": "fallback",
            "lat_ms": (time.perf_counter() - start) * 1000,
            "error": str(exc),
        }
