"""Belief state aggregation helpers for Capsule Brain."""

from __future__ import annotations

import logging
import time
from typing import Any

from capsule_brain.llm_adapter.deepseek_client import DeepSeekClient

log = logging.getLogger(__name__)


class BeliefStateManager:
    """Manages the AGI's working memory and belief state."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine
        self.current_query: str = ""
        self.retrieved_knowledge: list[str] = []
        self.current_plan: dict[str, Any] = {}
        self.self_awareness_metrics: dict[str, Any] = {}
        self.last_update: float = time.time()
        self.deepseek_client = DeepSeekClient()

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
        
        # Broadcast state update to GUI
        if hasattr(self.engine, 'broadcast_belief_state_update'):
            self.engine.broadcast_belief_state_update()

    def synthesize_context_for_llm(self) -> tuple[str, str]:
        """Return ``(context, system_prompt)`` strings for LLM calls."""

        # Get recent conversation history for better context
        recent_memories = []
        if hasattr(self.engine, 'memory') and hasattr(self.engine.memory, 'recent_memories'):
            recent_memories = self.engine.memory.recent_memories[-6:]  # Last 6 exchanges
        
        context_lines = [
            f"Query: {self.current_query}",
            f"Retrieved: {' | '.join(self.retrieved_knowledge[:5])}",
            f"Plan keys: {list(self.current_plan.keys())}",
            f"Self-metrics: phi={self.self_awareness_metrics.get('phi', 0.0):.2f}",
        ]
        
        # Add recent conversation context
        if recent_memories:
            context_lines.append("\nRecent conversation:")
            for memory in recent_memories:
                role = memory.get('role', 'unknown')
                content = memory.get('content', '')[:200]  # Limit length
                context_lines.append(f"{role}: {content}")
        
        system_prompt = (
            "You are Capsule Brain Supreme AGI. Maintain conversation context and memory. "
            "Be succinct, cite tools you would call, and propose next steps. "
            "Reference previous parts of the conversation when relevant."
        )
        return "\n".join(context_lines), system_prompt

    async def generate_llm_response(self) -> dict[str, Any]:
        """Generate a response using DeepSeek V3."""
        context, system_prompt = self.synthesize_context_for_llm()
        return await self.deepseek_client.generate_response(
            context, system_prompt
        )
