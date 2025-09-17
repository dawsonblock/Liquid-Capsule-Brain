"""Simple heuristics that propose self-wiring improvements."""
from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any

log = logging.getLogger(__name__)


class SelfWirer:
    """Proposes safe, local edits to improve integration (Φ) and manage memory size."""

    def __init__(self, engine: Any, interval: int = 60) -> None:
        self.engine = engine
        self.interval = interval
        self.performance_history: list[dict[str, float]] = []
        self.last_proposal_time = 0.0

    async def run(self, bus: asyncio.Queue[dict[str, Any]]) -> None:
        while not self.engine._shutdown_event.is_set():
            await asyncio.sleep(self.interval)
            try:
                edits = self._propose_edits()
                if edits:
                    await bus.put(
                        {"type": "self_wiring_proposal", "edits": edits, "ts": time.time()}
                    )
                    self.last_proposal_time = time.time()
            except Exception as exc:  # pragma: no cover - defensive logging
                log.error("Self-wiring error: %s", exc)

    def _propose_edits(self) -> list[dict[str, Any]]:
        metrics = self.engine.iit_analyzer.get_latest_metrics()
        self.performance_history.append(
            {
                "ts": time.time(),
                "phi": float(metrics.get("phi", 0.0)),
                "mem": float(len(self.engine.memory)),
            }
        )
        self.performance_history = self.performance_history[-200:]
        if time.time() - self.last_proposal_time < 300:
            return []

        proposals: list[dict[str, Any]] = []
        phi = float(metrics.get("phi", 0.0))
        if phi < 1.0 and self.engine.knowledge_graph.number_of_nodes() >= 2:
            nodes = list(self.engine.knowledge_graph.nodes())
            source = random.choice(nodes)
            target = random.choice(nodes)
            if source != target:
                proposals.append(
                    {
                        "type": "graph_edge_add",
                        "source": source,
                        "target": target,
                        "reason": f"Low phi {phi:.2f}",
                    }
                )
        if len(self.engine.memory) > 1_000:
            proposals.append(
                {
                    "type": "memory_trim",
                    "target_size": 800,
                    "reason": "Memory approaching capacity",
                }
            )
        return proposals[:3]

    def summary(self) -> dict[str, float | int]:
        if not self.performance_history:
            return {}
        tail = self.performance_history[-20:]
        average_phi = sum(entry["phi"] for entry in tail) / len(tail)
        return {"avg_phi": float(average_phi), "n": len(tail)}
