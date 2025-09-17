"""Entry point for running the Capsule Brain API server."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "capsule_brain.api.server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )


if __name__ == "__main__":
    main()
