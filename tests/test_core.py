import asyncio

import pytest

from capsule_brain.core.capsule_engine import CapsuleEngine


@pytest.mark.asyncio
async def test_engine_background_tasks() -> None:
    engine = CapsuleEngine()
    await engine.start_background_tasks()
    await asyncio.sleep(0.1)
    summary = engine.get_state_summary()
    assert "self_awareness_metrics" in summary
    await engine.shutdown()


def test_add_memory_and_edge() -> None:
    engine = CapsuleEngine()
    engine.add_memory("user", "hello")
    assert engine.memory[-1]["content"] == "hello"
    engine.add_graph_edge("X", "Y")
    graph = engine.get_state_summary()["graph"]
    assert graph["nodes"] >= 2 and graph["edges"] >= 1
