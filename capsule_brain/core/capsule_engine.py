import asyncio
import logging
import time
from collections.abc import Coroutine
from typing import Any

from fastapi import FastAPI

from capsule_brain.gui.gui import AdvancedGUI

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
        self._background_tasks: set[asyncio.Task[Any]] = set()
        self.gui: AdvancedGUI | None = None
        self._gui_task: asyncio.Task[Any] | None = None
        self._shutdown_event = asyncio.Event()

    def register_background_task(
        self, task_or_coro: Coroutine[Any, Any, Any] | asyncio.Task[Any]
    ) -> asyncio.Task[Any]:
        if isinstance(task_or_coro, asyncio.Task):
            task = task_or_coro
        else:
            task = asyncio.create_task(task_or_coro)

        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

    async def start_background_tasks(self, app: FastAPI) -> None:
        if self.bus is not None:
            raise RuntimeError("Engine background tasks are already running")

        self._shutdown_event.clear()
        self.bus = asyncio.Queue()
        self.register_background_task(self.iit_analyzer.run_analysis_loop(self.bus))
        self.register_background_task(self.self_wirer.run(self.bus))
        self.gui = AdvancedGUI(self, app)
        self._gui_task = self.register_background_task(self.gui.run_broadcasters())

    async def shutdown(self) -> None:
        if not self._background_tasks:
            self.bus = None
            self.gui = None
            self._gui_task = None
            self._shutdown_event = asyncio.Event()
            return

        self._shutdown_event.set()
        tasks = list(self._background_tasks)
        for task in tasks:
            task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self._background_tasks.clear()
        self._gui_task = None
        self.gui = None
        self.bus = None
        self._shutdown_event = asyncio.Event()

    @property
    def is_shutting_down(self) -> bool:
        return self._shutdown_event.is_set()

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
