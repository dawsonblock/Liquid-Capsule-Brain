import httpx
import pytest

from capsule_brain.api.server import app
from teacher.ai_overseer import AIOverseer


@pytest.mark.asyncio
async def test_overseer_graph_synthesis_creates_edge() -> None:
    overseer = AIOverseer("teacher/overseer_config.yaml", student_api_host="http://testserver")
    await overseer.http_client.aclose()

    edges_after = None
    await app.router.startup()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            overseer.http_client = client
            before = await client.get("/state/summary")
            edges_before = before.json()["graph"]["edges"]

            plan = {
                "action": "graph_synthesis",
                "source_node": "planner",
                "target_node": "retrieval",
                "relation": "related_to",
            }
            await overseer.execute_action(plan)

            after = await client.get("/state/summary")
            edges_after = after.json()["graph"]["edges"]
    finally:
        await app.router.shutdown()

    assert edges_after is not None
    assert edges_after >= edges_before + 1
