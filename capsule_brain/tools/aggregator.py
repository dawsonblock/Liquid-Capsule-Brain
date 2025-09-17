import ast
import asyncio
import logging
import operator as op
import time
from collections.abc import Callable
from typing import Any, TypeAlias, cast

from ..retrieval.index import retrieve_topk
from ..security.input_sanitizer import validate_tool_params

log = logging.getLogger(__name__)

Number: TypeAlias = float | int
BinaryOperator = Callable[[Number, Number], Number]
UnaryOperator = Callable[[Number], Number]


def _negate(value: Number) -> Number:
    return cast(Number, -value)


ALLOWED_BIN_OPS: dict[type[ast.AST], BinaryOperator] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
}

ALLOWED_UNARY_OPS: dict[type[ast.AST], UnaryOperator] = {ast.USub: _negate}


def _safe_eval(expr: str) -> Number:
    def eval_(node: ast.AST) -> Number:
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ValueError("Unsafe expression")
            return cast(Number, value)
        if isinstance(node, ast.Num):  # pragma: no cover - legacy Python nodes
            value = node.n
            if isinstance(value, bool):
                raise ValueError("Unsafe expression")
            return cast(Number, value)
        if isinstance(node, ast.BinOp):
            bin_operator = ALLOWED_BIN_OPS.get(type(node.op))
            if bin_operator is None:
                raise ValueError("Unsafe expression")
            return bin_operator(eval_(node.left), eval_(node.right))
        if isinstance(node, ast.UnaryOp):
            unary_operator = ALLOWED_UNARY_OPS.get(type(node.op))
            if unary_operator is None:
                raise ValueError("Unsafe expression")
            return unary_operator(eval_(node.operand))
        raise ValueError("Unsafe expression")

    parsed = ast.parse(expr, mode="eval")
    return eval_(parsed.body)


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
