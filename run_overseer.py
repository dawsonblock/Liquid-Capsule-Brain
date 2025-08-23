import asyncio
import logging

from teacher.ai_overseer import AIOverseer

logging.basicConfig(level=logging.INFO)


async def main():
    o = AIOverseer(config_path="teacher/overseer_config.yaml")
    await o.run_supervisory_loop(num_cycles=5)


if __name__ == "__main__":
    asyncio.run(main())
