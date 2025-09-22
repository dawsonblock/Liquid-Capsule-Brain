#!/usr/bin/env python3
"""Simple validation script to check if the build prerequisites are met."""

from __future__ import annotations

import ast
import sys
import tomllib
from collections.abc import Iterable
from pathlib import Path


def check_file_syntax(filepath: Path) -> tuple[bool, str | None]:
    """Check if a Python file has valid syntax."""

    try:
        source = filepath.read_text(encoding="utf-8")
    except OSError as exc:
        return False, str(exc)

    try:
        ast.parse(source)
        return True, None
    except SyntaxError as exc:  # pragma: no cover - utility script
        return False, str(exc)


def _print_status(prefix: str, message: str) -> None:
    print(f"{prefix} {message}")


def _check_required_files(paths: Iterable[Path]) -> list[Path]:
    missing: list[Path] = []
    for path in paths:
        if path.exists():
            _print_status("✅", f"{path} exists")
        else:
            _print_status("❌", f"{path} missing")
            missing.append(path)
    return missing


def _check_python_syntax(paths: Iterable[Path]) -> list[tuple[Path, str]]:
    syntax_errors: list[tuple[Path, str]] = []
    for path in paths:
        if not path.exists():
            _print_status("⚠️", f"{path} not found for syntax check")
            continue

        is_valid, error_message = check_file_syntax(path)
        if is_valid:
            _print_status("✅", f"{path} syntax OK")
        else:
            _print_status("❌", f"{path} syntax error: {error_message}")
            syntax_errors.append((path, error_message or "unknown error"))
    return syntax_errors


def _check_gitignore(path: Path) -> None:
    if not path.exists():
        return

    content = path.read_text(encoding="utf-8")
    expected_entries = [".venv/", ".env"]
    missing_entries = [entry for entry in expected_entries if entry not in content]

    if missing_entries:
        _print_status("⚠️", f".gitignore missing entries: {missing_entries}")
    else:
        _print_status("✅", ".gitignore has required entries")


def _check_python_version(pyproject_path: Path) -> bool:
    """Check if the current Python version meets the project's requirements."""
    if not pyproject_path.exists():
        _print_status("⚠️", f"{pyproject_path} not found, skipping Python version check.")
        return True  # Cannot check, so we don't fail

    if tomllib is None:
        _print_status(
            "⚠️", "tomli is not installed, skipping Python version check for older Python."
        )
        return True

    try:
        with pyproject_path.open("rb") as f:
            pyproject_data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        _print_status("❌", f"Error parsing {pyproject_path}: {exc}")
        return False

    requires_python = pyproject_data.get("project", {}).get("requires-python")
    if not requires_python:
        _print_status("⚠️", "No 'requires-python' found in pyproject.toml.")
        return True  # No requirement specified

    # Simple parsing for ">=MAJ.MIN" format
    try:
        spec = requires_python.strip().removeprefix(">=")
        req_major, req_minor = map(int, spec.split("."))
        current_major, current_minor = sys.version_info.major, sys.version_info.minor

        if (current_major, current_minor) >= (req_major, req_minor):
            _print_status(
                "✅",
                f"Python version {current_major}.{current_minor} meets requirement '{requires_python}'",
            )
            return True
        else:
            _print_status(
                "❌",
                f"Python version {current_major}.{current_minor} does not meet requirement '{requires_python}'",
            )
            return False
    except ValueError:
        _print_status(
            "⚠️", f"Could not parse 'requires-python' value: '{requires_python}'. Skipping check."
        )
        return True


def _check_requirements(path: Path) -> None:
    if not path.exists():
        return

    requirements = path.read_text(encoding="utf-8")
    if "torch==2.1.0" in requirements:
        _print_status("❌", "torch==2.1.0 incompatible with Python 3.12+")
    elif "torch==" in requirements:
        _print_status("✅", "PyTorch version specified")
    else:
        _print_status("⚠️", "No PyTorch version found")


def main() -> int:
    print("=== Liquid Capsule Brain Build Validation ===")
    print(f"Python version: {sys.version}")

    pyproject_path = Path("pyproject.toml")
    is_version_ok = _check_python_version(pyproject_path)

    required_files = [
        Path(".env.example"),
        Path(".env.reverse-proxy.example"),
        Path("requirements.txt"),
        Path("requirements-dev.txt"),
        Path("launch_capsule_brain.py"),
        Path("capsule_brain/api/server.py"),
        Path("Dockerfile"),
        Path("Makefile"),
        pyproject_path,
    ]
    missing_files = _check_required_files(required_files)

    capsule_brain_path = Path("capsule_brain")
    python_files = [
        Path("launch_capsule_brain.py"),
        Path(__file__),
    ]
    if capsule_brain_path.exists() and capsule_brain_path.is_dir():
        python_files.extend(capsule_brain_path.rglob("*.py"))

    syntax_errors = _check_python_syntax(python_files)

    _check_gitignore(Path(".gitignore"))
    _check_requirements(Path("requirements.txt"))

    print("\n=== Summary ===")
    if not is_version_ok:
        _print_status("❌", "Python version requirement not met.")
        return 1

    if missing_files:
        _print_status("❌", f"Missing files: {[str(f) for f in missing_files]}")
        return 1

    if syntax_errors:
        _print_status("❌", f"Syntax errors: {syntax_errors}")
        return 1

    _print_status("✅", "All build prerequisites are met!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and configure your settings")
    print("2. Run 'make dev-setup' to install dependencies")
    print("3. Run 'make dev' to start development server")
    print("4. Run 'make build' to build Docker image")
    return 0


if __name__ == "__main__":
    sys.exit(main())
