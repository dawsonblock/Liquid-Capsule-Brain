"""In-memory retrieval helpers used by Capsule Brain."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

log = logging.getLogger(__name__)


async def retrieve_topk(query: str, k: int = 5) -> dict[str, Any]:
    """Return mock retrieval results for *query*.

    The implementation is intentionally lightweight and deterministic so tests can
    rely on consistent payloads without external network calls.
    """

    start = time.perf_counter()
    try:
        await asyncio.sleep(0.1)
        candidate_results = [
            f"Knowledge about {query} from scientific literature",
            f"Historical context related to {query}",
            f"Recent developments in {query} field",
            f"Technical specifications for {query}",
            f"Practical applications of {query}",
        ]

        return {
            "abstracts": candidate_results[:k],
            "lat_ms": (time.perf_counter() - start) * 1000,
            "total_results": len(candidate_results[:k]),
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        log.error("Retrieval failed: %s", exc)
        return {
            "abstracts": [],
            "lat_ms": (time.perf_counter() - start) * 1000,
            "error": str(exc),
        }
