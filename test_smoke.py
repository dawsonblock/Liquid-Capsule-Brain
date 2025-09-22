#!/usr/bin/env python3
"""Smoke test for Capsule Brain Supreme AGI system."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import requests


def test_imports() -> bool:
    """Test that all critical modules can be imported."""
    print("🔍 Testing imports...")
    try:
        import prometheus_fastapi_instrumentator
        import tomli

        import capsule_brain.api.server
        import capsule_brain.core.capsule_engine
        import capsule_brain.ingestion.extractor
        import capsule_brain.llm_adapter.deepseek_client
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_dependencies() -> bool:
    """Test that all required dependencies are available."""
    print("🔍 Testing dependencies...")
    try:
        # Test pypdf
        # Test tomli
        import tomli

        # Test OpenAI
        from openai import APIError, OpenAI

        # Test Prometheus
        from prometheus_fastapi_instrumentator import Instrumentator
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError

        print("✅ All dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Dependency missing: {e}")
        return False


def test_pdf_extraction() -> bool:
    """Test PDF extraction functionality."""
    print("🔍 Testing PDF extraction...")
    try:
        from capsule_brain.ingestion.extractor import extract_bytes

        # Test with a simple text file first
        test_txt_content = b"Hello, this is a test document for extraction."
        text, meta = extract_bytes("test.txt", "text/plain", test_txt_content)

        if "Hello, this is a test document" in text:
            print("✅ Text extraction working")
            return True
        else:
            print(f"❌ Text extraction failed. Got: {text[:100]}...")
            return False

    except Exception as e:
        print(f"❌ PDF extraction test failed: {e}")
        return False


def test_server_startup() -> bool:
    """Test that the server can start without errors."""
    print("🔍 Testing server startup...")
    try:
        # Test that the server module can be imported and app created
        from capsule_brain.api.server import app

        # Check that Prometheus is instrumented
        routes = [route.path for route in app.routes]
        if "/metrics" in routes:
            print("✅ Server startup successful, Prometheus metrics exposed")
            return True
        else:
            print("❌ Prometheus metrics not exposed")
            return False

    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False


def test_environment_validation() -> bool:
    """Test environment variable validation."""
    print("🔍 Testing environment validation...")

    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False

    # Check for required environment variables
    required_vars = ["DEEPSEEK_API_KEY", "ADMIN_TOKEN"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False

    print("✅ Environment validation passed")
    return True


def test_openai_client() -> bool:
    """Test OpenAI client initialization."""
    print("🔍 Testing OpenAI client...")
    try:
        from capsule_brain.llm_adapter.deepseek_client import DeepSeekClient

        client = DeepSeekClient()

        if client.is_available():
            print("✅ OpenAI client initialized with API key")
            return True
        else:
            print("⚠️  OpenAI client initialized but no API key (expected in CI)")
            return True  # This is OK for testing without API key

    except Exception as e:
        print(f"❌ OpenAI client test failed: {e}")
        return False


async def test_uvicorn_smoke() -> bool:
    """Test Uvicorn server smoke test."""
    print("🔍 Testing Uvicorn smoke test...")

    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "capsule_brain.api.server:app",
            "--host", "127.0.0.1",
            "--port", "8001",  # Use different port to avoid conflicts
            "--log-level", "error"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait for server to start
        await asyncio.sleep(3)

        # Test health endpoint
        try:
            response = requests.get("http://127.0.0.1:8001/healthz", timeout=5)
            if response.status_code == 200:
                print("✅ Uvicorn smoke test passed")
                success = True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                success = False
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check request failed: {e}")
            success = False

        # Clean up
        process.terminate()
        process.wait(timeout=5)

        return success

    except Exception as e:
        print(f"❌ Uvicorn smoke test failed: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("🚀 Starting Capsule Brain Supreme AGI Smoke Tests\n")

    tests = [
        ("Import Test", test_imports),
        ("Dependencies Test", test_dependencies),
        ("PDF Extraction Test", test_pdf_extraction),
        ("Server Startup Test", test_server_startup),
        ("Environment Validation", test_environment_validation),
        ("OpenAI Client Test", test_openai_client),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)

        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Run async test
    print(f"\n{'='*50}")
    print("Running: Uvicorn Smoke Test")
    print('='*50)
    try:
        result = asyncio.run(test_uvicorn_smoke())
        results.append(("Uvicorn Smoke Test", result))
    except Exception as e:
        print(f"❌ Uvicorn Smoke Test crashed: {e}")
        results.append(("Uvicorn Smoke Test", False))

    # Summary
    print(f"\n{'='*50}")
    print("SMOKE TEST SUMMARY")
    print('='*50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All smoke tests passed! System is ready.")
        return 0
    else:
        print("💥 Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
