"""Tool aggregation utilities."""

from __future__ import annotations

import ast
import asyncio
import logging
import time
from typing import Any

from ..retrieval.index import retrieve_topk
from ..security.input_sanitizer import validate_tool_params

logger = logging.getLogger(__name__)


def _safe_eval(expr: str) -> float:
    """Evaluate a basic arithmetic expression safely."""

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
            return float(node.value)
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return float(left + right)
            if isinstance(node.op, ast.Sub):
                return float(left - right)
            if isinstance(node.op, ast.Mult):
                return float(left * right)
            if isinstance(node.op, ast.Div):
                return float(left / right)
            if isinstance(node.op, ast.Pow):
                return float(left**right)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return float(-_eval(node.operand))
        raise ValueError("Unsafe expression")

    parsed = ast.parse(expr, mode="eval")
    return _eval(parsed.body)


class ToolAggregator:
    """Execute tool hints and collect their responses."""

    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}
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
                logger.error("Tool failure: %s", exc)
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
