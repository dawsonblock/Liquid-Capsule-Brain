"""Tool aggregation utilities used by the planner."""
from __future__ import annotations

import ast
import asyncio
import logging
import operator as op
import time
from collections.abc import Callable
from typing import Any

from ..retrieval.index import retrieve_topk
from ..security.input_sanitizer import validate_tool_params

log = logging.getLogger(__name__)

BinaryOp = Callable[[float, float], float]
UnaryOp = Callable[[float], float]

BINARY_OPS: dict[type[ast.operator], BinaryOp] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
}
UNARY_OPS: dict[type[ast.unaryop], UnaryOp] = {ast.USub: lambda value: -value}


def _safe_eval(expr: str) -> float:
    def eval_(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
            return float(node.value)
        if isinstance(node, ast.BinOp):
            op_func = BINARY_OPS[type(node.op)]
            return op_func(eval_(node.left), eval_(node.right))
        if isinstance(node, ast.UnaryOp):
            unary_func = UNARY_OPS[type(node.op)]
            return unary_func(eval_(node.operand))
        raise ValueError("Unsafe expression")

    parsed = ast.parse(expr, mode="eval")
    return eval_(parsed.body)  # type: ignore[arg-type]


class ToolAggregator:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}
        self.results_cache: dict[str, Any] = {}

    async def maybe_batch(self, tool_hints: list[dict[str, Any]]) -> tuple[dict[str, Any], float]:
        start = time.perf_counter()
        if not tool_hints:
            return {"results": []}, 0.0

        results: list[dict[str, Any]] = []
        for hint in tool_hints[:5]:
            try:
                clean = validate_tool_params(hint)
                results.append(await self._execute_tool(clean))
            except Exception as exc:  # pragma: no cover - defensive logging
                log.error("Tool failure: %s", exc)
                results.append({"error": str(exc), "tool": hint.get("tool", "unknown")})
        latency_ms = (time.perf_counter() - start) * 1000
        return {"results": results}, latency_ms

    async def _execute_tool(self, hint: dict[str, Any]) -> dict[str, Any]:
        name = hint.get("tool", "unknown")
        await asyncio.sleep(0.05)
        if name == "local_search":
            query = hint.get("query", "")
            retrieval = await retrieve_topk(query)
            return {"tool": "local_search", "query": query, "results": retrieval.get("abstracts", [])}
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
