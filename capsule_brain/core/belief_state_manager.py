import logging
import time
from typing import Any

log = logging.getLogger(__name__)


class BeliefStateManager:
    """Manages the AGI's working memory and belief state."""

    def __init__(self, engine):
        self.engine = engine
        self.current_query: str = ""
        self.retrieved_knowledge: list[str] = []
        self.current_plan: dict[str, Any] = {}
        self.self_awareness_metrics: dict[str, Any] = {}
        self.last_update: float = time.time()

    def update_state(
        self,
        new_query: str,
        retrieved_knowledge: list[str],
        current_plan: dict[str, Any],
        self_awareness_metrics: dict[str, Any],
    ) -> None:
        self.current_query = new_query
        self.retrieved_knowledge = retrieved_knowledge
        self.current_plan = current_plan
        self.self_awareness_metrics = self_awareness_metrics
        self.last_update = time.time()

    def synthesize_context_for_llm(self) -> tuple[str, str]:
        """Return (context, system_prompt) strings for LLM calls."""
        context_lines = [
            f"Query: {self.current_query}",
            f"Retrieved: {' | '.join(self.retrieved_knowledge[:5])}",
            f"Plan keys: {list(self.current_plan.keys())}",
            f"Self-metrics: phi={self.self_awareness_metrics.get('phi', 0.0):.2f}",
        ]
        system_prompt = (
            "You are Capsule Brain. Be succinct, cite tools you would call, and propose next steps."
        )
        return "\n".join(context_lines), system_prompt
