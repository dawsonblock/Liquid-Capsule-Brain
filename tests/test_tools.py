import pytest

from capsule_brain.tools.aggregator import ToolAggregator


@pytest.mark.asyncio
async def test_calculator_tool_simple_expression():
    aggregator = ToolAggregator()
    result = await aggregator._execute_tool({"tool": "calculator", "expression": "2 + 3 * 4"})
    assert result["result"] == 14


@pytest.mark.asyncio
async def test_maybe_batch_returns_calculator_result():
    aggregator = ToolAggregator()
    payload, elapsed_ms = await aggregator.maybe_batch([
        {"tool": "calculator", "expression": "6 / 2"}
    ])
    assert elapsed_ms >= 0
    assert payload["results"][0]["result"] == 3.0
