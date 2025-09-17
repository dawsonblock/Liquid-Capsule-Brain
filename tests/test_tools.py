import asyncio

from capsule_brain.tools.aggregator import ToolAggregator


def test_calculator_tool_simple_expression() -> None:
    aggregator = ToolAggregator()
    result = asyncio.run(
        aggregator._execute_tool({"tool": "calculator", "expression": "2 + 3 * 4"})
    )
    assert result["result"] == 14


def test_maybe_batch_returns_calculator_result() -> None:
    aggregator = ToolAggregator()
    payload, elapsed_ms = asyncio.run(
        aggregator.maybe_batch([
            {"tool": "calculator", "expression": "6 / 2"}
        ])
    )
    assert elapsed_ms >= 0
    assert payload["results"][0]["result"] == 3.0
