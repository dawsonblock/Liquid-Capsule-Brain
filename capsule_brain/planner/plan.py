from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

log = logging.getLogger(__name__)


async def plan_once(query: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        tool_hints: list[dict[str, Any]] = []
        lowered = query.lower()
        if any(keyword in lowered for keyword in ["latest", "current", "recent", "news"]):
            tool_hints.append({"tool": "local_search", "query": query, "priority": "high"})
        if any(keyword in lowered for keyword in ["calculate", "compute", "math"]):
            tool_hints.append({"tool": "calculator", "expression": query, "priority": "medium"})
        await asyncio.sleep(0.05)
        return {
            "tool_hints": tool_hints,
            "reasoning_steps": "tool_assisted" if tool_hints else "direct_response",
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
