"""Advanced profiling system for performance analysis and optimization."""

import asyncio
import cProfile
import functools
import io
import logging
import os
import pstats
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

import psutil
try:
    from memory_profiler import profile as memory_profile
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False
    # Create a no-op decorator when memory_profiler is not available
    def memory_profile(func):
        return func

log = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    """Result of a profiling operation."""
    function_name: str
    total_time: float
    call_count: int
    average_time: float
    memory_usage: int
    cpu_usage: float
    line_profiling: Optional[Dict] = None
    memory_profiling: Optional[Dict] = None


class AdvancedProfiler:
    """Advanced profiling system with multiple profiling techniques."""

    def __init__(self) -> None:
        """Initialize the profiler."""
        self.profiler = cProfile.Profile()
        self.profile_results: Dict[str, ProfileResult] = {}
        self.active_profiles: Dict[str, cProfile.Profile] = {}
        self.profiling_enabled = os.getenv("PROFILING_ENABLED", "true").lower() == "true"
        self.memory_profiling_enabled = os.getenv("MEMORY_PROFILING_ENABLED", "true").lower() == "true"
        self.line_profiling_enabled = os.getenv("LINE_PROFILING_ENABLED", "false").lower() == "true"
        
        # Performance thresholds
        self.slow_function_threshold = float(os.getenv("SLOW_FUNCTION_THRESHOLD", "0.1"))
        self.memory_threshold = int(os.getenv("MEMORY_PROFILING_THRESHOLD", "10")) * 1024 * 1024  # 10MB
        
        log.info("Advanced Profiler initialized")

    @contextmanager
    def profile_function(self, function_name: str):
        """Context manager for profiling function execution."""
        if not self.profiling_enabled:
            yield
            return

        # Start profiling
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Capture initial state
        start_time = time.time()
        start_memory = self._get_memory_usage()
        start_cpu = self._get_cpu_usage()
        
        try:
            yield profiler
        finally:
            # Stop profiling
            profiler.disable()
            
            # Capture final state
            end_time = time.time()
            end_memory = self._get_memory_usage()
            end_cpu = self._get_cpu_usage()
            
            # Analyze results
            self._analyze_profile_results(
                profiler, function_name, end_time - start_time,
                end_memory - start_memory, end_cpu - start_cpu
            )

    def profile_decorator(self, func: Callable) -> Callable:
        """Decorator for profiling function execution."""
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not self.profiling_enabled:
                return await func(*args, **kwargs)
            
            function_name = f"{func.__module__}.{func.__name__}"
            
            with self.profile_function(function_name) as profiler:
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not self.profiling_enabled:
                return func(*args, **kwargs)
            
            function_name = f"{func.__module__}.{func.__name__}"
            
            with self.profile_function(function_name) as profiler:
                return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    def memory_profile_decorator(self, func: Callable) -> Callable:
        """Decorator for memory profiling."""
        if not self.memory_profiling_enabled:
            return func
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use memory_profiler's profile decorator
            profiled_func = memory_profile(func)
            return profiled_func(*args, **kwargs)
        
        return wrapper

    def _analyze_profile_results(self, profiler: cProfile.Profile, function_name: str, 
                                total_time: float, memory_delta: int, cpu_delta: float) -> None:
        """Analyze profiling results."""
        # Get stats
        stats = pstats.Stats(profiler)
        
        # Find the function in stats
        function_stats = None
        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            if func[2] == function_name.split('.')[-1]:  # Match function name
                function_stats = (cc, nc, tt, ct, callers)
                break
        
        if function_stats:
            cc, nc, tt, ct, callers = function_stats
            
            result = ProfileResult(
                function_name=function_name,
                total_time=tt,
                call_count=cc,
                average_time=tt / cc if cc > 0 else 0,
                memory_usage=memory_delta,
                cpu_usage=cpu_delta
            )
            
            self.profile_results[function_name] = result
            
            # Log slow functions
            if result.average_time > self.slow_function_threshold:
                log.warning(
                    f"Slow function detected: {function_name} "
                    f"(avg: {result.average_time:.3f}s, calls: {cc})"
                )

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

    def get_profile_summary(self) -> Dict[str, Any]:
        """Get profiling summary."""
        if not self.profiling_enabled:
            return {"profiling_enabled": False}
        
        # Calculate statistics
        total_functions = len(self.profile_results)
        slow_functions = sum(1 for r in self.profile_results.values() 
                           if r.average_time > self.slow_function_threshold)
        
        # Get top slow functions
        slow_functions_list = sorted(
            self.profile_results.items(),
            key=lambda x: x[1].average_time,
            reverse=True
        )[:10]
        
        # Get memory usage
        current_memory = self._get_memory_usage()
        
        return {
            "profiling_enabled": self.profiling_enabled,
            "memory_profiling_enabled": self.memory_profiling_enabled,
            "line_profiling_enabled": self.line_profiling_enabled,
            "total_functions_profiled": total_functions,
            "slow_functions_detected": slow_functions,
            "current_memory_usage_mb": current_memory / 1024 / 1024,
            "slow_function_threshold": self.slow_function_threshold,
            "top_slow_functions": [
                {
                    "function": name,
                    "average_time": result.average_time,
                    "call_count": result.call_count,
                    "total_time": result.total_time,
                    "memory_usage": result.memory_usage,
                    "cpu_usage": result.cpu_usage
                }
                for name, result in slow_functions_list
            ]
        }

    def get_detailed_profile_report(self) -> Dict[str, Any]:
        """Get detailed profiling report."""
        if not self.profiling_enabled:
            return {"profiling_enabled": False}
        
        # Analyze all profile results
        analysis = {}
        for function_name, result in self.profile_results.items():
            analysis[function_name] = {
                "total_time": result.total_time,
                "call_count": result.call_count,
                "average_time": result.average_time,
                "memory_usage": result.memory_usage,
                "cpu_usage": result.cpu_usage,
                "is_slow": result.average_time > self.slow_function_threshold,
                "memory_intensive": abs(result.memory_usage) > self.memory_threshold
            }
        
        # Generate recommendations
        recommendations = self._generate_optimization_recommendations()
        
        return {
            "function_analysis": analysis,
            "system_metrics": {
                "total_memory_mb": self._get_memory_usage() / 1024 / 1024,
                "cpu_percent": self._get_cpu_usage(),
                "active_profiles": len(self.active_profiles)
            },
            "recommendations": recommendations,
            "profiling_settings": {
                "profiling_enabled": self.profiling_enabled,
                "memory_profiling_enabled": self.memory_profiling_enabled,
                "line_profiling_enabled": self.line_profiling_enabled,
                "slow_function_threshold": self.slow_function_threshold,
                "memory_threshold_mb": self.memory_threshold / 1024 / 1024
            }
        }

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Find slowest functions
        slowest_functions = sorted(
            self.profile_results.items(),
            key=lambda x: x[1].average_time,
            reverse=True
        )[:5]
        
        for function_name, result in slowest_functions:
            if result.average_time > self.slow_function_threshold:
                recommendations.append(
                    f"Optimize '{function_name}' - average execution time: {result.average_time:.3f}s"
                )
        
        # Find memory-intensive functions
        memory_intensive = [
            (name, result) for name, result in self.profile_results.items()
            if abs(result.memory_usage) > self.memory_threshold
        ]
        
        for function_name, result in memory_intensive:
            recommendations.append(
                f"Review memory usage in '{function_name}' - {result.memory_usage / 1024 / 1024:.2f}MB"
            )
        
        # System-level recommendations
        current_memory = self._get_memory_usage() / 1024 / 1024
        if current_memory > 500:  # 500MB
            recommendations.append("Consider memory optimization - high overall memory usage")
        
        cpu_usage = self._get_cpu_usage()
        if cpu_usage > 80:  # 80%
            recommendations.append("High CPU usage detected - consider performance optimization")
        
        return recommendations

    def export_profile_data(self, filepath: str) -> None:
        """Export profiling data to file."""
        if not self.profiling_enabled:
            return
        
        import json
        
        profile_data = {
            "summary": self.get_profile_summary(),
            "detailed_report": self.get_detailed_profile_report(),
            "raw_results": {
                name: {
                    "function_name": result.function_name,
                    "total_time": result.total_time,
                    "call_count": result.call_count,
                    "average_time": result.average_time,
                    "memory_usage": result.memory_usage,
                    "cpu_usage": result.cpu_usage
                }
                for name, result in self.profile_results.items()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(profile_data, f, indent=2, default=str)
        
        log.info(f"Profile data exported to {filepath}")

    def start_profiling(self, profile_name: str) -> None:
        """Start profiling with a specific name."""
        if not self.profiling_enabled:
            return
        
        profiler = cProfile.Profile()
        profiler.enable()
        self.active_profiles[profile_name] = profiler
        log.info(f"Started profiling: {profile_name}")

    def stop_profiling(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Stop profiling and return results."""
        if not self.profiling_enabled or profile_name not in self.active_profiles:
            return None
        
        profiler = self.active_profiles[profile_name]
        profiler.disable()
        
        # Analyze results
        stats = pstats.Stats(profiler)
        
        # Convert to dictionary
        results = {}
        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            results[f"{func[0]}:{func[1]}:{func[2]}"] = {
                "call_count": cc,
                "total_time": tt,
                "cumulative_time": ct,
                "callers": dict(callers)
            }
        
        del self.active_profiles[profile_name]
        log.info(f"Stopped profiling: {profile_name}")
        
        return results


# Global profiler instance
advanced_profiler = AdvancedProfiler()