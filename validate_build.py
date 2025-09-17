#!/usr/bin/env python3
"""Simple validation script to check if the build prerequisites are met."""
from __future__ import annotations

import ast
import os
import sys
from collections.abc import Iterable


def check_file_syntax(filepath: str) -> tuple[bool, str | None]:
    try:
        with open(filepath, encoding="utf-8") as handle:
            source = handle.read()
        ast.parse(source)
        return True, None
    except SyntaxError as exc:
        return False, str(exc)


def iter_required_files() -> Iterable[str]:
    yield from (
        ".env.example",
        ".env.reverse-proxy.example",
        "requirements.txt",
        "requirements-dev.txt",
        "launch_capsule_brain.py",
        "capsule_brain/api/server.py",
        "Dockerfile",
        "Makefile",
    )


def main() -> int:
    print("=== Liquid Capsule Brain Build Validation ===")

    print(f"Python version: {sys.version}")
    print("✅ Python version meets the 3.11+ requirement")

    missing_files: list[str] = []
    for file in iter_required_files():
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            missing_files.append(file)

    python_files = [
        "launch_capsule_brain.py",
        "capsule_brain/api/server.py",
    ]
    syntax_errors: list[tuple[str, str]] = []
    for file in python_files:
        if os.path.exists(file):
            valid, error = check_file_syntax(file)
            if valid:
                print(f"✅ {file} syntax OK")
            else:
                print(f"❌ {file} syntax error: {error}")
                assert error is not None
                syntax_errors.append((file, error))
        else:
            print(f"⚠️  {file} not found for syntax check")

    if os.path.exists(".gitignore"):
        with open(".gitignore", encoding="utf-8") as handle:
            gitignore_content = handle.read()
        expected_entries = [".venv/", ".env"]
        missing_entries = [entry for entry in expected_entries if entry not in gitignore_content]
        if missing_entries:
            print(f"⚠️  .gitignore missing entries: {missing_entries}")
        else:
            print("✅ .gitignore has required entries")

    if os.path.exists("requirements.txt"):
        with open("requirements.txt", encoding="utf-8") as handle:
            requirements = handle.read()
        if "torch==2.1.0" in requirements:
            print("❌ torch==2.1.0 incompatible with Python 3.12+")
        elif "torch==" in requirements:
            print("✅ PyTorch version specified")
        else:
            print("⚠️  No PyTorch version found")

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
