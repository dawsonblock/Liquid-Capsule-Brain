from __future__ import annotations

import logging
import os
from typing import Any


log = logging.getLogger(__name__)


class SecretManager:
    """Fetch configuration secrets from environment variables."""

    @staticmethod
    def get_secret(key: str, default: Any | None = None) -> Any | None:
        """Return the secret value for ``key`` if present."""

        value = os.getenv(key, default)
        if value in (None, "") and default is None:
            log.warning("Secret %s not found", key)
        return value

    @staticmethod
    def get_required_secret(key: str) -> str:
        """Return the secret value or raise if it is missing."""

        value = os.getenv(key)
        if value is None or value == "":
            raise ValueError(f"Required secret {key} not found")
        return value

    @staticmethod
    def validate_api_key(api_key: str | None) -> bool:
        """Return ``True`` when ``api_key`` looks well-formed."""

        return bool(api_key and len(api_key) >= 10)
