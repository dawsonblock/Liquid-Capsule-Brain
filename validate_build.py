#!/usr/bin/env python3
"""Simple validation script to check if the build prerequisites are met."""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterable
from pathlib import Path

REQUIRED_FILES: tuple[str, ...] = (
    ".env.example",
    ".env.reverse-proxy.example",
    "requirements.txt",
    "requirements-dev.txt",
    "launch_capsule_brain.py",
    "capsule_brain/api/server.py",
    "Dockerfile",
    "Makefile",
)

PYTHON_FILES: tuple[str, ...] = (
    "launch_capsule_brain.py",
    "capsule_brain/api/server.py",
)


def check_file_syntax(path: Path) -> tuple[bool, str | None]:
    """Check if a Python file has valid syntax."""

    try:
        ast.parse(path.read_text())
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def existing_paths(paths: Iterable[str]) -> dict[str, Path]:
    return {entry: Path(entry) for entry in paths if Path(entry).exists()}


def display_summary(missing: list[str], syntax_errors: list[tuple[str, str]]) -> int:
    print("\n=== Summary ===")
    if missing:
        print(f"❌ Missing files: {missing}")
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


def main() -> int:  # noqa: PLR0912 - simple diagnostic script
    print("=== Liquid Capsule Brain Build Validation ===")

    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 12):
        print("⚠️  Warning: Python 3.12+ recommended")
    else:
        print("✅ Python version OK")

    missing_files: list[str] = []
    for name in REQUIRED_FILES:
        path = Path(name)
        if path.exists():
            print(f"✅ {name} exists")
        else:
            print(f"❌ {name} missing")
            missing_files.append(name)

    syntax_errors: list[tuple[str, str]] = []
    available_python_files = existing_paths(PYTHON_FILES)
    for name, path in available_python_files.items():
        valid, error = check_file_syntax(path)
        if valid:
            print(f"✅ {name} syntax OK")
        else:
            print(f"❌ {name} syntax error: {error}")
            syntax_errors.append((name, error or "Unknown error"))

    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
        expected_entries = (".venv/", ".env")
        missing_entries = [entry for entry in expected_entries if entry not in gitignore_content]
        if missing_entries:
            print(f"⚠️  .gitignore missing entries: {missing_entries}")
        else:
            print("✅ .gitignore has required entries")

    requirements_path = Path("requirements.txt")
    if requirements_path.exists():
        requirements = requirements_path.read_text()
        if "torch==2.1.0" in requirements:
            print("❌ torch==2.1.0 incompatible with Python 3.12+")
        elif "torch==" in requirements:
            print("✅ PyTorch version specified")
        else:
            print("⚠️  No PyTorch version found")

    return display_summary(missing_files, syntax_errors)


if __name__ == "__main__":
    sys.exit(main())
