import ast
import asyncio
import logging
import operator as op
import time
from typing import Any

from ..retrieval.index import retrieve_topk
from ..security.input_sanitizer import validate_tool_params

log = logging.getLogger(__name__)

ALLOWED_OPS: dict[type[ast.AST], Any] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: lambda value: -value,
}


def _safe_eval(expr: str) -> Any:
    def eval_node(node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            operator = ALLOWED_OPS[type(node.op)]
            return operator(eval_node(node.left), eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            operator = ALLOWED_OPS[type(node.op)]
            return operator(eval_node(node.operand))
        raise ValueError("Unsafe expression")

    parsed = ast.parse(expr, mode="eval")
    return eval_node(parsed.body)


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
                sanitized_hint = validate_tool_params(hint)
                results.append(await self._execute_tool(sanitized_hint))
            except Exception as exc:  # noqa: BLE001 - surface tool errors cleanly
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
            return {"tool": "calculator", "expression": expression, "result": _safe_eval(expression)}

        return {"tool": name, "status": "completed", "data": "Mock tool execution result"}

    async def health_check(self) -> bool:
        return True
