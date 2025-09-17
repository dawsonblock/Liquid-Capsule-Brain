"""Mock retrieval pipeline used for tool demonstrations."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

log = logging.getLogger(__name__)


async def retrieve_topk(query: str, k: int = 5) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        await asyncio.sleep(0.05)
        mock_results = [
            {"title": f"Result {index}", "snippet": f"Snippet for {query} #{index}"}
            for index in range(1, k + 1)
        ]
        return {
            "abstracts": mock_results,
            "lat_ms": (time.perf_counter() - start) * 1000,
            "total_results": len(mock_results),
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        log.error("Retrieval failed: %s", exc)
        return {
            "abstracts": [],
            "lat_ms": (time.perf_counter() - start) * 1000,
            "error": str(exc),
        }
