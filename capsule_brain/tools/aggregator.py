from __future__ import annotations

import ast
import asyncio
import logging
import time
from typing import Any, TypeAlias, cast

from ..retrieval.index import retrieve_topk
from ..security.input_sanitizer import validate_tool_params

log = logging.getLogger(__name__)

Number: TypeAlias = float | int


def _safe_eval(expr: str) -> Number:
    """Safely evaluate a mathematical expression containing numeric literals."""

    def eval_(node: ast.AST) -> Number:
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ValueError("Unsafe expression")
            return cast(Number, value)
        if isinstance(node, ast.Num):  # pragma: no cover - for Python <3.8 compatibility
            value = node.n
            if isinstance(value, bool):
                raise ValueError("Unsafe expression")
            return cast(Number, value)
        if isinstance(node, ast.BinOp):
            left_value = eval_(node.left)
            right_value = eval_(node.right)
            op_node = node.op
            if isinstance(op_node, ast.Add):
                return cast(Number, left_value + right_value)
            if isinstance(op_node, ast.Sub):
                return cast(Number, left_value - right_value)
            if isinstance(op_node, ast.Mult):
                return cast(Number, left_value * right_value)
            if isinstance(op_node, ast.Div):
                return cast(Number, left_value / right_value)
            if isinstance(op_node, ast.Pow):
                return cast(Number, left_value**right_value)
            raise ValueError("Unsafe expression")
        if isinstance(node, ast.UnaryOp):
            operand = eval_(node.operand)
            if isinstance(node.op, ast.USub):
                return cast(Number, -operand)
            raise ValueError("Unsafe expression")
        raise ValueError("Unsafe expression")

    parsed = ast.parse(expr, mode="eval").body
    return eval_(parsed)


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
                clean_hint = validate_tool_params(hint)
                results.append(await self._execute_tool(clean_hint))
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
