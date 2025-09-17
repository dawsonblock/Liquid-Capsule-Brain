#!/usr/bin/env python3
"""Simple validation script to check if the build prerequisites are met."""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path


def check_file_syntax(filepath: str) -> tuple[bool, str | None]:
    """Check if a Python file has valid syntax."""

    try:
        source = Path(filepath).read_text(encoding="utf-8")
        ast.parse(source)
        return True, None
    except SyntaxError as exc:
        return False, str(exc)


def main() -> int:
    print("=== Liquid Capsule Brain Build Validation ===")

    # Check Python version
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 12):
        print("⚠️  Warning: Python 3.12+ recommended")
    else:
        print("✅ Python version OK")

    # Check critical files exist
    required_files = [
        ".env.example",
        ".env.reverse-proxy.example",
        "requirements.txt",
        "requirements-dev.txt",
        "launch_capsule_brain.py",
        "capsule_brain/api/server.py",
        "Dockerfile",
        "Makefile",
    ]

    missing_files: list[str] = []
    for filename in required_files:
        if os.path.exists(filename):
            print(f"✅ {filename} exists")
        else:
            print(f"❌ {filename} missing")
            missing_files.append(filename)

    # Check Python syntax
    python_files = [
        "launch_capsule_brain.py",
        "capsule_brain/api/server.py",
    ]

    syntax_errors: list[tuple[str, str]] = []
    for filepath in python_files:
        if os.path.exists(filepath):
            valid, error = check_file_syntax(filepath)
            if valid:
                print(f"✅ {filepath} syntax OK")
            else:
                print(f"❌ {filepath} syntax error: {error}")
                syntax_errors.append((filepath, error or ""))
        else:
            print(f"⚠️  {filepath} not found for syntax check")

    # Check .gitignore
    if os.path.exists(".gitignore"):
        gitignore_content = Path(".gitignore").read_text(encoding="utf-8")

        expected_entries = [".venv/", ".env"]
        missing_entries = [
            entry for entry in expected_entries if entry not in gitignore_content
        ]

        if missing_entries:
            print(f"⚠️  .gitignore missing entries: {missing_entries}")
        else:
            print("✅ .gitignore has required entries")

    # Check requirements.txt for Python 3.12 compatibility
    if os.path.exists("requirements.txt"):
        requirements = Path("requirements.txt").read_text(encoding="utf-8")

        # Check for problematic PyTorch version
        if "torch==2.1.0" in requirements:
            print("❌ torch==2.1.0 incompatible with Python 3.12+")
        elif "torch==" in requirements:
            print("✅ PyTorch version specified")
        else:
            print("⚠️  No PyTorch version found")

    # Summary
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
