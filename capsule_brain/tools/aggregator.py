"""Utility aggregator that fans out tool requests and consolidates results."""

from __future__ import annotations

import ast
import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from ..retrieval.index import retrieve_topk
from ..security.input_sanitizer import validate_tool_params

log = logging.getLogger(__name__)

BinaryOperator = Callable[[float, float], float]
UnaryOperator = Callable[[float], float]

BINARY_OPERATORS: dict[type[ast.AST], BinaryOperator] = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a**b,
}

UNARY_OPERATORS: dict[type[ast.AST], UnaryOperator] = {
    ast.USub: lambda value: -value,
}


def _safe_eval(expr: str) -> float:
    """Evaluate a simple arithmetic expression safely."""

    def eval_node(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
            return float(node.value)
        if isinstance(node, ast.BinOp):
            binary_op = BINARY_OPERATORS[type(node.op)]
            left = eval_node(node.left)
            right = eval_node(node.right)
            return binary_op(left, right)
        if isinstance(node, ast.UnaryOp):
            unary_op = UNARY_OPERATORS[type(node.op)]
            return unary_op(eval_node(node.operand))
        msg = f"Unsafe expression: {expr!r}"
        raise ValueError(msg)

    parsed = ast.parse(expr, mode="eval")
    return eval_node(parsed.body)


class ToolAggregator:
    """Coordinate tool execution with basic batching and caching."""

    def __init__(self) -> None:
        self.results_cache: dict[str, Any] = {}

    async def maybe_batch(self, tool_hints: list[dict[str, Any]]) -> tuple[dict[str, Any], float]:
        start = time.perf_counter()
        if not tool_hints:
            return {"results": []}, 0.0

        results = []
        for hint in tool_hints[:5]:
            try:
                clean_hint = validate_tool_params(hint)
                results.append(await self._execute_tool(clean_hint))
            except Exception as exc:  # pragma: no cover - defensive logging
                log.exception("Tool failure: %s", exc)
                results.append({"error": str(exc), "tool": hint.get("tool", "unknown")})

        latency_ms = (time.perf_counter() - start) * 1000
        return {"results": results}, latency_ms

    async def _execute_tool(self, hint: dict[str, Any]) -> dict[str, Any]:
        name = hint.get("tool", "unknown")
        await asyncio.sleep(0.05)

        if name == "local_search":
            query = hint.get("query", "")
            abstracts = (await retrieve_topk(query)).get("abstracts", [])
            return {"tool": "local_search", "query": query, "results": abstracts}

        if name == "calculator":
            expression = hint.get("expression", "0")
            return {
                "tool": "calculator",
                "expression": expression,
                "result": _safe_eval(expression),
            }

        return {"tool": name, "status": "completed", "data": "Mock tool execution result"}

    async def health_check(self) -> bool:
        return True
