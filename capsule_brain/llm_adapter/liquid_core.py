"""Synthetic liquid neural network adapter used for demonstrations."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

import numpy as np
import torch

log = logging.getLogger(__name__)

INPUT_SIZE = 384
HIDDEN_SIZE = 256
OUTPUT_SIZE = 384


class MockCfC(torch.nn.Module):
    """Tiny continuous-time recurrent block used for experiments."""

    def __init__(self, in_features: int, hidden_size: int, out_features: int) -> None:
        super().__init__()
        self.linear_in = torch.nn.Linear(in_features, hidden_size)
        self.linear_out = torch.nn.Linear(hidden_size, out_features)
        self.activation = torch.nn.Tanh()

    def forward(
        self, inputs: torch.Tensor, hidden: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        outputs = []
        for timestep in range(inputs.shape[1]):
            x_t = inputs[:, timestep, :]
            hidden = self.activation(self.linear_in(x_t) + hidden)
            outputs.append(self.linear_out(hidden).unsqueeze(1))
        return torch.cat(outputs, dim=1), hidden


class LiquidReasoningCore:
    """Surface area for simulating Liquid Neural Network behaviour."""

    def __init__(self) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        log.info("Liquid Core on %s", self.device)
        self.cfc_model = MockCfC(INPUT_SIZE, HIDDEN_SIZE, OUTPUT_SIZE).to(self.device)
        self.hidden_state = torch.zeros(1, HIDDEN_SIZE, device=self.device)
        self.engine_ref: Any | None = None
        self.state_health_checks = True

    def attach_engine_reference(self, engine: Any) -> None:
        self.engine_ref = engine

    def _text_to_embedding(self, text: str) -> torch.Tensor:
        hashed_value = hash(text) % (2**31)
        bits = [(hashed_value >> bit) & 1 for bit in range(INPUT_SIZE)]
        return torch.tensor(bits, dtype=torch.float32, device=self.device).unsqueeze(0)

    def _check_state(self) -> bool:
        if not self.state_health_checks:
            return True

        snapshot = self.hidden_state.detach().cpu().numpy()
        if not np.isfinite(snapshot).all():
            self.hidden_state = torch.zeros(1, HIDDEN_SIZE, device=self.device)
            return False

        if np.abs(snapshot).max() > 100:
            self.hidden_state = torch.tanh(self.hidden_state)
            return False

        return True

    async def _decode(self, vector: torch.Tensor) -> str:
        if self.engine_ref is not None:
            vector_list = vector.squeeze(0).detach().cpu().numpy().tolist()
            results = self.engine_ref.search_memory(vector_list, top_k=1)
            if results:
                focus = results[0].get("text", "processing")
                return f"[Liquid Thought] Focusing on: {focus}."

        norm = float(torch.norm(vector).item())
        if norm > 5:
            return "[Liquid Thought] High-intensity cognitive processing detected."
        if norm > 2:
            return "[Liquid Thought] Moderate cognitive activity."
        return "[Liquid Thought] Low-level background processing."

    async def process_stream(self, context_snippets: Sequence[str]) -> dict[str, Any]:
        try:
            if not self._check_state():
                log.debug("Resetting hidden state before processing stream")

            if context_snippets:
                embeddings = [self._text_to_embedding(text) for text in context_snippets[:10]]
                inputs = torch.stack(embeddings, dim=1)
            else:
                inputs = torch.zeros(1, 1, INPUT_SIZE, device=self.device)

            with torch.no_grad():
                outputs, self.hidden_state = self.cfc_model(inputs, self.hidden_state)
                final_vector = outputs[:, -1, :]

            decoded = await self._decode(final_vector)
            self._check_state()
            return {
                "text": decoded,
                "output_norm": float(torch.norm(final_vector).item()),
                "context_length": len(context_snippets),
            }
        except Exception as exc:  # pragma: no cover - defensive logging
            log.error("Liquid processing error: %s", exc)
            return {"text": "[Error] Liquid core processing failed."}
