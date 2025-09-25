"""Load testing configuration for Capsule Brain using Locust."""

import random

from locust import HttpUser, between, task


class CapsuleBrainUser(HttpUser):
    """Simulated user behavior for load testing."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self) -> None:
        """Called when a user starts."""
        self.admin_token = "test-admin-token"
        self.headers = {"x-admin-token": self.admin_token}

    @task(10)
    def health_check(self) -> None:
        """Check system health (most common operation)."""
        self.client.get("/healthz", headers=self.headers)

    @task(5)
    def debug_status(self) -> None:
        """Check debug status."""
        self.client.get("/debug/summary", headers=self.headers)

    @task(3)
    def performance_metrics(self) -> None:
        """Get performance metrics."""
        self.client.get("/debug/performance", headers=self.headers)

    @task(2)
    def memory_status(self) -> None:
        """Check memory status."""
        self.client.get("/debug/memory", headers=self.headers)

    @task(1)
    def upload_document(self) -> None:
        """Upload a test document."""
        # Create a small test file
        test_content = b"Test document content for load testing"
        files = {"file": ("test.txt", test_content, "text/plain")}
        data = {"q": "What is this document about?"}

        self.client.post("/ask_with_document", files=files, data=data)

    @task(1)
    def ask_question(self) -> None:
        """Ask a question to the system."""
        questions = [
            "What is the current system status?",
            "How is the performance?",
            "Are there any errors?",
            "What is the memory usage?",
            "Show me the debug information",
        ]

        question = random.choice(questions)
        self.client.post("/ask", json={"q": question})

    @task(1)
    def get_metrics(self) -> None:
        """Get Prometheus metrics."""
        self.client.get("/metrics")


class HighLoadUser(CapsuleBrainUser):
    """High-load user that performs more operations."""

    wait_time = between(0.5, 1.5)  # Faster operations

    @task(20)
    def rapid_health_checks(self) -> None:
        """Rapid health checks."""
        self.client.get("/healthz", headers=self.headers)

    @task(10)
    def debug_operations(self) -> None:
        """Various debug operations."""
        debug_endpoints = [
            "/debug/summary",
            "/debug/performance",
            "/debug/memory",
            "/debug/analysis",
        ]

        endpoint = random.choice(debug_endpoints)
        self.client.get(endpoint, headers=self.headers)
