from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from .alignment_core import AlignmentCore
from .belief_state_manager import BeliefStateManager
from .iit_analyzer import IITAnalyzer
from .self_wiring import SelfWirer

log = logging.getLogger(__name__)


class CapsuleEngine:
    def __init__(self) -> None:
        self.start_time = time.time()
        self.alignment_core = AlignmentCore()
        self.belief_state_manager = BeliefStateManager(self)
        self.iit_analyzer = IITAnalyzer(self)
        self.self_wirer = SelfWirer(self)
        self.memory: list[dict[str, Any]] = []
        self.knowledge_graph = self.iit_analyzer.get_initial_graph()
        self.bus: asyncio.Queue[Any] | None = None
        self._background_tasks: list[asyncio.Task[Any]] = []
        self._shutdown_event = asyncio.Event()

    async def start_background_tasks(self) -> None:
        self.bus = asyncio.Queue()
        self._background_tasks.append(
            asyncio.create_task(self.iit_analyzer.run_analysis_loop(self.bus))
        )
        self._background_tasks.append(asyncio.create_task(self.self_wirer.run(self.bus)))

    async def shutdown(self) -> None:
        self._shutdown_event.set()
        for task in self._background_tasks:
            task.cancel()
        await asyncio.gather(*self._background_tasks, return_exceptions=True)

    def add_memory(self, role: str, content: str) -> None:
        self.memory.append({"ts": time.time(), "role": role, "content": content})
        self.memory = self.memory[-5000:]

    def add_graph_edge(self, source: str, target: str, relation: str = "related_to") -> None:
        self.knowledge_graph.add_node(source)
        self.knowledge_graph.add_node(target)
        self.knowledge_graph.add_edge(source, target, relation=relation)

    def get_state_summary(self) -> dict[str, Any]:
        phi = self.iit_analyzer.get_latest_metrics()
        return {
            "uptime_s": int(time.time() - self.start_time),
            "principles": self.alignment_core.list(),
            "memory_size": len(self.memory),
            "self_awareness_metrics": phi,
            "self_wiring": self.self_wirer.summary(),
            "graph": {
                "nodes": self.knowledge_graph.number_of_nodes(),
                "edges": self.knowledge_graph.number_of_edges(),
            },
        }
