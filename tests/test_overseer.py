from typing import Any, cast

import httpx
import pytest

from capsule_brain.api import server
from capsule_brain.core.capsule_engine import CapsuleEngine
from teacher.ai_overseer import AIOverseer


@pytest.mark.asyncio
async def test_overseer_can_add_graph_edge() -> None:
    overseer = AIOverseer("teacher/overseer_config.yaml", student_api_host="http://test")
    await overseer.http_client.aclose()

    transport = httpx.ASGITransport(app=cast(Any, server.app))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        overseer.http_client = client

        previous_engine = server.engine
        engine = CapsuleEngine()
        await engine.start_background_tasks()
        server.engine = engine

        try:
            student_state = await overseer.assess_student_state()
            student_state.setdefault("self_awareness_metrics", {})["phi"] = 1.5

            plan = await overseer.plan_next_action(student_state)
            assert plan["action"] == "graph_synthesis"
            assert {"source", "target"}.issubset(plan)
            assert plan.get("relation") == "related_to"

            await overseer.execute_action(plan)

            assert server.engine is not None
            graph = server.engine.knowledge_graph
            assert graph.has_edge(plan["source"], plan["target"])
            edge_data = graph.get_edge_data(plan["source"], plan["target"])
            assert edge_data.get("relation") == plan["relation"]
        finally:
            await engine.shutdown()
            server.engine = previous_engine
