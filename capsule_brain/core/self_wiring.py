"""Logic for proposing self-wiring updates to the knowledge graph."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any

logger = logging.getLogger(__name__)


class SelfWirer:
    """Propose safe, local edits to improve integration (Φ) and manage memory size."""

    def __init__(self, engine: Any, interval: int = 60) -> None:
        self.engine = engine
        self.interval = interval
        self.performance_history: list[dict[str, Any]] = []
        self.last_proposal_time = 0.0

    async def run(self, bus: asyncio.Queue | None) -> None:
        while not self.engine._shutdown_event.is_set():
            await asyncio.sleep(self.interval)
            try:
                edits = self._propose_edits()
                if edits and bus:
                    await bus.put(
                        {"type": "self_wiring_proposal", "edits": edits, "ts": time.time()}
                    )
                    self.last_proposal_time = time.time()
            except Exception:  # pragma: no cover - defensive logging
                logger.exception("Self-wiring error")

    def _propose_edits(self) -> list[dict[str, Any]]:
        metrics = self.engine.iit_analyzer.get_latest_metrics()
        self.performance_history.append(
            {
                "ts": time.time(),
                "phi": metrics.get("phi", 0.0),
                "mem": len(self.engine.memory),
            }
        )
        self.performance_history = self.performance_history[-200:]
        if time.time() - self.last_proposal_time < 300:
            return []
        edits: list[dict[str, Any]] = []
        phi = metrics.get("phi", 0.0)
        if phi < 1.0 and self.engine.knowledge_graph.number_of_nodes() >= 2:
            nodes = list(self.engine.knowledge_graph.nodes())
            node_a = random.choice(nodes)
            node_b = random.choice(nodes)
            if node_a != node_b:
                edits.append(
                    {
                        "type": "graph_edge_add",
                        "source": node_a,
                        "target": node_b,
                        "reason": f"Low phi {phi:.2f}",
                    }
                )
        if len(self.engine.memory) > 1000:
            edits.append(
                {
                    "type": "memory_trim",
                    "target_size": 800,
                    "reason": "Memory approaching capacity",
                }
            )
        return edits[:3]

    def summary(self) -> dict[str, Any]:
        if not self.performance_history:
            return {}
        tail = self.performance_history[-20:]
        avg_phi = sum(item["phi"] for item in tail) / len(tail)
        return {"avg_phi": float(avg_phi), "n": len(tail)}
