"""Command-line entry point for the external AI overseer."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from teacher.ai_overseer import AIOverseer

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    overseer = AIOverseer(config_path=Path("teacher/overseer_config.yaml"))
    await overseer.run_supervisory_loop(num_cycles=5)


if __name__ == "__main__":
    asyncio.run(main())
