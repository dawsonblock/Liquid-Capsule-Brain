import asyncio
import logging
from typing import Any, cast

import httpx
import yaml

log = logging.getLogger(__name__)


class AIOverseer:
    def __init__(self, config_path: str, student_api_host: str = "http://localhost:8000") -> None:
        self.student_api_host = student_api_host
        with open(config_path, encoding="utf-8") as config_file:
            config: dict[str, Any] = yaml.safe_load(config_file)
            self.config = config["ai_overseer_config"]
        self.http_client = httpx.AsyncClient(timeout=180.0)

    async def assess_student_state(self) -> dict[str, Any]:
        response = await self.http_client.get(f"{self.student_api_host}/state/summary")
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    async def plan_next_action(self, student_state: dict[str, Any]) -> dict[str, Any]:
        phi = float(student_state.get("self_awareness_metrics", {}).get("phi", 0.0))
        if phi < 1.0:
            return {
                "action": "reasoning_probe",
                "question": "How does entropy in thermodynamics relate to technical debt in software systems?",
            }
        return {
            "action": "graph_synthesis",
            "source": "attention",
            "relation": "related_to",
            "target": "knowledge_integration",
        }

    async def execute_action(self, plan: dict[str, Any]) -> None:
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
            params = {key: plan[key] for key in ("source", "target") if key in plan}
            if "relation" in plan:
                params["relation"] = plan["relation"]
            await self.http_client.post(
                f"{self.student_api_host}/graph/edge",
                params=params,
            )

    async def run_supervisory_loop(self, num_cycles: int = 5) -> None:
        for _ in range(num_cycles):
            try:
                student_state = await self.assess_student_state()
                plan = await self.plan_next_action(student_state)
                await self.execute_action(plan)
                await asyncio.sleep(5)
            except Exception as exc:  # pragma: no cover - defensive logging
                log.error("Overseer cycle error: %s", exc)
                await asyncio.sleep(5)
