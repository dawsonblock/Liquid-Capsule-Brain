"""Comprehensive tests for debugging and enhancement systems."""

import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from capsule_brain.api.server import app
from capsule_brain.debugging.advanced_debugger import advanced_debugger
from capsule_brain.debugging.memory_debugger import memory_debugger
from capsule_brain.debugging.profiler import advanced_profiler
from capsule_brain.debugging.static_analysis import static_analyzer
from capsule_brain.enhancements.monitoring_dashboard import monitoring_dashboard
from capsule_brain.enhancements.performance_optimizer import performance_optimizer
from capsule_brain.enhancements.security_enhancer import security_enhancer


class TestAdvancedDebugger:
    """Test advanced debugging system."""

    def test_debug_context(self) -> None:
        """Test debug context manager."""
        with advanced_debugger.debug_context("test_operation") as context:
            assert context.request_id is not None
            assert context.start_time > 0
            assert context.memory_before is not None
        
        # Check that context was recorded
        assert len(advanced_debugger.context_history) > 0

    def test_debug_function_decorator(self) -> None:
        """Test debug function decorator."""
        @advanced_debugger.debug_function
        def test_function(x: int, y: int) -> int:
            return x + y
        
        result = test_function(2, 3)
        assert result == 5
        
        # Check that function was debugged
        assert len(advanced_debugger.context_history) > 0

    def test_debug_summary(self) -> None:
        """Test debug summary generation."""
        summary = advanced_debugger.get_debug_summary()
        
        assert "debug_enabled" in summary
        assert "total_contexts" in summary
        assert "performance_stats" in summary

    def test_performance_report(self) -> None:
        """Test performance report generation."""
        report = advanced_debugger.get_performance_report()
        
        assert "performance_analysis" in report
        assert "system_metrics" in report
        assert "recommendations" in report


class TestMemoryDebugger:
    """Test memory debugging system."""

    def test_memory_snapshot(self) -> None:
        """Test memory snapshot functionality."""
        snapshot = memory_debugger.take_snapshot("test_snapshot")
        
        assert snapshot is not None
        assert snapshot.memory_usage > 0
        assert snapshot.objects_count > 0
        assert snapshot.timestamp > 0

    def test_memory_summary(self) -> None:
        """Test memory summary generation."""
        summary = memory_debugger.get_memory_summary()
        
        assert "debug_enabled" in summary
        assert "current_memory" in summary
        assert "statistics" in summary
        assert "gc_info" in summary

    def test_garbage_collection(self) -> None:
        """Test garbage collection functionality."""
        gc_stats = memory_debugger.force_garbage_collection()
        
        assert "objects_collected" in gc_stats
        assert "memory_freed_bytes" in gc_stats
        assert "objects_freed" in gc_stats

    def test_memory_leaks_report(self) -> None:
        """Test memory leaks report generation."""
        report = memory_debugger.get_memory_leaks_report()
        
        assert "leak_analysis" in report
        assert "recommendations" in report
        assert "summary" in report


class TestAdvancedProfiler:
    """Test advanced profiling system."""

    def test_profile_function_decorator(self) -> None:
        """Test profile function decorator."""
        @advanced_profiler.profile_decorator
        def test_function(x: int) -> int:
            time.sleep(0.01)  # Small delay for profiling
            return x * 2
        
        result = test_function(5)
        assert result == 10
        
        # Check that function was profiled
        summary = advanced_profiler.get_profile_summary()
        assert summary["total_functions_profiled"] > 0

    def test_profile_summary(self) -> None:
        """Test profile summary generation."""
        summary = advanced_profiler.get_profile_summary()
        
        assert "profiling_enabled" in summary
        assert "total_functions_profiled" in summary
        assert "current_memory_usage_mb" in summary

    def test_detailed_profile_report(self) -> None:
        """Test detailed profile report generation."""
        report = advanced_profiler.get_detailed_profile_report()
        
        assert "function_analysis" in report
        assert "system_metrics" in report
        assert "recommendations" in report


class TestStaticAnalyzer:
    """Test static analysis system."""

    def test_analysis_summary(self) -> None:
        """Test analysis summary generation."""
        summary = static_analyzer.get_analysis_summary()
        
        assert "analysis_enabled" in summary
        assert "total_issues" in summary
        assert "tools_enabled" in summary

    def test_detailed_report(self) -> None:
        """Test detailed analysis report generation."""
        report = static_analyzer.get_detailed_report()
        
        assert "summary" in report
        assert "security_issues" in report
        assert "code_issues" in report
        assert "recommendations" in report


