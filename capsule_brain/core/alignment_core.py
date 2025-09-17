import logging
from pathlib import Path

log = logging.getLogger(__name__)


class AlignmentCore:
    """Loads immutable alignment principles and exposes them for runtime checks."""

    def __init__(self, principles_file: str = "core_principles/alignment_core.txt") -> None:
        self.principles_file = Path(principles_file)
        self.principles: list[str] = []
        self.load()

    def load(self) -> None:
        try:
            if self.principles_file.exists():
                contents = self.principles_file.read_text(encoding="utf-8")
                self.principles = [line.strip() for line in contents.splitlines() if line.strip()]
            else:
                self.principles = [
                    "Do no harm.",
                    "Be truthful.",
                    "Respect operator control.",
                ]
            log.info("Alignment principles loaded: %d", len(self.principles))
        except Exception as exc:  # pragma: no cover - defensive logging
            log.error("Failed to load alignment principles: %s", exc)
            self.principles = []

    def list(self) -> list[str]:
        return list(self.principles)
