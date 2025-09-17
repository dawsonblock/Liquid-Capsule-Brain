"""Self-wiring routines that mutate engine state based on metrics."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - only for typing
    from asyncio import Queue

    from .capsule_engine import CapsuleEngine

log = logging.getLogger(__name__)

class SelfWirer:
    """Proposes safe, local edits to improve integration (Φ) and manage memory size."""

    def __init__(self, engine: CapsuleEngine, interval: int = 60) -> None:
        self.engine = engine
        self.interval = interval
        self.performance_history: list[dict[str, float | int]] = []
        self.last_proposal_time = 0.0

    async def run(self, bus: Queue[dict[str, Any]]) -> None:
        while not self.engine._shutdown_event.is_set():
            await asyncio.sleep(self.interval)
            try:
                edits = self._propose_edits()
                if edits:
                    await bus.put({"type": "self_wiring_proposal", "edits": edits, "ts": time.time()})
                    self.last_proposal_time = time.time()
            except Exception as exc:  # pragma: no cover - defensive logging
                log.exception("Self-wiring error: %s", exc)

    def _propose_edits(self) -> list[dict[str, Any]]:
        metrics = self.engine.iit_analyzer.get_latest_metrics()
        self.performance_history.append(
            {"ts": time.time(), "phi": metrics.get("phi", 0.0), "mem": len(self.engine.memory)}
        )
        self.performance_history = self.performance_history[-200:]
        if time.time() - self.last_proposal_time < 300:
            return []

        edits: list[dict[str, Any]] = []
        phi = metrics.get("phi", 0.0)
        if phi < 1.0 and self.engine.knowledge_graph.number_of_nodes() >= 2:
            nodes = list(self.engine.knowledge_graph.nodes())
            a = random.choice(nodes)
            b = random.choice(nodes)
            if a != b:
                edits.append({"type": "graph_edge_add", "source": a, "target": b, "reason": f"Low phi {phi:.2f}"})
        if len(self.engine.memory) > 1000:
            edits.append({"type": "memory_trim", "target_size": 800, "reason": "Memory approaching capacity"})
        return edits[:3]

    def summary(self) -> dict[str, float | int]:
        if not self.performance_history:
            return {}
        tail = self.performance_history[-20:]
        avg_phi = sum(float(x["phi"]) for x in tail) / len(tail)
        return {"avg_phi": avg_phi, "n": len(tail)}
