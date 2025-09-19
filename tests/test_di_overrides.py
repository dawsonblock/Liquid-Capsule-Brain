from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from capsule_brain.api.dependencies import get_engine
from capsule_brain.api.server import app

ADMIN_HEADERS = {"x-admin-token": "test-admin-token"}


@pytest.fixture(autouse=True)
def _admin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN_HEADERS["x-admin-token"])
    monkeypatch.setenv("APP_ENV", "test")


@dataclass
class _StubBeliefManager:
    calls: int = 0

    def synthesize_context_for_llm(self) -> tuple[str, str]:
        self.calls += 1
        return ("stub-context", "stub-system")

    async def generate_llm_response(self) -> dict[str, Any]:
        return {}


class _StubGraph:
    def __init__(self) -> None:
        self._nodes: set[str] = set()
        self._edges = 0

    def number_of_nodes(self) -> int:
        return len(self._nodes)

    def number_of_edges(self) -> int:
        return self._edges

    def add_edge(self, source: str, target: str) -> None:
        self._nodes.update({source, target})
        self._edges += 1


class _StubEngine:
    def __init__(self) -> None:
        self.summary_payload = {"engine": "stubbed"}
        self.belief_state_manager = _StubBeliefManager()
        self.knowledge_graph = _StubGraph()
        self.memories: list[tuple[str, str]] = []

    def get_state_summary(self) -> dict[str, Any]:
        return self.summary_payload

    def add_memory(self, role: str, content: str) -> None:
        self.memories.append((role, content))

    def add_graph_edge(self, source: str, target: str, relation: str = "related_to") -> None:
        self.knowledge_graph.add_edge(source, target)


@pytest.fixture
def stub_engine() -> _StubEngine:
    return _StubEngine()


@pytest.fixture
def override_engine(stub_engine: _StubEngine) -> Generator[_StubEngine, None, None]:
    app.dependency_overrides[get_engine] = lambda: stub_engine
    yield stub_engine
    app.dependency_overrides.pop(get_engine, None)


@pytest.fixture
def client(override_engine: _StubEngine) -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


def test_engine_override_provides_custom_summary(
    client: TestClient, stub_engine: _StubEngine
) -> None:
    response = client.get("/state/summary", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json() == stub_engine.summary_payload


def test_engine_override_applies_to_ask_routes(
    client: TestClient, stub_engine: _StubEngine
) -> None:
    response = client.post("/ask", params={"q": "dependency injection"})
    assert response.status_code == 200
    assert stub_engine.memories == [("user", "dependency injection")]
    assert response.json()["context"] == "stub-context"
    assert response.json()["system"] == "stub-system"
    assert stub_engine.belief_state_manager.calls == 1
