"""Simple helpers for retrieving secrets from the environment."""

from __future__ import annotations

import logging
import os
from typing import Any, cast

log = logging.getLogger(__name__)


class SecretManager:
    """Encapsulate interactions with environment-provided secrets."""

    @staticmethod
    def get_secret(key: str, default: Any | None = None) -> Any | None:
        value = os.getenv(key, default)
        if value in {None, ""} and default is None:
            log.warning("Secret %s not found", key)
        return value

    @staticmethod
    def get_required_secret(key: str) -> str:
        value = os.getenv(key)
        if value in {None, ""}:
            raise ValueError(f"Required secret {key} not found")
        return cast(str, value)

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        return bool(api_key and len(api_key) >= 10)
