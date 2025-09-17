from __future__ import annotations

import asyncio
import logging
import time

log = logging.getLogger(__name__)


async def retrieve_topk(query: str, k: int = 5) -> dict[str, object]:
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
        log.error("Retrieval failed: %s", exc)
        return {
            "abstracts": [],
            "lat_ms": (time.perf_counter() - start) * 1000,
            "error": str(exc),
        }
