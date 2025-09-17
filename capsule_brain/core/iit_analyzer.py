from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any

import networkx as nx

log = logging.getLogger(__name__)


class IITAnalyzer:
    """Lightweight network-based Φ surrogate using clustering × density × size."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine
        self.current_phi: float = 0.0
        self.current_glyphs: list[str] = []
        self.graph = nx.Graph()
        self.last_analysis = time.time()
        self.max_nodes_eval = 200
        self.analysis_interval = 5  # seconds
        self._initialize_graph()

    def _initialize_graph(self) -> None:
        for idx in range(8):
            self.graph.add_node(f"n{idx}")
        for idx in range(7):
            self.graph.add_edge(f"n{idx}", f"n{idx + 1}")
        self.engine.knowledge_graph = self.graph

    def get_initial_graph(self) -> nx.Graph:
        return self.graph

    def get_latest_metrics(self) -> dict[str, Any]:
        return {
            "phi": float(self.current_phi),
            "glyphs": list(self.current_glyphs),
            "last": self.last_analysis,
        }

    def _compute_phi(self) -> None:
        node_count = self.graph.number_of_nodes()
        if node_count < 2:
            self.current_phi = 0.0
            self.current_glyphs = []
            return

        sample_nodes = list(self.graph.nodes())[: min(node_count, self.max_nodes_eval)]
        subgraph = self.graph.subgraph(sample_nodes)
        try:
            clustering = nx.average_clustering(subgraph)
        except Exception:  # pragma: no cover - library edge cases
            clustering = 0.0
        density = nx.density(subgraph)
        phi_value = max(0.0, min(clustering * density * node_count, 10.0))
        self.current_phi = float(phi_value)
        glyphs = ["○", "◎", "◉"]
        glyph_index = min(int(phi_value // 1.5), len(glyphs) - 1)
        self.current_glyphs = [glyphs[glyph_index]]
        if node_count > 20:
            self.current_glyphs.append("⬡")
        if density > 0.3:
            self.current_glyphs.append("▣")
        self.last_analysis = time.time()

    async def run_analysis_loop(self, bus: asyncio.Queue[Any]) -> None:
        while not self.engine._shutdown_event.is_set():
            try:
                if random.random() < 0.2 and self.graph.number_of_nodes() < 300:
                    node_a = f"n{random.randint(0, 9999)}"
                    node_b = f"n{random.randint(0, 9999)}"
                    self.graph.add_node(node_a)
                    self.graph.add_node(node_b)
                    self.graph.add_edge(node_a, node_b)
                self._compute_phi()
            except Exception as exc:  # pragma: no cover - defensive logging
                log.error("IIT compute error: %s", exc)
                self.current_phi = 0.0
                self.current_glyphs = []
            await asyncio.sleep(self.analysis_interval)
