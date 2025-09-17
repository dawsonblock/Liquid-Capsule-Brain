"""Heuristic planning helpers used by the Capsule Brain."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

log = logging.getLogger(__name__)


async def plan_once(query: str) -> dict[str, Any]:
    """Return a lightweight plan describing which tools to consult for *query*.

    The planner is intentionally simple: it looks for a couple of keyword families
    and promotes matching tools so other subsystems can fan out the work.  The
    function also records the approximate latency so callers can reason about the
    responsiveness of the planning loop.
    """

    start = time.perf_counter()
    try:
        tool_hints: list[dict[str, str]] = []
        normalized_query = query.lower()

        if any(keyword in normalized_query for keyword in {"latest", "current", "recent", "news"}):
            tool_hints.append(
                {
                    "tool": "local_search",
                    "query": query,
                    "priority": "high",
                }
            )

        if any(keyword in normalized_query for keyword in {"calculate", "compute", "math"}):
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
        log.error("Planning failed: %s", exc)
        return {
            "tool_hints": [],
            "reasoning_steps": "fallback",
            "lat_ms": (time.perf_counter() - start) * 1000,
            "error": str(exc),
        }
