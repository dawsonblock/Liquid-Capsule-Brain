"""Helpers for fetching environment-based secrets."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


class SecretManager:
    """Centralised helper for retrieving secrets with fallbacks."""

    @staticmethod
    def get_secret(key: str, default: str | None = None) -> str | None:
        value = os.getenv(key, default)
        if value is None:
            logger.warning("Secret %s not found", key)
        return value

    @staticmethod
    def get_required_secret(key: str) -> str:
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Required secret {key} not found")
        return value

    @staticmethod
    def validate_api_key(api_key: str | None) -> bool:
        return bool(api_key and len(api_key) >= 10)
