"""Admin authentication dependency utilities."""

from __future__ import annotations

import os
from functools import lru_cache

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

ADMIN_HEADER_NAME = "x-admin-token"
_admin_scheme = APIKeyHeader(name=ADMIN_HEADER_NAME, auto_error=False)
_LOCAL_PROFILES = {"local", "development", "dev"}


@lru_cache(maxsize=1)
def _local_profile_tokens() -> tuple[str, ...]:
    """Profiles that should bypass admin token enforcement when unset."""
    return tuple(_LOCAL_PROFILES)


def _current_profile() -> str:
    return (
        os.getenv("APP_PROFILE")
        or os.getenv("APP_ENV")
        or os.getenv("ENVIRONMENT")
        or os.getenv("ENV")
        or "development"
    )


def require_admin_token(token: str | None = Security(_admin_scheme)) -> None:
    """Validate the admin token header for sensitive routes."""

    expected = os.getenv("ADMIN_TOKEN")
    if expected:
        if token != expected:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="invalid admin token",
            )
        return

    if _current_profile().lower() in _local_profile_tokens():
        # In local development we allow access when no token configured.
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="admin token not configured",
    )

