"""Test configuration and fixtures for GUI testing."""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

# Set test environment variables
os.environ["APP_ENV"] = "test"
os.environ["ADMIN_TOKEN"] = "test-admin-token"
os.environ["DEEPSEEK_API_KEY"] = "test-api-key"


@pytest.fixture
def test_app():
    """Create a test FastAPI app with GUI components."""
    from capsule_brain.api.server import app
    
    # Mock the engine to avoid complex initialization
    mock_engine = MagicMock()
    mock_engine.start_time = 0
    mock_engine.memory = []
    mock_engine.knowledge_graph = MagicMock()
    mock_engine.knowledge_graph.nodes = []
    mock_engine.overseer_enabled = False
    mock_engine.is_shutting_down = False
    mock_engine.bus = AsyncMock()
    
    # Override the app state
    app.state.engine = mock_engine
    
    return app


@pytest.fixture
def client(test_app):
    """Create a test client with proper GUI setup."""
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def gui_security():
    """Create a fresh GUI security manager for testing."""
    from capsule_brain.gui.security import GUISecurityManager
    return GUISecurityManager()


@pytest.fixture
def gui_performance():
    """Create a fresh GUI performance manager for testing."""
    from capsule_brain.gui.performance import GUIPerformanceManager
    return GUIPerformanceManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.send_text = AsyncMock()
    return mock_ws


@pytest.fixture(autouse=True)
def cleanup_test_environment():
    """Clean up after each test."""
    yield
    # Clean up any test-specific state
    import capsule_brain.gui.security as gui_security_module
    import capsule_brain.gui.performance as gui_performance_module
    
    # Reset global instances
    gui_security_module.gui_security.blocked_ips.clear()
    gui_security_module.gui_security.rate_limits.clear()
    gui_performance_module.gui_performance.connected_clients.clear()
    gui_performance_module.gui_performance.message_stats.clear()
