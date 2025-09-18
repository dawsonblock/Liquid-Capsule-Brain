"""FastAPI dependency helpers for Capsule Brain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException, Request, status

if TYPE_CHECKING:
    from capsule_brain.core.capsule_engine import CapsuleEngine


_ENGINE_STATE_ATTR = "capsule_engine"


def attach_engine(app: FastAPI, engine: "CapsuleEngine") -> None:
    """Attach the CapsuleEngine instance to app state."""

    setattr(app.state, _ENGINE_STATE_ATTR, engine)


def detach_engine(app: FastAPI) -> "CapsuleEngine | None":
    """Remove the CapsuleEngine from state and return it if present."""

    engine = getattr(app.state, _ENGINE_STATE_ATTR, None)
    if hasattr(app.state, _ENGINE_STATE_ATTR):
        delattr(app.state, _ENGINE_STATE_ATTR)
    return engine


def peek_engine(app: FastAPI) -> "CapsuleEngine | None":
    """Inspect the current CapsuleEngine without enforcing readiness."""

    return getattr(app.state, _ENGINE_STATE_ATTR, None)


def get_engine(request: Request) -> "CapsuleEngine":
    """Dependency that provides the current engine or raises 503."""

    engine = peek_engine(request.app)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="engine not ready",
        )
    return engine

