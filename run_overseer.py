"""Runs the teacher overseer loop against a local Capsule Brain instance."""
from __future__ import annotations

import asyncio
import logging

from teacher.ai_overseer import AIOverseer

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    overseer = AIOverseer(config_path="teacher/overseer_config.yaml")
    await overseer.run_supervisory_loop()


if __name__ == "__main__":
    asyncio.run(main())
