"""Convenience launcher for the Capsule Brain FastAPI application."""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
else:
    print("⚠️  No .env file found")


def main() -> None:
    env = os.getenv("APP_ENV", "development").lower()
    reload = env in {"local", "development", "dev"}
    workers = int(os.getenv("UVICORN_WORKERS", "1" if reload else "2"))
    uvicorn.run(
        "capsule_brain.api.server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=reload,
        workers=workers,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
