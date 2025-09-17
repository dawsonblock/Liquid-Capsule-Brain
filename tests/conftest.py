"""Pytest configuration for the Capsule Brain project."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is available on the Python import path so that
# ``capsule_brain`` can be imported when tests are executed from within the
# ``tests`` directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

# Explicitly enable ``pytest_asyncio`` so that async tests decorated with
# ``@pytest.mark.asyncio`` are executed using an event loop without requiring
# every test module to import the plugin manually.
pytest_plugins = ("pytest_asyncio",)
