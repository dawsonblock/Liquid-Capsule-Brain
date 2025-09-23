"""Advanced debugging infrastructure for comprehensive application monitoring."""

import asyncio
import functools
import inspect
import logging
import os
import sys
import time
import traceback
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

import psutil
from fastapi import Request, Response

log = logging.getLogger(__name__)


@dataclass
class DebugContext:
    """Context for debugging information."""
    request_id: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_before: Optional[int] = None
    memory_after: Optional[int] = None
    cpu_before: Optional[float] = None
    cpu_after: Optional[float] = None
    stack_trace: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class AdvancedDebugger:
    """Advanced debugging system with comprehensive monitoring capabilities."""

    def __init__(self) -> None:
        """Initialize the advanced debugger."""
        self.active_contexts: Dict[str, DebugContext] = {}
        self.context_history: deque = deque(maxlen=1000)
        self.performance_data: Dict[str, List[float]] = defaultdict(list)
        self.error_patterns: Dict[str, int] = defaultdict(int)
        self.memory_leaks: Set[str] = set()
        self.slow_operations: Dict[str, float] = {}
        self.debug_enabled = os.getenv("DEBUG_MODE", "false").lower() == "true"
        self.profiling_enabled = os.getenv("PROFILING_ENABLED", "false").lower() == "true"
        
        # Performance thresholds
        self.slow_threshold = float(os.getenv("SLOW_OPERATION_THRESHOLD", "1.0"))
        self.memory_threshold = int(os.getenv("MEMORY_THRESHOLD_MB", "100")) * 1024 * 1024
        
        log.info("Advanced Debugger initialized")

    @contextmanager
    def debug_context(self, operation_name: str, request_id: str = None):
        """Context manager for debugging operations."""
        if not self.debug_enabled:
            yield
            return

        context_id = request_id or f"{operation_name}_{int(time.time() * 1000)}"
        
        # Capture initial state
        context = DebugContext(
            request_id=context_id,
            start_time=time.time(),
            memory_before=self._get_memory_usage(),
            cpu_before=self._get_cpu_usage()
        )
        
        self.active_contexts[context_id] = context
        
        try:
            yield context
        except Exception as e:
            context.errors.append(str(e))
            context.stack_trace = traceback.format_exc()
            self._record_error_pattern(str(e))
            raise
        finally:
            # Capture final state
            context.end_time = time.time()
            context.duration = context.end_time - context.start_time
            context.memory_after = self._get_memory_usage()
            context.cpu_after = self._get_cpu_usage()
            
            # Record performance metrics
            self._record_performance_metrics(context)
            
            # Check for issues
            self._check_performance_issues(context)
            self._check_memory_issues(context)
            
            # Store in history
            self.context_history.append(context)
            
            # Clean up
            del self.active_contexts[context_id]

    def debug_function(self, func: Callable) -> Callable:
        """Decorator for debugging function execution."""
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not self.debug_enabled:
                return await func(*args, **kwargs)
            
            operation_name = f"{func.__module__}.{func.__name__}"
            
            with self.debug_context(operation_name) as context:
                # Capture function arguments
                context.variables["args"] = str(args)[:500]  # Truncate for storage
                context.variables["kwargs"] = str(kwargs)[:500]
                
                # Execute function
                start_time = time.time()
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Record execution time
                context.performance_metrics["execution_time"] = execution_time
                
                return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not self.debug_enabled:
                return func(*args, **kwargs)
            
            operation_name = f"{func.__module__}.{func.__name__}"
            
            with self.debug_context(operation_name) as context:
                # Capture function arguments
                context.variables["args"] = str(args)[:500]
                context.variables["kwargs"] = str(kwargs)[:500]
                
                # Execute function
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Record execution time
                context.performance_metrics["execution_time"] = execution_time
                
                return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    def debug_request(self, request: Request, response: Response) -> None:
        """Debug HTTP request/response cycle."""
        if not self.debug_enabled:
            return
        
        operation_name = f"HTTP_{request.method}_{request.url.path}"
        
        with self.debug_context(operation_name) as context:
            # Capture request details
            context.variables.update({
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "response_status": response.status_code,
                "response_headers": dict(response.headers)
            })
            
            # Check for performance issues
            if context.duration and context.duration > self.slow_threshold:
                self.slow_operations[operation_name] = context.duration
                context.warnings.append(f"Slow operation: {context.duration:.2f}s")

    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            process = psutil.Process()
            return process.memory_info().rss
        except Exception:
            return 0

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            process = psutil.Process()
            return process.cpu_percent()
        except Exception:
            return 0.0

    def _record_performance_metrics(self, context: DebugContext) -> None:
        """Record performance metrics for analysis."""
        if context.duration:
            self.performance_data[context.request_id].append(context.duration)
            
            # Keep only recent data
            if len(self.performance_data[context.request_id]) > 100:
                self.performance_data[context.request_id] = self.performance_data[context.request_id][-50:]

    def _record_error_pattern(self, error: str) -> None:
        """Record error patterns for analysis."""
        # Extract error type
        error_type = error.split(":")[0] if ":" in error else error
        self.error_patterns[error_type] += 1

    def _check_performance_issues(self, context: DebugContext) -> None:
        """Check for performance issues."""
        if context.duration and context.duration > self.slow_threshold:
            context.warnings.append(f"Slow operation detected: {context.duration:.2f}s")
            
        if context.memory_before and context.memory_after:
            memory_diff = context.memory_after - context.memory_before
            if memory_diff > self.memory_threshold:
                context.warnings.append(f"High memory usage: {memory_diff / 1024 / 1024:.2f}MB")

    def _check_memory_issues(self, context: DebugContext) -> None:
        """Check for memory leaks and issues."""
        if context.memory_before and context.memory_after:
            memory_diff = context.memory_after - context.memory_before
            if memory_diff > self.memory_threshold:
                self.memory_leaks.add(context.request_id)

    def get_debug_summary(self) -> Dict[str, Any]:
        """Get comprehensive debug summary."""
        if not self.debug_enabled:
            return {"debug_enabled": False}
        
        # Calculate statistics
        total_contexts = len(self.context_history)
        error_count = sum(len(ctx.errors) for ctx in self.context_history)
        warning_count = sum(len(ctx.warnings) for ctx in self.context_history)
        
        # Performance statistics
        all_durations = [ctx.duration for ctx in self.context_history if ctx.duration]
        avg_duration = sum(all_durations) / len(all_durations) if all_durations else 0
        max_duration = max(all_durations) if all_durations else 0
        
        # Memory statistics
        memory_usage = self._get_memory_usage()
        cpu_usage = self._get_cpu_usage()
        
        return {
            "debug_enabled": self.debug_enabled,
            "profiling_enabled": self.profiling_enabled,
            "total_contexts": total_contexts,
            "active_contexts": len(self.active_contexts),
            "error_count": error_count,
            "warning_count": warning_count,
            "memory_leaks_detected": len(self.memory_leaks),
            "slow_operations": len(self.slow_operations),
            "performance_stats": {
                "average_duration": avg_duration,
                "max_duration": max_duration,
                "current_memory_mb": memory_usage / 1024 / 1024,
                "current_cpu_percent": cpu_usage
            },
            "error_patterns": dict(self.error_patterns),
            "recent_slow_operations": dict(list(self.slow_operations.items())[-10:]),
            "thresholds": {
                "slow_operation_threshold": self.slow_threshold,
                "memory_threshold_mb": self.memory_threshold / 1024 / 1024
            }
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report."""
        if not self.debug_enabled:
            return {"debug_enabled": False}
        
        # Analyze performance data
        performance_analysis = {}
        for operation, durations in self.performance_data.items():
            if durations:
                performance_analysis[operation] = {
                    "count": len(durations),
                    "avg_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "p95_duration": sorted(durations)[int(len(durations) * 0.95)] if durations else 0
                }
        
        return {
            "performance_analysis": performance_analysis,
            "system_metrics": {
                "memory_usage_mb": self._get_memory_usage() / 1024 / 1024,
                "cpu_usage_percent": self._get_cpu_usage(),
                "active_processes": len(psutil.pids())
            },
            "recommendations": self._generate_performance_recommendations()
        }

    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance recommendations based on analysis."""
        recommendations = []
        
        # Check for slow operations
        if self.slow_operations:
            slowest = max(self.slow_operations.items(), key=lambda x: x[1])
            recommendations.append(f"Consider optimizing '{slowest[0]}' (takes {slowest[1]:.2f}s)")
        
        # Check for memory issues
        if self.memory_leaks:
            recommendations.append(f"Investigate potential memory leaks in {len(self.memory_leaks)} operations")
        
        # Check for error patterns
        if self.error_patterns:
            most_common_error = max(self.error_patterns.items(), key=lambda x: x[1])
            recommendations.append(f"Address recurring error: '{most_common_error[0]}' ({most_common_error[1]} occurrences)")
        
        # System recommendations
        memory_usage = self._get_memory_usage() / 1024 / 1024
        if memory_usage > 500:  # 500MB
            recommendations.append("Consider memory optimization - current usage is high")
        
        cpu_usage = self._get_cpu_usage()
        if cpu_usage > 80:  # 80%
            recommendations.append("High CPU usage detected - consider load balancing or optimization")
        
        return recommendations

    def export_debug_data(self, filepath: str) -> None:
        """Export debug data to file for analysis."""
        if not self.debug_enabled:
            return
        
        debug_data = {
            "summary": self.get_debug_summary(),
            "performance_report": self.get_performance_report(),
            "context_history": [
                {
                    "request_id": ctx.request_id,
                    "duration": ctx.duration,
                    "memory_before": ctx.memory_before,
                    "memory_after": ctx.memory_after,
                    "errors": ctx.errors,
                    "warnings": ctx.warnings,
                    "performance_metrics": ctx.performance_metrics
                }
                for ctx in self.context_history
            ]
        }
        
        import json
        with open(filepath, 'w') as f:
            json.dump(debug_data, f, indent=2, default=str)
        
        log.info(f"Debug data exported to {filepath}")


# Global debugger instance
advanced_debugger = AdvancedDebugger()