#!/usr/bin/env python3
"""Simple validation script to check if the build prerequisites are met."""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterable
from pathlib import Path


def check_file_syntax(filepath: Path) -> tuple[bool, str | None]:
    """Check if a Python file has valid syntax."""

    try:
        source = filepath.read_text(encoding="utf-8")
        ast.parse(source)
        return True, None
    except SyntaxError as error:
        return False, str(error)


def _print_header() -> None:
    print("=== Liquid Capsule Brain Build Validation ===")


def _check_python_version() -> None:
    print(f"Python version: {sys.version}")
    print("✅ Python version OK")


def _check_required_files(required_files: Iterable[Path]) -> list[Path]:
    missing: list[Path] = []
    for file_path in required_files:
        if file_path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            missing.append(file_path)
    return missing


def _check_python_syntax(files: Iterable[Path]) -> list[tuple[Path, str]]:
    errors: list[tuple[Path, str]] = []
    for file_path in files:
        if not file_path.exists():
            print(f"⚠️  {file_path} not found for syntax check")
            continue

        valid, error = check_file_syntax(file_path)
        if valid:
            print(f"✅ {file_path} syntax OK")
        else:
            print(f"❌ {file_path} syntax error: {error}")
            assert error is not None
            errors.append((file_path, error))
    return errors


def _check_gitignore() -> None:
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        print("⚠️  .gitignore not found")
        return

    content = gitignore_path.read_text(encoding="utf-8")
    expected_entries = [".venv/", ".env"]
    missing_entries = [entry for entry in expected_entries if entry not in content]

    if missing_entries:
        print(f"⚠️  .gitignore missing entries: {missing_entries}")
    else:
        print("✅ .gitignore has required entries")


def _check_requirements() -> None:
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        print("⚠️  requirements.txt not found")
        return

    requirements = requirements_path.read_text(encoding="utf-8")
    if "torch==2.1.0" in requirements:
        print("❌ torch==2.1.0 incompatible with Python 3.12+")
    elif "torch==" in requirements:
        print("✅ PyTorch version specified")
    else:
        print("⚠️  No PyTorch version found")


def main() -> int:
    _print_header()
    _check_python_version()

    required_files = [
        Path(".env.example"),
        Path(".env.reverse-proxy.example"),
        Path("requirements.txt"),
        Path("requirements-dev.txt"),
        Path("launch_capsule_brain.py"),
        Path("capsule_brain/api/server.py"),
        Path("Dockerfile"),
        Path("Makefile"),
    ]
    missing_files = _check_required_files(required_files)

    python_files = [
        Path("launch_capsule_brain.py"),
        Path("capsule_brain/api/server.py"),
    ]
    syntax_errors = _check_python_syntax(python_files)

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
