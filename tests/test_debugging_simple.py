"""Simple tests for debugging and enhancement systems without full app initialization."""

import os
import time
from unittest.mock import Mock, patch

import pytest

# Set environment variables to enable debugging
os.environ["DEBUG_MODE"] = "true"
os.environ["PROFILING_ENABLED"] = "true"
os.environ["MEMORY_DEBUG_ENABLED"] = "true"
os.environ["TRACEMALLOC_ENABLED"] = "true"
os.environ["PERFORMANCE_OPTIMIZATION_ENABLED"] = "true"
os.environ["SECURITY_ENHANCEMENT_ENABLED"] = "true"
os.environ["MONITORING_DASHBOARD_ENABLED"] = "true"

from capsule_brain.debugging.advanced_debugger import AdvancedDebugger, advanced_debugger
from capsule_brain.debugging.memory_debugger import MemoryDebugger, memory_debugger
from capsule_brain.debugging.profiler import AdvancedProfiler, advanced_profiler
from capsule_brain.debugging.static_analysis import StaticAnalyzer, static_analyzer
from capsule_brain.enhancements.monitoring_dashboard import MonitoringDashboard, monitoring_dashboard
from capsule_brain.enhancements.performance_optimizer import PerformanceOptimizer, performance_optimizer
from capsule_brain.enhancements.security_enhancer import SecurityEnhancer, security_enhancer


class TestAdvancedDebuggerSimple:
    """Test advanced debugging system without full app."""

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


class TestMemoryDebuggerSimple:
    """Test memory debugging system without full app."""

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


class TestAdvancedProfilerSimple:
    """Test advanced profiling system without full app."""

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


class TestPerformanceOptimizerSimple:
    """Test performance optimization system without full app."""

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
        # Clear cache before test
        performance_optimizer.cache.clear()
        
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

    def test_performance_summary(self) -> None:
        """Test performance summary generation."""
        summary = performance_optimizer.get_performance_summary()
        
        assert "optimization_enabled" in summary
        assert "cache_stats" in summary
        assert "performance_metrics" in summary
        assert "resource_health" in summary


class TestSecurityEnhancerSimple:
    """Test security enhancement system without full app."""

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

    def test_security_summary(self) -> None:
        """Test security summary generation."""
        summary = security_enhancer.get_security_summary()
        
        assert "security_enabled" in summary
        assert "threat_detection" in summary
        assert "total_security_events" in summary
        assert "recommendations" in summary


class TestMonitoringDashboardSimple:
    """Test monitoring dashboard system without full app."""

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


class TestIntegrationSimple:
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
        def test_integrated_function(x: int) -> int:
            with performance_optimizer.performance_monitor("test_operation"):
                return x * x
        
        result = test_integrated_function(5)
        assert result == 25
        
        # Both systems should have recorded the operation
        debug_summary = advanced_debugger.get_debug_summary()
        perf_summary = performance_optimizer.get_performance_summary()
        
        assert debug_summary["total_contexts"] > 0
        assert perf_summary["total_operations"] > 0
