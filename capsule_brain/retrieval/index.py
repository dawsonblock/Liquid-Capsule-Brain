"""Retrieval helpers that simulate a document index lookup."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

log = logging.getLogger(__name__)


async def retrieve_topk(query: str, k: int = 5) -> dict[str, Any]:
    """Return a deterministic set of synthetic abstracts for the supplied query."""

    start = time.perf_counter()
    try:
        await asyncio.sleep(0.1)
        candidates = [
            f"Knowledge about {query} from scientific literature",
            f"Historical context related to {query}",
            f"Recent developments in {query} field",
            f"Technical specifications for {query}",
            f"Practical applications of {query}",
        ]
        sliced = candidates[:k]
        return {
            "abstracts": sliced,
            "lat_ms": (time.perf_counter() - start) * 1000,
            "total_results": len(sliced),
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        log.exception("Retrieval failed: %s", exc)
        return {
            "abstracts": [],
            "lat_ms": (time.perf_counter() - start) * 1000,
            "error": str(exc),
        }
