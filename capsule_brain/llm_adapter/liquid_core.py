"""Mock implementation of a liquid neural network reasoning core."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import torch

logger = logging.getLogger(__name__)

INPUT_SIZE = 384
HIDDEN_SIZE = 256
OUTPUT_SIZE = 384


class MockCfC(torch.nn.Module):
    def __init__(self, in_features: int, hidden_size: int, out_features: int) -> None:
        super().__init__()
        self.l1 = torch.nn.Linear(in_features, hidden_size)
        self.l2 = torch.nn.Linear(hidden_size, out_features)
        self.act = torch.nn.Tanh()

    def forward(  # type: ignore[override]
        self, inputs: torch.Tensor, hidden: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        outputs = []
        for timestep in range(inputs.shape[1]):
            x_val = inputs[:, timestep, :]
            hidden = self.act(self.l1(x_val) + hidden)
            outputs.append(self.l2(hidden).unsqueeze(1))
        return torch.cat(outputs, dim=1), hidden


class LiquidReasoningCore:
    def __init__(self) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Liquid Core on %s", self.device)
        self.cfc_model = MockCfC(INPUT_SIZE, HIDDEN_SIZE, OUTPUT_SIZE).to(self.device)
        self.hidden_state = torch.zeros(1, HIDDEN_SIZE).to(self.device)
        self.engine_ref: Any | None = None
        self.state_health_checks = True

    def _text_to_embedding(self, text: str) -> torch.Tensor:
        hashed = hash(text) % (2**31)
        array = [(hashed >> idx) & 1 for idx in range(INPUT_SIZE)]
        return torch.tensor(array, dtype=torch.float32, device=self.device).unsqueeze(0)

    def _check_state(self) -> bool:
        if not self.state_health_checks:
            return True
        arr = self.hidden_state.detach().cpu().numpy()
        if not np.isfinite(arr).all():
            self.hidden_state = torch.zeros(1, HIDDEN_SIZE).to(self.device)
            return False
        if abs(arr).max() > 100:
            self.hidden_state = torch.tanh(self.hidden_state)
            return False
        return True

    async def _decode(self, vector: torch.Tensor) -> str:
        if self.engine_ref:
            vector_list = vector.squeeze(0).detach().cpu().numpy().tolist()
            results = self.engine_ref.search_memory(vector_list, top_k=1)
            if results:
                return (
                    "[Liquid Thought] Focusing on: "
                    f"{results[0].get('text', 'processing')}"
                    "."
                )
        norm = float(torch.norm(vector).item())
        if norm > 5:
            return "[Liquid Thought] High-intensity cognitive processing detected."
        if norm > 2:
            return "[Liquid Thought] Moderate cognitive activity."
        return "[Liquid Thought] Low-level background processing."

    async def process_stream(self, context_snippets: list[str]) -> dict[str, Any]:
        try:
            if not self._check_state():
                logger.warning("Hidden state reset during process_stream")
            inputs = (
                torch.zeros(1, 1, INPUT_SIZE, device=self.device)
                if not context_snippets
                else torch.stack(
                    [self._text_to_embedding(snippet) for snippet in context_snippets[:10]],
                    dim=1,
                )
            )
            with torch.no_grad():
                out, self.hidden_state = self.cfc_model(inputs, self.hidden_state)
                final = out[:, -1, :]
            decoded = await self._decode(final)
            self._check_state()
            return {
                "text": decoded,
                "output_norm": float(torch.norm(final).item()),
                "context_length": len(context_snippets),
            }
        except Exception:  # pragma: no cover - defensive logging
            logger.exception("Liquid processing error")
            return {"text": "[Error] Liquid core processing failed."}

    def attach_engine_reference(self, engine: Any) -> None:
        self.engine_ref = engine
