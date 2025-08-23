#!/usr/bin/env python3
"""
Simple validation script to check if the build prerequisites are met.
"""

import ast
import os
import sys


def check_file_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath) as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, str(e)


def main():
    print("=== Liquid Capsule Brain Build Validation ===")

    # Check Python version
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 11):
        print("⚠️  Warning: Python 3.11+ recommended")
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

    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            missing_files.append(file)

    # Check Python syntax
    python_files = [
        "launch_capsule_brain.py",
        "capsule_brain/api/server.py",
    ]

    syntax_errors = []
    for file in python_files:
        if os.path.exists(file):
            valid, error = check_file_syntax(file)
            if valid:
                print(f"✅ {file} syntax OK")
            else:
                print(f"❌ {file} syntax error: {error}")
                syntax_errors.append((file, error))
        else:
            print(f"⚠️  {file} not found for syntax check")

    # Check .gitignore
    if os.path.exists(".gitignore"):
        with open(".gitignore") as f:
            gitignore_content = f.read()

        expected_entries = [".venv/", ".env"]
        missing_entries = []
        for entry in expected_entries:
            if entry not in gitignore_content:
                missing_entries.append(entry)

        if missing_entries:
            print(f"⚠️  .gitignore missing entries: {missing_entries}")
        else:
            print("✅ .gitignore has required entries")

    # Check requirements.txt for Python 3.12 compatibility
    if os.path.exists("requirements.txt"):
        with open("requirements.txt") as f:
            requirements = f.read()

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
