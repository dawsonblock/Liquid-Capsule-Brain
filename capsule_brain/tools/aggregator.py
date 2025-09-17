"""Aggregate tool execution helpers for Capsule Brain."""

from __future__ import annotations

import ast
import asyncio
import logging
import time
from collections.abc import Callable
from numbers import Real
from typing import Any

from ..retrieval.index import retrieve_topk
from ..security.input_sanitizer import validate_tool_params

log = logging.getLogger(__name__)

BinaryOperator = Callable[[float, float], float]
UnaryOperator = Callable[[float], float]

ALLOWED_BINARY_OPS: dict[type[ast.AST], BinaryOperator] = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
    ast.Pow: lambda left, right: left**right,
}

ALLOWED_UNARY_OPS: dict[type[ast.AST], UnaryOperator] = {
    ast.USub: lambda value: -value,
}


def _safe_eval(expression: str) -> float:
    node = ast.parse(expression, mode="eval").body

    def evaluate(current: ast.AST) -> float:
        if isinstance(current, ast.Constant):
            value = current.value
            if isinstance(value, Real):
                return float(value)
        if isinstance(current, ast.BinOp):
            binary_operator = ALLOWED_BINARY_OPS.get(type(current.op))
            if binary_operator is None:
                msg = f"Unsupported binary operator: {current.op!r}"
                raise ValueError(msg)
            left = evaluate(current.left)
            right = evaluate(current.right)
            return binary_operator(left, right)
        if isinstance(current, ast.UnaryOp):
            unary_operator = ALLOWED_UNARY_OPS.get(type(current.op))
            if unary_operator is None:
                msg = f"Unsupported unary operator: {current.op!r}"
                raise ValueError(msg)
            operand = evaluate(current.operand)
            return unary_operator(operand)
        msg = f"Unsafe expression element: {current!r}"
        raise ValueError(msg)

    return evaluate(node)


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
                cleaned = validate_tool_params(hint)
                results.append(await self._execute_tool(cleaned))
            except Exception as exc:  # pragma: no cover - defensive logging
                log.error("Tool failure: %s", exc)
                results.append({"error": str(exc), "tool": hint.get("tool", "unknown")})

        return {"results": results}, (time.perf_counter() - start) * 1000

    async def _execute_tool(self, hint: dict[str, Any]) -> dict[str, Any]:
        name = hint.get("tool", "unknown")
        await asyncio.sleep(0.05)

        if name == "local_search":
            query = hint.get("query", "")
            search_results = await retrieve_topk(query)
            return {
                "tool": "local_search",
                "query": query,
                "results": search_results.get("abstracts", []),
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
