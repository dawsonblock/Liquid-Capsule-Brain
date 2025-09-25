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
    import logging

    log = logging.getLogger(__name__)

    expected = os.getenv("ADMIN_TOKEN")
    log.info(f"Admin token validation - Expected: {bool(expected)}, Received: {bool(token)}")

    if expected:
        if token != expected:
            log.warning("Invalid admin token provided")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="invalid admin token",
            )
        log.info("Admin token validation successful")
        return

    if _current_profile().lower() in _local_profile_tokens():
        # In local development we allow access when no token configured.
        log.info("Local profile - bypassing admin token")
        return

    log.warning("Admin token not configured and not in local profile")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="admin token not configured",
    )
