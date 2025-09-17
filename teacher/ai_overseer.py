"""Supervisory loop for coordinating the student agent."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, cast

import httpx
import yaml

logger = logging.getLogger(__name__)

_REASONING_PROMPT = (
    "How does entropy in thermodynamics relate to technical debt in software systems?"
)


class AIOverseer:
    """Coordinate high level interventions for the student agent."""

    def __init__(self, config_path: str, student_api_host: str = "http://localhost:8000") -> None:
        self.student_api_host = student_api_host.rstrip("/")
        self.config = self._load_config(config_path)
        self.http_client = httpx.AsyncClient(timeout=180.0)

    @staticmethod
    def _load_config(config_path: str) -> dict[str, Any]:
        raw_data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        if not isinstance(raw_data, dict):
            return {}
        section = raw_data.get("ai_overseer_config", {})
        if isinstance(section, dict):
            return cast(dict[str, Any], section)
        return {}

    async def assess_student_state(self) -> dict[str, Any]:
        response = await self.http_client.get(f"{self.student_api_host}/state/summary")
        response.raise_for_status()
        payload = cast(dict[str, Any], response.json())
        return payload

    async def plan_next_action(self, student_state: dict[str, Any]) -> dict[str, Any]:
        phi = float(student_state.get("self_awareness_metrics", {}).get("phi", 0.0))
        if phi < 1.0:
            return {"action": "reasoning_probe", "question": _REASONING_PROMPT}
        return {
            "action": "graph_synthesis",
            "source_node": "attention",
            "relation": "related_to",
            "target_node": "knowledge_integration",
        }

    async def execute_action(self, plan: dict[str, Any]) -> None:
        action = plan.get("action")
        if action == "reasoning_probe":
            await self.http_client.post(
                f"{self.student_api_host}/ask", json={"q": plan["question"]}
            )
        elif action == "knowledge_injection":
            prompt = f"Research '{plan['topic']}' using your tools and summarize the key findings."
            await self.http_client.post(f"{self.student_api_host}/ask", json={"q": prompt})
        elif action == "graph_synthesis":
            await self.http_client.post(f"{self.student_api_host}/graph/edge", params=plan)
        else:
            logger.warning("Unknown plan action encountered: %s", action)

    async def run_supervisory_loop(self, num_cycles: int = 5) -> None:
        for _ in range(num_cycles):
            try:
                student_state = await self.assess_student_state()
                plan = await self.plan_next_action(student_state)
                await self.execute_action(plan)
                await asyncio.sleep(5)
            except Exception:  # pragma: no cover - defensive logging
                logger.exception("Overseer cycle error")
                await asyncio.sleep(5)

    async def aclose(self) -> None:
        """Release the underlying HTTP resources."""

        await self.http_client.aclose()
