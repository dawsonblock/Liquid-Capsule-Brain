"""Teacher-side orchestration for supervising Capsule Brain."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, cast

import httpx
import yaml


log = logging.getLogger(__name__)


class AIOverseer:
    def __init__(self, config_path: str, student_api_host: str = "http://localhost:8000") -> None:
        self.student_api_host = student_api_host.rstrip("/")
        config_file = Path(config_path)
        config_data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
        self.config: Dict[str, Any] = config_data["ai_overseer_config"]
        self.http_client = httpx.AsyncClient(timeout=180.0)

    async def assess_student_state(self) -> Dict[str, Any]:
        response = await self.http_client.get(f"{self.student_api_host}/state/summary")
        response.raise_for_status()
        return cast(Dict[str, Any], response.json())

    async def plan_next_action(self, student_state: Dict[str, Any]) -> Dict[str, Any]:
        phi = float(student_state.get("self_awareness_metrics", {}).get("phi", 0.0))
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

    async def execute_action(self, plan: Dict[str, Any]) -> None:
        action = plan.get("action")
        if action == "reasoning_probe":
            await self.http_client.post(
                f"{self.student_api_host}/ask",
                json={"q": plan["question"]},
            )
        elif action == "knowledge_injection":
            prompt = f"Research '{plan['topic']}' using your tools and summarize the key findings."
            await self.http_client.post(
                f"{self.student_api_host}/ask",
                json={"q": prompt},
            )
        elif action == "graph_synthesis":
            await self.http_client.post(
                f"{self.student_api_host}/graph/edge",
                params=plan,
            )

    async def run_supervisory_loop(self, num_cycles: int = 5) -> None:
        for _ in range(num_cycles):
            try:
                state = await self.assess_student_state()
                plan = await self.plan_next_action(state)
                await self.execute_action(plan)
                await asyncio.sleep(5)
            except Exception as exc:  # pragma: no cover - defensive logging
                log.error("Overseer cycle error: %s", exc)
                await asyncio.sleep(5)
