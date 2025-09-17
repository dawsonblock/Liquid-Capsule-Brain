"""Utility helpers for retrieving secrets and API keys."""

from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger(__name__)


class SecretManager:
    """Simple wrapper around environment variables with logging."""

    @staticmethod
    def get_secret(key: str, default: Any | None = None) -> Any | None:
        value = os.getenv(key, default)
        if value is None and default is None:
            log.warning("Secret %s not found", key)
        return value

    @staticmethod
    def get_required_secret(key: str) -> str:
        value = os.getenv(key)
        if not value:
            msg = f"Required secret {key} not found"
            raise ValueError(msg)
        return value

    @staticmethod
    def validate_api_key(api_key: str | None) -> bool:
        return bool(api_key and len(api_key) >= 10)
