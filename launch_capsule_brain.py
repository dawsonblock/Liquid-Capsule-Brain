from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("capsule_brain.api.server:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
