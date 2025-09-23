"""Simplified GUI tests that focus on core functionality."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path

from capsule_brain.gui.security import GUISecurityManager
from capsule_brain.gui.performance import GUIPerformanceManager


class TestGUISecuritySimple:
    """Test GUI security features with isolated components."""

    def test_file_upload_validation(self) -> None:
        """Test file upload validation."""
        security = GUISecurityManager()
        
        # Valid file
        security.validate_file_upload("test.pdf", 1024)
        
        # Invalid extension
        with pytest.raises(Exception):  # HTTPException
            security.validate_file_upload("test.exe", 1024)
        
        # File too large
        with pytest.raises(Exception):  # HTTPException
            security.validate_file_upload("test.pdf", 11 * 1024 * 1024)
        
        # Dangerous filename
        with pytest.raises(Exception):  # HTTPException
            security.validate_file_upload("../../../etc/passwd", 1024)

    def test_input_sanitization(self) -> None:
        """Test input sanitization."""
        security = GUISecurityManager()
        
        # HTML tags
        sanitized = security.sanitize_user_input("<script>alert('xss')</script>")
        assert "<script>" not in sanitized
        assert "alert" in sanitized
        
        # Special characters
        sanitized = security.sanitize_user_input("Test & < > \" '")
        assert "&amp;" in sanitized
        assert "&lt;" in sanitized or "<" not in sanitized
        assert "&gt;" in sanitized or ">" not in sanitized
        
        # Length limit
        long_input = "x" * 5000
        sanitized = security.sanitize_user_input(long_input)
        assert len(sanitized) <= 4003  # 4000 + "..."

    def test_websocket_message_validation(self) -> None:
        """Test WebSocket message validation."""
        security = GUISecurityManager()
        
        # Valid message
        assert security.validate_websocket_message("Hello world")
        
        # Script tag
        assert not security.validate_websocket_message("<script>alert('xss')</script>")
        
        # JavaScript URL
        assert not security.validate_websocket_message("javascript:alert('xss')")
        
        # Too long
        long_message = "x" * 10001
        assert not security.validate_websocket_message(long_message)

    def test_rate_limiting(self) -> None:
        """Test rate limiting functionality."""
        security = GUISecurityManager()
        client_ip = "192.168.1.1"
        
        # Should allow requests within limit
        for _ in range(60):
            assert security.check_rate_limit(client_ip)
        
        # Should block after limit
        assert not security.check_rate_limit(client_ip)

    def test_ip_blocking(self) -> None:
        """Test IP blocking functionality."""
        security = GUISecurityManager()
        client_ip = "192.168.1.100"
        
        # Initially not blocked
        assert not security.is_ip_blocked(client_ip)
        
        # Block IP
        security.block_ip(client_ip)
        assert security.is_ip_blocked(client_ip)


class TestGUIPerformanceSimple:
    """Test GUI performance features with isolated components."""

    @pytest.mark.asyncio
    async def test_message_queue(self) -> None:
        """Test message queue functionality."""
        performance = GUIPerformanceManager()
        
        # Add message
        success = await performance.add_message({"type": "test", "data": "hello"})
        assert success
        
        # Add broadcast
        success = await performance.add_broadcast({"type": "broadcast", "data": "world"})
        assert success

    def test_performance_stats(self) -> None:
        """Test performance statistics."""
        performance = GUIPerformanceManager()
        stats = performance.get_performance_stats()
        
        assert "performance_metrics" in stats
        assert "message_stats" in stats
        assert "connected_clients" in stats
        assert "queue_sizes" in stats

    def test_mobile_optimization(self) -> None:
        """Test mobile optimization detection."""
        performance = GUIPerformanceManager()
        
        # Mobile user agent
        mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
        mobile_opts = performance.optimize_for_mobile(mobile_ua)
        assert mobile_opts["reduced_animations"] is True
        assert mobile_opts["touch_optimized"] is True
        
        # Desktop user agent
        desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        desktop_opts = performance.optimize_for_mobile(desktop_ua)
        assert desktop_opts["reduced_animations"] is False
        assert desktop_opts["touch_optimized"] is False


class TestGUIStaticFiles:
    """Test static file serving."""

    def test_static_files_exist(self) -> None:
        """Test that static files exist."""
        static_path = Path(__file__).parent.parent / "capsule_brain" / "gui" / "static"
        
        # Check main files
        assert (static_path / "index.html").exists()
        assert (static_path / "app.js").exists()
        assert (static_path / "styles.css").exists()
        
        # Check mobile files
        mobile_path = static_path / "mobile"
        assert mobile_path.exists()
        assert (mobile_path / "index.html").exists()
        assert (mobile_path / "app.js").exists()
        assert (mobile_path / "styles.css").exists()

    def test_static_file_content(self) -> None:
        """Test static file content."""
        static_path = Path(__file__).parent.parent / "capsule_brain" / "gui" / "static"
        
        # Check HTML content
        html_content = (static_path / "index.html").read_text()
        assert "Capsule Brain" in html_content
        assert "DOCTYPE html" in html_content
        
        # Check CSS content
        css_content = (static_path / "styles.css").read_text()
        assert "body" in css_content or ".app-container" in css_content
        
        # Check JS content
        js_content = (static_path / "app.js").read_text()
        assert "CapsuleBrainApp" in js_content or "class" in js_content


class TestGUIMinimalApp:
    """Test GUI with minimal FastAPI app."""

    def test_minimal_gui_app(self) -> None:
        """Test GUI with a minimal FastAPI app."""
        app = FastAPI()
        
        # Add basic static file serving
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        
        static_path = Path(__file__).parent.parent / "capsule_brain" / "gui" / "static"
        
        # Mount static files
        app.mount("/static", StaticFiles(directory=static_path), name="static")
        
        # Add root route
        @app.get("/")
        async def root():
            return FileResponse(static_path / "index.html")
        
        # Test the app
        with TestClient(app) as client:
            # Test root route
            response = client.get("/")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            assert "Capsule Brain" in response.text
            
            # Test static files
            response = client.get("/static/styles.css")
            assert response.status_code == 200
            assert "text/css" in response.headers["content-type"]
            
            response = client.get("/static/app.js")
            assert response.status_code == 200
            assert "javascript" in response.headers["content-type"]

    def test_gui_deployment_info(self) -> None:
        """Test GUI deployment information."""
        from capsule_brain.gui.deployment import GUIDeploymentManager
        
        app = FastAPI()
        manager = GUIDeploymentManager(app)
        
        # Test deployment info
        info = manager.get_deployment_summary()
        assert "environment" in info
        assert "features_enabled" in info
        assert "configuration" in info
        
        # Test validation
        validation = manager.validate_deployment()
        assert "valid" in validation
        assert "checks" in validation
        
        # Test environment config
        config = manager.get_environment_config()
        assert "environment" in config
        assert "features" in config
