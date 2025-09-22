"""Minimal supervisory loop for integration tests and demos."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx
import yaml  # type: ignore[import-untyped]

log = logging.getLogger(__name__)


class AIOverseer:
    """Coordinate simple oversight flows against the Capsule Brain API."""

    def __init__(
        self,
        config_path: str | Path,
        student_api_host: str = "http://localhost:8000",
        *,
        http_timeout: float = 180.0,
    ) -> None:
        self.student_api_host = student_api_host.rstrip("/")
        self.config = self._load_config(config_path)
        self.http_client = httpx.AsyncClient(timeout=http_timeout)

        # Conversation memory to prevent repetitive questions
        self.asked_questions: list[tuple[str, float]] = []  # (question, timestamp)
        self.question_rotation_index = 0

        # Diverse question bank for reasoning probes
        self.reasoning_questions = [
            "How does entropy in thermodynamics relate to technical debt in software systems?",
            "What are the parallels between biological evolution and machine learning optimization?",
            "How can principles from quantum mechanics inform distributed systems design?",
            "What insights from cognitive psychology can improve AI system architecture?",
            "How do economic principles of supply and demand apply to computational resource allocation?",
            "What can we learn from ecological systems for building resilient software architectures?",
            "How do principles from game theory apply to cybersecurity and adversarial AI?",
            "What parallels exist between musical composition and algorithmic design?",
            "How can principles from linguistics improve natural language processing systems?",
            "What insights from physics can enhance our understanding of information theory?",
            "How do principles from neuroscience inform artificial neural network design?",
            "What can we learn from swarm intelligence for distributed AI systems?",
            "How do principles from chaos theory apply to system resilience and fault tolerance?",
            "What insights from sociology can improve human-AI interaction design?",
            "How can principles from thermodynamics optimize energy consumption in computing?",
            "What parallels exist between immune systems and cybersecurity defense mechanisms?",
            "How do principles from fluid dynamics apply to data flow optimization?",
            "What can we learn from ant colony optimization for distributed algorithms?",
            "How do principles from molecular biology inform self-organizing systems?",
            "What insights from astronomy can improve large-scale data processing systems?",
            "How can principles from geology inform data persistence and storage strategies?",
            "What parallels exist between weather prediction and machine learning forecasting?",
            "How do principles from chemistry inform chemical reaction-inspired algorithms?",
            "What can we learn from DNA replication for data replication strategies?",
            "How do principles from optics inform information transmission and processing?",
            "What insights from materials science can improve hardware-software co-design?",
            "How can principles from genetics inform evolutionary algorithms and optimization?",
            "What parallels exist between ecosystem dynamics and distributed system behavior?",
            "How do principles from acoustics apply to signal processing and communication?",
            "What can we learn from plant growth patterns for adaptive system design?"
        ]

    @staticmethod
    def _load_config(config_path: str | Path) -> Mapping[str, Any]:
        config_file = Path(config_path)
        with config_file.open(encoding="utf-8") as handle:
            raw_config = yaml.safe_load(handle)

        if not isinstance(raw_config, Mapping):
            raise ValueError("AI overseer configuration must be a mapping")

        section = raw_config.get("ai_overseer_config")
        if not isinstance(section, Mapping):
            raise ValueError("'ai_overseer_config' section missing or invalid")

        return section

    def _select_next_question(self, recent_memories: list[dict], current_time: float) -> str | None:
        """Select a question that hasn't been asked recently."""
        # Check recent memories for questions asked in the last 10 minutes
        recent_questions = set()
        for memory in recent_memories[-10:]:  # Check last 10 memories
            if memory.get("role") == "user":
                content = memory.get("content", "")
                # Check if this looks like a reasoning probe question
                for question in self.reasoning_questions:
                    if question.lower() in content.lower():
                        recent_questions.add(question)

        # Also check our internal question history (last 5 minutes)
        for question, timestamp in self.asked_questions:
            if current_time - timestamp < 300:  # 5 minutes
                recent_questions.add(question)

        # Find a question that hasn't been asked recently
        for i in range(len(self.reasoning_questions)):
            question = self.reasoning_questions[self.question_rotation_index]
            self.question_rotation_index = (self.question_rotation_index + 1) % len(self.reasoning_questions)

            if question not in recent_questions:
                return question

        # All questions have been asked recently
        return None

    async def assess_student_state(self) -> dict[str, Any]:
        response = await self.http_client.get(f"{self.student_api_host}/state/summary")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Student state response must be a JSON object")
        return payload

    async def plan_next_action(self, student_state: Mapping[str, Any]) -> dict[str, Any]:
        metrics = student_state.get("self_awareness_metrics")
        phi = 0.0
        if isinstance(metrics, Mapping):
            phi_value = metrics.get("phi", 0.0)
            try:
                phi = float(phi_value)
            except (TypeError, ValueError):  # pragma: no cover - defensive fallback
                log.debug("Unable to interpret phi value: %s", phi_value)

        # Check recent memories to avoid repetitive questions
        recent_memories = student_state.get("recent_memories", [])
        current_time = time.time()

        # Clean up old question history (older than 1 hour)
        self.asked_questions = [
            (q, t) for q, t in self.asked_questions
            if current_time - t < 3600
        ]

        if phi < 1.0:
            # Select a question that hasn't been asked recently
            question = self._select_next_question(recent_memories, current_time)
            if question:
                # Record this question as asked
                self.asked_questions.append((question, current_time))
                return {
                    "action": "reasoning_probe",
                    "question": question,
                }
            else:
                # If all questions have been asked recently, wait
                log.info("All reasoning questions asked recently, skipping probe")
                return {
                    "action": "wait",
                    "reason": "recent_questions_exhausted"
                }

        return {
            "action": "graph_synthesis",
            "source_node": "attention",
            "relation": "related_to",
            "target_node": "knowledge_integration",
        }

    async def execute_action(self, plan: Mapping[str, Any]) -> None:
        action = plan.get("action")

        if action == "reasoning_probe":
            question = plan.get("question")
            if isinstance(question, str):
                log.info(f"Overseer asking reasoning probe: {question[:50]}...")
                await self.http_client.post(
                    f"{self.student_api_host}/ask",
                    json={"q": question},
                )
            return

        if action == "wait":
            reason = plan.get("reason", "unknown")
            log.info(f"Overseer waiting: {reason}")
            return

        if action == "knowledge_injection":
            topic = plan.get("topic")
            if isinstance(topic, str):
                prompt = f"Research '{topic}' using your tools and summarize the key findings."
                await self.http_client.post(
                    f"{self.student_api_host}/ask",
                    json={"q": prompt},
                )
            return

        if action == "graph_synthesis":
            await self.http_client.post(
                f"{self.student_api_host}/graph/edge",
                params=plan,
            )

    async def run_supervisory_loop(self, num_cycles: int = 5, *, delay_seconds: float = 5.0) -> None:
        for _ in range(num_cycles):
            try:
                student_state = await self.assess_student_state()
                plan = await self.plan_next_action(student_state)
                await self.execute_action(plan)
            except Exception as exc:  # pragma: no cover - defensive logging
                log.error("Overseer cycle error: %s", exc)
            finally:
                await asyncio.sleep(delay_seconds)