class TestPerformanceOptimizer:
    """Test performance optimization system."""

    def test_cache_functionality(self) -> None:
        """Test cache functionality."""
        # Test cache set/get
        performance_optimizer.cache.set("test_key", "test_value", 60)
        value = performance_optimizer.cache.get("test_key")
        assert value == "test_value"
        
        # Test cache hit rate
        hit_rate = performance_optimizer.cache.get_hit_rate()
        assert hit_rate >= 0.0

    def test_cache_decorator(self) -> None:
        """Test cache decorator."""
        call_count = 0
        
        @performance_optimizer.cache_decorator(ttl=60)
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * x
        
        # First call should execute function
        result1 = expensive_function(5)
        assert result1 == 25
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 25
        assert call_count == 1  # Should not increment

    def test_performance_monitor(self) -> None:
        """Test performance monitoring."""
        with performance_optimizer.performance_monitor("test_operation") as context:
            time.sleep(0.01)  # Small delay
        
        # Check that performance was monitored
        summary = performance_optimizer.get_performance_summary()
        assert summary["total_operations"] > 0

    def test_performance_summary(self) -> None:
        """Test performance summary generation."""
        summary = performance_optimizer.get_performance_summary()
        
        assert "optimization_enabled" in summary
        assert "cache_stats" in summary
        assert "performance_metrics" in summary
        assert "resource_health" in summary

    def test_optimization_recommendations(self) -> None:
        """Test optimization recommendations."""
        recommendations = performance_optimizer.get_optimization_recommendations()
        
        assert isinstance(recommendations, list)
        # Recommendations should be strings
        for rec in recommendations:
            assert isinstance(rec, str)

    def test_cache_optimization(self) -> None:
        """Test cache optimization."""
        optimization_result = performance_optimizer.optimize_cache()
        
        assert "cache_size_before" in optimization_result
        assert "hit_rate_before" in optimization_result
        assert "optimizations_applied" in optimization_result


class TestSecurityEnhancer:
    """Test security enhancement system."""

    def test_threat_detection(self) -> None:
        """Test threat detection."""
        request_data = {
            "path": "/test",
            "query_string": "id=1' OR '1'='1",  # SQL injection attempt
            "source_ip": "192.168.1.1",
            "headers": {"user-agent": "test-agent"}
        }
        
        analysis = security_enhancer.analyze_request(request_data)
        
        assert "threats_detected" in analysis
        assert "security_score" in analysis
        assert "recommendations" in analysis

    def test_input_sanitization(self) -> None:
        """Test input sanitization."""
        malicious_input = "<script>alert('xss')</script>"
        sanitized = security_enhancer.sanitize_input(malicious_input)
        
        assert "<script>" not in sanitized
        assert "alert" in sanitized  # Content should be preserved but sanitized

    def test_csrf_token_generation(self) -> None:
        """Test CSRF token generation and validation."""
        session_id = "test_session_123"
        token = security_enhancer.generate_csrf_token(session_id)
        
        assert token is not None
        assert ":" in token  # Should contain timestamp separator
        
        # Test validation
        is_valid = security_enhancer.validate_csrf_token(token, session_id)
        assert is_valid is True
        
        # Test with wrong session ID
        is_invalid = security_enhancer.validate_csrf_token(token, "wrong_session")
        assert is_invalid is False

    def test_security_headers(self) -> None:
        """Test security headers generation."""
        headers = security_enhancer.get_security_headers()
        
        assert "Strict-Transport-Security" in headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "Content-Security-Policy" in headers

    def test_security_summary(self) -> None:
        """Test security summary generation."""
        summary = security_enhancer.get_security_summary()
        
        assert "security_enabled" in summary
        assert "threat_detection" in summary
        assert "total_security_events" in summary
        assert "recommendations" in summary


class TestMonitoringDashboard:
    """Test monitoring dashboard system."""

    @pytest.mark.asyncio
    async def test_dashboard_start_stop(self) -> None:
        """Test dashboard start/stop functionality."""
        # Start collection
        await monitoring_dashboard.start_collection()
        assert monitoring_dashboard.collection_task is not None
        
        # Wait a bit for collection
        await asyncio.sleep(0.1)
        
        # Stop collection
        await monitoring_dashboard.stop_collection()
        assert monitoring_dashboard.collection_task is None

    def test_dashboard_data(self) -> None:
        """Test dashboard data generation."""
        data = monitoring_dashboard.get_dashboard_data()
        
        assert "dashboard_enabled" in data
        assert "timestamp" in data
        assert "current_metrics" in data
        assert "active_alerts" in data
        assert "alert_summary" in data

    def test_health_status(self) -> None:
        """Test health status generation."""
        health = monitoring_dashboard.get_health_status()
        
        assert "status" in health
        assert "issues" in health
        assert "timestamp" in health
        assert "metrics_count" in health

    def test_metric_history(self) -> None:
        """Test metric history retrieval."""
        # This will be empty initially, but should not crash
        history = monitoring_dashboard.get_metric_history("cpu.usage", 10)
        
        assert isinstance(history, list)
        # Each item should have timestamp, value, unit
        for item in history:
            assert "timestamp" in item
            assert "value" in item
            assert "unit" in item


