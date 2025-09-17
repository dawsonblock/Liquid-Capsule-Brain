import asyncio

from capsule_brain.core.capsule_engine import CapsuleEngine


def test_engine_background_tasks() -> None:
    async def run() -> None:
        engine = CapsuleEngine()
        await engine.start_background_tasks()
        # allow a loop tick
        await asyncio.sleep(0.1)
        s = engine.get_state_summary()
        assert "self_awareness_metrics" in s
        await engine.shutdown()

    asyncio.run(run())

def test_add_memory_and_edge() -> None:
    engine = CapsuleEngine()
    engine.add_memory("user", "hello")
    assert engine.memory[-1]["content"] == "hello"
    engine.add_graph_edge("X", "Y")
    g = engine.get_state_summary()["graph"]
    assert g["nodes"] >= 2 and g["edges"] >= 1
