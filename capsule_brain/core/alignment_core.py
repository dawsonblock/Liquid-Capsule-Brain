"""Alignment core utilities."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AlignmentCore:
    """Load immutable alignment principles and expose them for runtime checks."""

    def __init__(self, principles_file: str = "core_principles/alignment_core.txt") -> None:
        self.principles_file = Path(principles_file)
        self.principles: list[str] = []
        self.load()

    def load(self) -> None:
        try:
            if self.principles_file.exists():
                self.principles = [
                    line.strip()
                    for line in self.principles_file.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
            else:
                self.principles = [
                    "Do no harm.",
                    "Be truthful.",
                    "Respect operator control.",
                ]
            logger.info("Alignment principles loaded: %d", len(self.principles))
        except Exception:  # pragma: no cover - defensive logging
            logger.exception("Failed to load alignment principles")
            self.principles = []

    def list(self) -> list[str]:
        return list(self.principles)
