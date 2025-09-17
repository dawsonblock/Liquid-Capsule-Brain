from __future__ import annotations

import ast
import asyncio
import logging
import operator as op
import time
from typing import Any, Callable, Dict, Iterable, List, Tuple

from ..retrieval.index import retrieve_topk
from ..security.input_sanitizer import validate_tool_params


log = logging.getLogger(__name__)

BinaryOp = Callable[[float, float], float]
UnaryOp = Callable[[float], float]

ALLOWED_BINARY_OPS: dict[type[ast.AST], BinaryOp] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
}

ALLOWED_UNARY_OPS: dict[type[ast.AST], UnaryOp] = {
    ast.USub: lambda value: -value,
}


def _safe_eval(expr: str) -> float:
    """Evaluate a simple arithmetic expression safely."""

    node = ast.parse(expr, mode="eval").body

    def eval_(ast_node: ast.AST) -> float:
        if isinstance(ast_node, ast.Num):  # type: ignore[attr-defined]
            literal = ast_node.n
            if not isinstance(literal, (int, float)):
                raise ValueError("Unsupported literal")
            return float(literal)
        if isinstance(ast_node, ast.BinOp):
            binary_op = ALLOWED_BINARY_OPS.get(type(ast_node.op))
            if binary_op is None:
                raise ValueError("Unsupported operator")
            return binary_op(eval_(ast_node.left), eval_(ast_node.right))
        if isinstance(ast_node, ast.UnaryOp):
            unary_op = ALLOWED_UNARY_OPS.get(type(ast_node.op))
            if unary_op is None:
                raise ValueError("Unsupported unary operator")
            return unary_op(eval_(ast_node.operand))
        raise ValueError("Unsafe expression")

    return eval_(node)


class ToolAggregator:
    """Coordinate multiple tool invocations with minimal batching."""

    def __init__(self) -> None:
        self.results_cache: dict[str, Dict[str, Any]] = {}

    async def maybe_batch(
        self, tool_hints: Iterable[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], float]:
        start = time.perf_counter()
        hints = list(tool_hints)
        if not hints:
            return {"results": []}, 0.0

        results: List[Dict[str, Any]] = []
        for hint in hints[:5]:
            try:
                clean = validate_tool_params(hint)
                results.append(await self._execute_tool(clean))
            except Exception as exc:  # pragma: no cover - defensive logging
                log.error("Tool failure: %s", exc)
                results.append({"error": str(exc), "tool": hint.get("tool", "unknown")})

        elapsed_ms = (time.perf_counter() - start) * 1000
        return {"results": results}, elapsed_ms

    async def _execute_tool(self, hint: Dict[str, Any]) -> Dict[str, Any]:
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
