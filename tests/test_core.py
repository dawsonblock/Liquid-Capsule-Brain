"""Core engine smoke tests."""

from __future__ import annotations

import asyncio

from capsule_brain.core.capsule_engine import CapsuleEngine


def test_engine_background_tasks() -> None:
    async def runner() -> None:
        engine = CapsuleEngine()
        await engine.start_background_tasks()
        await asyncio.sleep(0.1)

        summary = engine.get_state_summary()
        assert "self_awareness_metrics" in summary

        await engine.shutdown()

    asyncio.run(runner())


def test_add_memory_and_edge() -> None:
    engine = CapsuleEngine()
    engine.add_memory("user", "hello")
    assert engine.memory[-1]["content"] == "hello"

    engine.add_graph_edge("X", "Y")
    graph = engine.get_state_summary()["graph"]
    assert graph["nodes"] >= 2
    assert graph["edges"] >= 1
