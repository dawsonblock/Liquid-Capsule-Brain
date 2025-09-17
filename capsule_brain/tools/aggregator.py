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

Numeric = int | float | complex
SAFE_LITERAL_TYPES = (int, float, complex)
BinaryOp = Callable[[Numeric, Numeric], Numeric]
UnaryOp = Callable[[Numeric], Numeric]

BINARY_OPS: dict[type[ast.operator], BinaryOp] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
}
UNARY_OPS: dict[type[ast.unaryop], UnaryOp] = {ast.USub: lambda value: -value}


def _safe_eval(expr: str) -> Numeric:
    def eval_(node: ast.AST) -> Numeric:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, SAFE_LITERAL_TYPES):
                return node.value
            raise ValueError("Unsafe expression")
        if isinstance(node, ast.Num):  # pragma: no cover - compatibility with older ASTs
            if isinstance(node.n, SAFE_LITERAL_TYPES):
                return node.n
            raise ValueError("Unsafe expression")
        if isinstance(node, ast.BinOp):
            binary_op = BINARY_OPS.get(type(node.op))
            if binary_op is None:
                raise ValueError("Unsafe expression")
            return binary_op(eval_(node.left), eval_(node.right))
        if isinstance(node, ast.UnaryOp):
            unary_op = UNARY_OPS.get(type(node.op))
            if unary_op is None:
                raise ValueError("Unsafe expression")
            return unary_op(eval_(node.operand))
        raise ValueError("Unsafe expression")

    return eval_(ast.parse(expr, mode="eval").body)


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
            except Exception as exc:  # pragma: no cover - defensive logging path
                log.error("Tool failure: %s", exc)
                results.append({"error": str(exc), "tool": hint.get("tool", "unknown")})

        elapsed_ms = (time.perf_counter() - start) * 1000
        return {"results": results}, elapsed_ms

    async def _execute_tool(self, hint: dict[str, Any]) -> dict[str, Any]:
        name = hint.get("tool", "unknown")
        await asyncio.sleep(0.05)

        if name == "local_search":
            query = hint.get("query", "")
            results = (await retrieve_topk(query)).get("abstracts", [])
            return {"tool": "local_search", "query": query, "results": results}

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
