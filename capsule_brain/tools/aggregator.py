"""Aggregate tool hints and execute simple built-in tools."""

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

logger = logging.getLogger(__name__)

_BINARY_OPS: dict[type[ast.AST], Callable[[float, float], float]] = {
    ast.Add: lambda left, right: float(op.add(left, right)),
    ast.Sub: lambda left, right: float(op.sub(left, right)),
    ast.Mult: lambda left, right: float(op.mul(left, right)),
    ast.Div: lambda left, right: float(op.truediv(left, right)),
    ast.Pow: lambda left, right: float(op.pow(left, right)),
}
_UNARY_OPS: dict[type[ast.AST], Callable[[float], float]] = {
    ast.USub: lambda value: -float(value),
}


def _safe_eval(expr: str) -> float:
    """Evaluate a mathematical expression using a restricted AST."""

    def eval_(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int | float)):
            return float(node.value)
        if isinstance(node, ast.BinOp):
            binary_operator = _BINARY_OPS[type(node.op)]
            return binary_operator(eval_(node.left), eval_(node.right))
        if isinstance(node, ast.UnaryOp):
            unary_operator = _UNARY_OPS[type(node.op)]
            return unary_operator(eval_(node.operand))
        raise ValueError("Unsafe expression")

    return eval_(ast.parse(expr, mode="eval").body)


class ToolAggregator:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}
        self.results_cache: dict[str, Any] = {}

    async def maybe_batch(
        self, tool_hints: list[dict[str, Any]]
    ) -> tuple[dict[str, Any], float]:
        start = time.perf_counter()
        if not tool_hints:
            return {"results": []}, 0.0

        results: list[dict[str, Any]] = []
        for hint in tool_hints[:5]:
            try:
                clean = validate_tool_params(hint)
                results.append(await self._execute_tool(clean))
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Tool failure")
                results.append({"error": str(exc), "tool": hint.get("tool", "unknown")})
        return {"results": results}, (time.perf_counter() - start) * 1000

    async def _execute_tool(self, hint: dict[str, Any]) -> dict[str, Any]:
        name = hint.get("tool", "unknown")
        await asyncio.sleep(0.05)
        if name == "local_search":
            query = hint.get("query", "")
            retrieval = await retrieve_topk(query)
            return {
                "tool": "local_search",
                "query": query,
                "results": retrieval.get("abstracts", []),
            }
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
