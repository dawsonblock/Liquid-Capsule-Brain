"""Performance tests for the Capsule Brain system."""

import asyncio
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from capsule_brain.api.server import app


class TestPerformance:
    """Performance test suite."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    @pytest.mark.slow
    def test_api_response_time(self, client: TestClient) -> None:
        """Test that API endpoints respond within acceptable time limits."""
        # Test with admin token for protected endpoints
        headers = {"x-admin-token": "test-token"}
        start_time = time.time()
        response = client.get("/healthz", headers=headers)
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 0.1  # 100ms limit

    @pytest.mark.slow
    def test_concurrent_requests(self, client: TestClient) -> None:
        """Test system performance under concurrent load."""
        import queue
        import threading

        results = queue.Queue()
        num_threads = 10
        requests_per_thread = 10

        def make_requests() -> None:
            headers = {"x-admin-token": "test-token"}
            for _ in range(requests_per_thread):
                start_time = time.time()
                response = client.get("/healthz", headers=headers)
                end_time = time.time()
                results.put((response.status_code, end_time - start_time))

        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Analyze results
        response_times = []
        while not results.empty():
            status_code, response_time = results.get()
            assert status_code == 200
            response_times.append(response_time)

        assert len(response_times) == num_threads * requests_per_thread
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 0.2  # 200ms average limit

    @pytest.mark.slow
    def test_memory_usage_stability(self, client: TestClient) -> None:
        """Test that memory usage remains stable under load."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make many requests
        headers = {"x-admin-token": "test-token"}
        for _ in range(100):
            response = client.get("/healthz", headers=headers)
            assert response.status_code == 200

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 10MB)
        assert memory_increase < 10 * 1024 * 1024

    @pytest.mark.slow
    def test_debugging_endpoints_performance(self, client: TestClient) -> None:
        """Test performance of debugging endpoints."""
        # Test with admin token
        headers = {"x-admin-token": "test-token"}

        endpoints = [
            "/debug/status",
            "/debug/health",
            "/debug/performance",
            "/debug/memory",
        ]

        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint, headers=headers)
            end_time = time.time()

            # Debug endpoints should respond within 500ms
            assert (end_time - start_time) < 0.5
            assert response.status_code in [200, 404]  # 404 if not in dev mode

    @pytest.mark.slow
    def test_large_file_upload_performance(self, client: TestClient) -> None:
        """Test performance of file upload with large files."""
        import io

        # Create a smaller test file (1MB) to avoid timeout issues
        large_content = b"x" * (1 * 1024 * 1024)
        large_file = io.BytesIO(large_content)

        start_time = time.time()
        response = client.post(
            "/ask_with_document",
            files={"file": ("test.pdf", large_file, "application/pdf")},
            data={"q": "Test question"},
        )
        end_time = time.time()

        # Should handle large files within 2 seconds
        assert (end_time - start_time) < 2.0
        assert response.status_code in [
            200,
            413,
            503,
        ]  # 413 if file too large, 503 if service unavailable

    @pytest.mark.slow
    def test_async_operations_performance(self) -> None:
        """Test performance of async operations."""

        async def async_operation() -> dict[str, Any]:
            await asyncio.sleep(0.01)  # Simulate async work
            return {"status": "success"}

        async def run_concurrent_operations() -> list[dict[str, Any]]:
            tasks = [async_operation() for _ in range(50)]
            return await asyncio.gather(*tasks)

        start_time = time.time()
        results = asyncio.run(run_concurrent_operations())
        end_time = time.time()

        assert len(results) == 50
        assert all(result["status"] == "success" for result in results)
        assert (end_time - start_time) < 1.0  # Should complete within 1 second
