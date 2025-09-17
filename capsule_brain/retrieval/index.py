"""Simple retrieval helpers used by the Capsule Brain."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


async def retrieve_topk(query: str, k: int = 5) -> dict[str, Any]:
    """Return ``k`` mock retrieval results for ``query``.

    The implementation simulates latency and returns templated strings that
    roughly mimic the shape of search results one might expect from a retrieval
    service.
    """

    start = time.perf_counter()
    try:
        await asyncio.sleep(0.1)
        results = [
            f"Knowledge about {query} from scientific literature",
            f"Historical context related to {query}",
            f"Recent developments in {query} field",
            f"Technical specifications for {query}",
            f"Practical applications of {query}",
        ]

        return {
            "abstracts": results[:k],
            "lat_ms": (time.perf_counter() - start) * 1000,
            "total_results": len(results[:k]),
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Retrieval failed: %s", exc)
        return {
            "abstracts": [],
            "lat_ms": (time.perf_counter() - start) * 1000,
            "error": str(exc),
        }
