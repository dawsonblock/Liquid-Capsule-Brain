#!/usr/bin/env python3
"""Validate that the local workspace has the prerequisites to run Capsule Brain."""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import Iterable, Sequence


def check_file_syntax(filepath: Path) -> tuple[bool, str | None]:
    """Return whether ``filepath`` contains valid Python syntax."""
    try:
        source = filepath.read_text(encoding="utf-8")
    except OSError as exc:
        return False, str(exc)

    try:
        ast.parse(source)
    except SyntaxError as exc:  # pragma: no cover - surfaced to the caller
        return False, str(exc)

    return True, None


def _print_file_status(required_files: Sequence[Path]) -> list[Path]:
    missing: list[Path] = []
    for file_path in required_files:
        if file_path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            missing.append(file_path)
    return missing


def _check_python_files(python_files: Iterable[Path]) -> list[tuple[Path, str]]:
    syntax_errors: list[tuple[Path, str]] = []
    for file_path in python_files:
        if not file_path.exists():
            print(f"⚠️  {file_path} not found for syntax check")
            continue

        valid, error = check_file_syntax(file_path)
        if valid:
            print(f"✅ {file_path} syntax OK")
        else:
            print(f"❌ {file_path} syntax error: {error}")
            syntax_errors.append((file_path, error or "unknown error"))
    return syntax_errors


def _gitignore_has_entries(entries: Iterable[str]) -> bool:
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        return False

    content = gitignore.read_text(encoding="utf-8")
    return all(entry in content for entry in entries)


def _check_requirements() -> None:
    requirements = Path("requirements.txt")
    if not requirements.exists():
        return

    content = requirements.read_text(encoding="utf-8")
    if "torch==2.1.0" in content:
        print("❌ torch==2.1.0 incompatible with Python 3.12+")
    elif "torch==" in content:
        print("✅ PyTorch version specified")
    else:
        print("⚠️  No PyTorch version found")


def main() -> int:
    print("=== Liquid Capsule Brain Build Validation ===")

    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 11):
        print("⚠️  Warning: Python 3.11+ recommended")
    else:
        print("✅ Python version OK")

    required = [
        Path(".env.example"),
        Path(".env.reverse-proxy.example"),
        Path("requirements.txt"),
        Path("requirements-dev.txt"),
        Path("launch_capsule_brain.py"),
        Path("capsule_brain/api/server.py"),
        Path("Dockerfile"),
        Path("Makefile"),
    ]
    missing_files = _print_file_status(required)

    syntax_targets = [
        Path("launch_capsule_brain.py"),
        Path("capsule_brain/api/server.py"),
    ]
    syntax_errors = _check_python_files(syntax_targets)

    expected_gitignore_entries = [".venv/", ".env"]
    if _gitignore_has_entries(expected_gitignore_entries):
        print("✅ .gitignore has required entries")
    else:
        print(f"⚠️  .gitignore missing entries: {expected_gitignore_entries}")

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
