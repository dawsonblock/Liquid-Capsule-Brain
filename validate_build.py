#!/usr/bin/env python3
"""Utility script to validate the repository's build prerequisites."""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterable
from pathlib import Path

REQUIRED_FILES = (
    ".env.example",
    ".env.reverse-proxy.example",
    "requirements.txt",
    "requirements-dev.txt",
    "launch_capsule_brain.py",
    "capsule_brain/api/server.py",
    "Dockerfile",
    "Makefile",
)

PYTHON_SYNTAX_TARGETS = (
    "launch_capsule_brain.py",
    "capsule_brain/api/server.py",
)

EXPECTED_GITIGNORE_ENTRIES = (".venv/", ".env")


def check_file_syntax(path: Path) -> tuple[bool, str | None]:
    """Return ``True`` if the file contains valid Python syntax."""

    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, str(exc)

    try:
        ast.parse(source)
    except SyntaxError as exc:  # pragma: no cover - depends on invalid inputs
        return False, str(exc)
    return True, None


def _print_header() -> None:
    print("=== Liquid Capsule Brain Build Validation ===")
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 12):
        print("⚠️  Warning: Python 3.12+ recommended")
    else:
        print("✅ Python version OK")


def _report_missing_files(files: Iterable[str]) -> list[str]:
    missing = []
    for file_name in files:
        if Path(file_name).exists():
            print(f"✅ {file_name} exists")
        else:
            print(f"❌ {file_name} missing")
            missing.append(file_name)
    return missing


def _check_python_syntax(files: Iterable[str]) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    for file_name in files:
        path = Path(file_name)
        if not path.exists():
            print(f"⚠️  {file_name} not found for syntax check")
            continue

        valid, error = check_file_syntax(path)
        if valid:
            print(f"✅ {file_name} syntax OK")
        else:
            print(f"❌ {file_name} syntax error: {error}")
            errors.append((file_name, error or "unknown error"))
    return errors


def _check_gitignore() -> None:
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        print("⚠️  .gitignore missing")
        return

    content = gitignore.read_text(encoding="utf-8")
    missing = [entry for entry in EXPECTED_GITIGNORE_ENTRIES if entry not in content]
    if missing:
        print(f"⚠️  .gitignore missing entries: {missing}")
    else:
        print("✅ .gitignore has required entries")


def _check_requirements() -> None:
    requirements = Path("requirements.txt")
    if not requirements.exists():
        print("⚠️  requirements.txt not found")
        return

    content = requirements.read_text(encoding="utf-8")
    if "torch==2.1.0" in content:
        print("❌ torch==2.1.0 incompatible with Python 3.12+")
    elif "torch==" in content:
        print("✅ PyTorch version specified")
    else:
        print("⚠️  No PyTorch version found")


def main() -> int:
    _print_header()

    missing_files = _report_missing_files(REQUIRED_FILES)
    syntax_errors = _check_python_syntax(PYTHON_SYNTAX_TARGETS)
    _check_gitignore()
    _check_requirements()

    print("\n=== Summary ===")
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return 1

    if syntax_errors:
        print(f"❌ Syntax errors: {syntax_errors}")
        return 1

    print("✅ All build prerequisites are met!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and configure your settings")
    print("2. Run 'make dev-setup' to install dependencies")
    print("3. Run 'make dev' to start development server")
    print("4. Run 'make build' to build Docker image")
    return 0


if __name__ == "__main__":
    sys.exit(main())