class TestDebuggingEndpoints:
    """Test debugging API endpoints."""

    def test_debug_summary_endpoint(self, client: TestClient) -> None:
        """Test debug summary endpoint."""
        headers = {"x-admin-token": "test-token"}
        response = client.get("/debug/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "advanced_debugger" in data
        assert "memory_debugger" in data
        assert "profiler" in data
        assert "static_analyzer" in data

    def test_debug_memory_endpoint(self, client: TestClient) -> None:
        """Test debug memory endpoint."""
        headers = {"x-admin-token": "test-token"}
        response = client.get("/debug/memory", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "debug_enabled" in data
        assert "current_memory" in data
        assert "statistics" in data

    def test_debug_performance_endpoint(self, client: TestClient) -> None:
        """Test debug performance endpoint."""
        headers = {"x-admin-token": "test-token"}
        response = client.get("/debug/performance", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "function_analysis" in data
        assert "system_metrics" in data
        assert "recommendations" in data

    def test_debug_gc_endpoint(self, client: TestClient) -> None:
        """Test debug garbage collection endpoint."""
        headers = {"x-admin-token": "test-token"}
        response = client.post("/debug/gc", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "objects_collected" in data
        assert "memory_freed_bytes" in data
        assert "objects_freed" in data

    def test_debug_snapshot_endpoint(self, client: TestClient) -> None:
        """Test debug snapshot endpoint."""
        headers = {"x-admin-token": "test-token"}
        response = client.post("/debug/snapshot?label=test", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["snapshot_taken"] is True
        assert data["label"] == "test"
        assert "timestamp" in data
        assert "memory_usage_mb" in data
        assert "objects_count" in data


class TestEnhancementEndpoints:
    """Test enhancement API endpoints."""

    def test_enhancements_summary_endpoint(self, client: TestClient) -> None:
        """Test enhancements summary endpoint."""
        headers = {"x-admin-token": "test-token"}
        response = client.get("/enhancements/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "performance_optimizer" in data
        assert "security_enhancer" in data
        assert "monitoring_dashboard" in data

    def test_enhancements_performance_endpoint(self, client: TestClient) -> None:
        """Test enhancements performance endpoint."""
        headers = {"x-admin-token": "test-token"}
        response = client.get("/enhancements/performance", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "optimization_enabled" in data
        assert "cache_stats" in data
        assert "performance_metrics" in data

    def test_enhancements_security_endpoint(self, client: TestClient) -> None:
        """Test enhancements security endpoint."""
        headers = {"x-admin-token": "test-token"}
        response = client.get("/enhancements/security", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "security_enabled" in data
        assert "threat_detection" in data
        assert "total_security_events" in data

    def test_enhancements_monitoring_endpoint(self, client: TestClient) -> None:
        """Test enhancements monitoring endpoint."""
        headers = {"x-admin-token": "test-token"}
        response = client.get("/enhancements/monitoring", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "dashboard_enabled" in data
        assert "current_metrics" in data
        assert "active_alerts" in data

    def test_enhancements_health_endpoint(self, client: TestClient) -> None:
        """Test enhancements health endpoint."""
        headers = {"x-admin-token": "test-token"}
        response = client.get("/enhancements/health", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "issues" in data
        assert "timestamp" in data

    def test_optimize_cache_endpoint(self, client: TestClient) -> None:
        """Test optimize cache endpoint."""
        headers = {"x-admin-token": "test-token"}
        response = client.post("/enhancements/optimize-cache", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cache_size_before" in data
        assert "hit_rate_before" in data
        assert "optimizations_applied" in data

    def test_analyze_security_endpoint(self, client: TestClient) -> None:
        """Test analyze security endpoint."""
        headers = {"x-admin-token": "test-token"}
        response = client.post("/enhancements/analyze-security", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "threats_detected" in data
        assert "security_score" in data
        assert "recommendations" in data


class TestIntegration:
    """Test integration between debugging and enhancement systems."""

    def test_system_integration(self) -> None:
        """Test that all systems work together."""
        # Test that all systems are initialized
        assert advanced_debugger is not None
        assert memory_debugger is not None
        assert advanced_profiler is not None
        assert static_analyzer is not None
        assert performance_optimizer is not None
        assert security_enhancer is not None
        assert monitoring_dashboard is not None

    def test_performance_with_debugging(self) -> None:
        """Test performance optimization with debugging enabled."""
        @advanced_debugger.debug_function
        @performance_optimizer.cache_decorator(ttl=60)
        def test_integrated_function(x: int) -> int:
            return x * x
        
        result = test_integrated_function(5)
        assert result == 25
        
        # Both systems should have recorded the operation
        debug_summary = advanced_debugger.get_debug_summary()
        perf_summary = performance_optimizer.get_performance_summary()
        
        assert debug_summary["total_contexts"] > 0
        assert perf_summary["total_operations"] > 0

    def test_security_with_monitoring(self) -> None:
        """Test security enhancement with monitoring."""
        # Simulate a suspicious request
        request_data = {
            "path": "/admin",
            "query_string": "cmd=rm -rf /",
            "source_ip": "192.168.1.100",
            "headers": {"user-agent": "suspicious-agent"}
        }
        
        # Analyze security
        security_analysis = security_enhancer.analyze_request(request_data)
        
        # Check monitoring
        health_status = monitoring_dashboard.get_health_status()
        
        assert "threats_detected" in security_analysis
        assert "status" in health_status
