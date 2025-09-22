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
        self.overseer_enabled = False
        self.overseer: Any = None

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
        if self._background_tasks:
            raise RuntimeError("Engine background tasks are already running")

        self._shutdown_event.clear()
        self.bus = asyncio.Queue()
        self.register_background_task(self.iit_analyzer.run_analysis_loop(self.bus))
        self.register_background_task(self.self_wirer.run(self.bus))
        self.gui = AdvancedGUI(self, app)
        self._gui_task = self.register_background_task(self.gui.run_broadcasters())

        # Start overseer if enabled
        if self.overseer_enabled:
            await self.start_overseer()

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

        # Broadcast memory update to GUI
        if self.bus:
            asyncio.create_task(
                self.bus.put(
                    {
                        "type": "memory_update",
                        "payload": {"role": role, "content": content, "timestamp": time.time()},
                    }
                )
            )

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
            "overseer_enabled": self.overseer_enabled,
            "graph": {
                "nodes": self.knowledge_graph.number_of_nodes(),
                "edges": self.knowledge_graph.number_of_edges(),
            },
            "belief_state": {
                "current_query": self.belief_state_manager.current_query,
                "retrieved_knowledge": (self.belief_state_manager.retrieved_knowledge),
                "current_plan": self.belief_state_manager.current_plan,
                "last_update": self.belief_state_manager.last_update,
            },
            "recent_memories": self.memory[-10:],  # Last 10 memories
            "thinking_process": self._get_thinking_process(),
        }

    def _get_thinking_process(self) -> dict[str, Any]:
        """Get current thinking process information."""
        return {
            "current_phi": self.iit_analyzer.current_phi,
            "neural_glyphs": self.iit_analyzer.current_glyphs,
            "graph_activity": {
                "recent_additions": len(
                    [m for m in self.memory if m.get("type") == "graph_edge"][-5:]
                ),
                "active_nodes": list(self.knowledge_graph.nodes())[-10:],
            },
            "self_wiring_proposals": self.self_wirer.performance_history[-5:],
            "last_analysis": self.iit_analyzer.last_analysis,
        }

    async def start_overseer(self) -> None:
        """Start the AI overseer if not already running."""
        if self.overseer is not None:
            return

        try:
            from pathlib import Path

            from teacher.ai_overseer import AIOverseer

            config_path = Path("teacher/overseer_config.yaml")
            if config_path.exists():
                self.overseer = AIOverseer(config_path=config_path)
                # Start overseer as background task
                self.register_background_task(self._run_overseer_loop())
                log.info("AI Overseer started")
            else:
                log.warning("Overseer config not found, skipping overseer startup")
        except Exception as exc:
            log.error("Failed to start overseer: %s", exc)

    async def stop_overseer(self) -> None:
        """Stop the AI overseer."""
        self.overseer_enabled = False
        self.overseer = None
        log.info("AI Overseer stopped")

    async def _run_overseer_loop(self) -> None:
        """Run the overseer supervisory loop."""
        if not self.overseer:
            return

        try:
            while not self._shutdown_event.is_set() and self.overseer_enabled:
                try:
                    student_state = await self.overseer.assess_student_state()
                    plan = await self.overseer.plan_next_action(student_state)
                    await self.overseer.execute_action(plan)

                    # Broadcast overseer action to GUI
                    if self.bus:
                        await self.bus.put(
                            {
                                "type": "overseer_action",
                                "payload": {
                                    "action": plan.get("action"),
                                    "description": (self._describe_overseer_action(plan)),
                                },
                            }
                        )

                except Exception as exc:
                    log.error("Overseer cycle error: %s", exc)
                finally:
                    await asyncio.sleep(30)  # Run every 30 seconds
        except asyncio.CancelledError:
            log.debug("Overseer loop cancelled")
        except Exception as exc:
            log.error("Overseer loop error: %s", exc)

    def _describe_overseer_action(self, plan: dict[str, Any]) -> str:
        """Generate a human-readable description of the overseer action."""
        action = plan.get("action", "unknown")

        if action == "reasoning_probe":
            question = plan.get("question", "")
            return f"Reasoning probe: {question[:100]}" f"{'...' if len(question) > 100 else ''}"
        elif action == "knowledge_injection":
            topic = plan.get("topic", "")
            return f"Knowledge injection: {topic}"
        elif action == "graph_synthesis":
            source = plan.get("source_node", "")
            target = plan.get("target_node", "")
            relation = plan.get("relation", "")
            return f"Graph synthesis: {source} {relation} {target}"
        else:
            return f"Overseer action: {action}"

    def enable_overseer(self) -> None:
        """Enable the AI overseer."""
        self.overseer_enabled = True
        log.info("AI Overseer enabled")

    def disable_overseer(self) -> None:
        """Disable the AI overseer."""
        self.overseer_enabled = False
        log.info("AI Overseer disabled")

    def broadcast_belief_state_update(self) -> None:
        """Broadcast current belief state to GUI."""
        if self.bus:
            asyncio.create_task(
                self.bus.put(
                    {
                        "type": "belief_state_update",
                        "payload": {
                            "belief_state": {
                                "current_query": (self.belief_state_manager.current_query),
                                "retrieved_knowledge": (
                                    self.belief_state_manager.retrieved_knowledge
                                ),
                                "current_plan": self.belief_state_manager.current_plan,
                                "last_update": self.belief_state_manager.last_update,
                            },
                            "thinking_process": self._get_thinking_process(),
                            "recent_memories": self.memory[-5:],  # Last 5 memories
                        },
                    }
                )
            )
