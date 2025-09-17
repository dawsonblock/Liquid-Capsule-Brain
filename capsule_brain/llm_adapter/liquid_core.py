"""Simplified liquid neural network adapter used for demonstrations."""

from __future__ import annotations

import logging
from typing import Any, Iterable

import numpy as np
import torch


log = logging.getLogger(__name__)

INPUT_SIZE = 384
HIDDEN_SIZE = 256
OUTPUT_SIZE = 384


class MockCfC(torch.nn.Module):
    """A toy closed-form continuous-time cell."""

    def __init__(self, in_features: int, hidden_size: int, out_features: int) -> None:
        super().__init__()
        self.linear1 = torch.nn.Linear(in_features, hidden_size)
        self.linear2 = torch.nn.Linear(hidden_size, out_features)
        self.activation = torch.nn.Tanh()

    def forward(
        self, inputs: torch.Tensor, hidden: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        outputs = []
        for step in range(inputs.shape[1]):
            x_step = inputs[:, step, :]
            hidden = self.activation(self.linear1(x_step) + hidden)
            outputs.append(self.linear2(hidden).unsqueeze(1))
        return torch.cat(outputs, dim=1), hidden


class LiquidReasoningCore:
    """Mimics a liquid neural network reasoning layer."""

    def __init__(self) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        log.info("Liquid Core on %s", self.device)
        self.cfc_model = MockCfC(INPUT_SIZE, HIDDEN_SIZE, OUTPUT_SIZE).to(self.device)
        self.hidden_state = torch.zeros(1, HIDDEN_SIZE, device=self.device)
        self.engine_ref: Any | None = None
        self.state_health_checks = True

    def _text_to_embedding(self, text: str) -> torch.Tensor:
        token_hash = hash(text) % (2**31)
        bits = [(token_hash >> idx) & 1 for idx in range(INPUT_SIZE)]
        tensor = torch.tensor(bits, dtype=torch.float32, device=self.device)
        return tensor.unsqueeze(0)

    def _check_state(self) -> bool:
        if not self.state_health_checks:
            return True

        array = self.hidden_state.detach().cpu().numpy()
        if not np.isfinite(array).all():
            self.hidden_state = torch.zeros(1, HIDDEN_SIZE, device=self.device)
            return False
        if np.abs(array).max() > 100:
            self.hidden_state = torch.tanh(self.hidden_state)
            return False
        return True

    async def _decode(self, vec: torch.Tensor) -> str:
        if self.engine_ref is not None:
            vector_list = vec.squeeze(0).detach().cpu().numpy().tolist()
            results = self.engine_ref.search_memory(vector_list, top_k=1)
            if results:
                focus = results[0].get("text", "processing")
                return f"[Liquid Thought] Focusing on: {focus}."

        norm = float(torch.norm(vec).item())
        if norm > 5:
            return "[Liquid Thought] High-intensity cognitive processing detected."
        if norm > 2:
            return "[Liquid Thought] Moderate cognitive activity."
        return "[Liquid Thought] Low-level background processing."

    async def process_stream(self, context_snippets: Iterable[str]) -> dict[str, Any]:
        snippets = list(context_snippets)
        try:
            if not self._check_state():
                log.debug("Liquid core hidden state refreshed due to health check.")

            if snippets:
                embeddings = [self._text_to_embedding(text) for text in snippets[:10]]
                inputs = torch.stack(embeddings, dim=1)
            else:
                inputs = torch.zeros(1, 1, INPUT_SIZE, device=self.device)

            with torch.no_grad():
                outputs, self.hidden_state = self.cfc_model(inputs, self.hidden_state)
                final_state = outputs[:, -1, :]

            decoded = await self._decode(final_state)
            self._check_state()
            return {
                "text": decoded,
                "output_norm": float(torch.norm(final_state).item()),
                "context_length": len(snippets),
            }
        except Exception as exc:  # pragma: no cover - defensive logging
            log.error("Liquid processing error: %s", exc)
            return {"text": "[Error] Liquid core processing failed."}

    def attach_engine_reference(self, engine: Any) -> None:
        self.engine_ref = engine
