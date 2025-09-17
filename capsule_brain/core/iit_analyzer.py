"""Crude IIT-inspired analyzer for tracking integration metrics."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import TYPE_CHECKING, Any

import networkx as nx

log = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover
    from asyncio import Queue

    from .capsule_engine import CapsuleEngine

class IITAnalyzer:
    """Lightweight network-based Φ surrogate using clustering × density × size."""

    def __init__(self, engine: CapsuleEngine) -> None:
        self.engine = engine
        self.current_phi: float = 0.0
        self.current_glyphs: list[str] = []
        self.graph = nx.Graph()
        self.last_analysis = time.time()
        self.max_nodes_eval = 200
        self.analysis_interval = 5  # seconds
        self._initialize_graph()

    def _initialize_graph(self) -> None:
        for i in range(8):
            self.graph.add_node(f"n{i}")
        for i in range(7):
            self.graph.add_edge(f"n{i}", f"n{i+1}")
        self.engine.knowledge_graph = self.graph

    def get_initial_graph(self) -> nx.Graph:
        return self.graph

    def get_latest_metrics(self) -> dict[str, Any]:
        return {"phi": float(self.current_phi), "glyphs": list(self.current_glyphs), "last": self.last_analysis}

    def _compute_phi(self) -> None:
        n_nodes = self.graph.number_of_nodes()
        if n_nodes < 2:
            self.current_phi, self.current_glyphs = 0.0, []
            return

        sample_nodes = list(self.graph.nodes())[: min(n_nodes, self.max_nodes_eval)]
        sub_graph = self.graph.subgraph(sample_nodes)
        try:
            clustering = nx.average_clustering(sub_graph)
        except Exception:  # pragma: no cover - defensive
            clustering = 0.0
        density = nx.density(sub_graph)
        phi = max(0.0, min(clustering * density * n_nodes, 10.0))
        self.current_phi = float(phi)

        glyphs = ["○", "◎", "◉"]
        self.current_glyphs = [glyphs[min(int(phi // 1.5), 2)]]
        if n_nodes > 20:
            self.current_glyphs.append("⬡")
        if density > 0.3:
            self.current_glyphs.append("▣")
        self.last_analysis = time.time()

    async def run_analysis_loop(self, bus: Queue[dict[str, Any]]) -> None:
        while not self.engine._shutdown_event.is_set():
            try:
                if random.random() < 0.2 and self.graph.number_of_nodes() < 300:
                    a = f"n{random.randint(0, 9999)}"
                    b = f"n{random.randint(0, 9999)}"
                    self.graph.add_node(a)
                    self.graph.add_node(b)
                    self.graph.add_edge(a, b)
                self._compute_phi()
                await bus.put({"type": "phi_update", "phi": self.current_phi})
            except Exception as exc:  # pragma: no cover - defensive logging
                log.exception("IIT compute error: %s", exc)
                self.current_phi, self.current_glyphs = 0.0, []
            await asyncio.sleep(self.analysis_interval)
