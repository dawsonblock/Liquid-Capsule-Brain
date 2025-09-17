"""Minimal supervisory loop for integration tests and demos."""

from __future__ import annotations

import asyncio
import logging
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

        if phi < 1.0:
            return {
                "action": "reasoning_probe",
                "question": "How does entropy in thermodynamics relate to technical debt in software systems?",
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
                await self.http_client.post(
                    f"{self.student_api_host}/ask",
                    json={"q": question},
                )
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
