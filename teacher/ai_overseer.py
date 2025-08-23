import asyncio
import json
import logging
from typing import Any, Dict

import httpx
import yaml

log = logging.getLogger(__name__)


class AIOverseer:
    def __init__(self, config_path: str, student_api_host: str = "http://localhost:8000"):
        self.student_api_host = student_api_host
        self.config = yaml.safe_load(open(config_path, "r"))["ai_overseer_config"]
        self.http_client = httpx.AsyncClient(timeout=180.0)

    async def assess_student_state(self) -> Dict[str, Any]:
        r = await self.http_client.get(f"{self.student_api_host}/state/summary")
        r.raise_for_status()
        return r.json()

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

    async def execute_action(self, plan: Dict[str, Any]):
        a = plan.get("action")
        if a == "reasoning_probe":
            await self.http_client.post(
                f"{self.student_api_host}/ask", json={"q": plan["question"]}
            )
        elif a == "knowledge_injection":
            prompt = f"Research '{plan['topic']}' using your tools and summarize the key findings."
            await self.http_client.post(f"{self.student_api_host}/ask", json={"q": prompt})
        elif a == "graph_synthesis":
            await self.http_client.post(f"{self.student_api_host}/graph/edge", params=plan)

    async def run_supervisory_loop(self, num_cycles: int = 5):
        for _ in range(num_cycles):
            try:
                s = await self.assess_student_state()
                plan = await self.plan_next_action(s)
                await self.execute_action(plan)
                await asyncio.sleep(5)
            except Exception as e:
                log.error(f"Overseer cycle error: {e}")
                await asyncio.sleep(5)
