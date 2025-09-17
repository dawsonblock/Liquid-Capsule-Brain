"""Utilities for retrieving background knowledge."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_RESULTS = [
    "Knowledge about {query} from scientific literature",
    "Historical context related to {query}",
    "Recent developments in {query} field",
    "Technical specifications for {query}",
    "Practical applications of {query}",
]


async def retrieve_topk(query: str, k: int = 5) -> dict[str, Any]:
    """Return up to ``k`` mock retrieval results for ``query``."""

    start = time.perf_counter()

    try:
        await asyncio.sleep(0.1)
        results = [item.format(query=query) for item in _DEFAULT_RESULTS][:k]
        return {
            "abstracts": results,
            "lat_ms": (time.perf_counter() - start) * 1000,
            "total_results": len(results),
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Retrieval failed")
        return {
            "abstracts": [],
            "lat_ms": (time.perf_counter() - start) * 1000,
            "error": str(exc),
        }
