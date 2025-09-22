"""Performance profiling system for Capsule Brain."""

import asyncio
import cProfile
import functools
import io
import logging
import pstats
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

log = logging.getLogger(__name__)


class Profiler:
    """Advanced performance profiling system."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.profiles: dict[str, cProfile.Profile] = {}
        self.timing_data: dict[str, list[float]] = {}
        self.memory_snapshots: list[dict[str, Any]] = []
        self.max_snapshots = 100

    def start_profile(self, name: str) -> None:
        """Start profiling a named section."""
        if not self.enabled:
            return

        if name not in self.profiles:
            self.profiles[name] = cProfile.Profile()

        self.profiles[name].enable()
        log.debug(f"Started profiling: {name}")

    def stop_profile(self, name: str) -> None:
        """Stop profiling a named section."""
        if not self.enabled or name not in self.profiles:
            return

        self.profiles[name].disable()
        log.debug(f"Stopped profiling: {name}")

    def get_profile_stats(self, name: str, sort_by: str = "cumulative") -> str:
        """Get profiling statistics for a named section."""
        if name not in self.profiles:
            return f"No profile data for '{name}'"

        s = io.StringIO()
        ps = pstats.Stats(self.profiles[name], stream=s)
        ps.sort_stats(sort_by)
        ps.print_stats(20)  # Top 20 functions

        return s.getvalue()

    def get_profiling_summary(self) -> dict[str, Any]:
        """Get a summary of all profiling data."""
        summary = {
            "enabled": self.enabled,
            "active_profiles": list(self.profiles.keys()),
            "timing_data": dict(self.timing_data),
            "memory_snapshots_count": len(self.memory_snapshots),
        }
        return summary

    def time_function(self, name: str | None = None):
        """Decorator to time function execution."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                func_name = name or f"{func.__module__}.{func.__name__}"
                start_time = time.perf_counter()

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.perf_counter() - start_time
                    self._record_timing(func_name, duration)

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)

                func_name = name or f"{func.__module__}.{func.__name__}"
                start_time = time.perf_counter()

                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.perf_counter() - start_time
                    self._record_timing(func_name, duration)

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def _record_timing(self, name: str, duration: float) -> None:
        """Record timing data for a function."""
        if name not in self.timing_data:
            self.timing_data[name] = []

        self.timing_data[name].append(duration)

        # Keep only last 1000 measurements per function
        if len(self.timing_data[name]) > 1000:
            self.timing_data[name] = self.timing_data[name][-1000:]

    def get_timing_stats(self, name: str) -> dict[str, float]:
        """Get timing statistics for a function."""
        if name not in self.timing_data or not self.timing_data[name]:
            return {}

        times = self.timing_data[name]
        return {
            "count": len(times),
            "total": sum(times),
            "average": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "median": sorted(times)[len(times) // 2],
        }

    def get_all_timing_stats(self) -> dict[str, dict[str, float]]:
        """Get timing statistics for all functions."""
        return {name: self.get_timing_stats(name) for name in self.timing_data.keys()}

    @asynccontextmanager
    async def profile_context(self, name: str):
        """Context manager for profiling code sections."""
        if not self.enabled:
            yield
            return

        self.start_profile(name)
        start_time = time.perf_counter()

        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self.stop_profile(name)
            self._record_timing(f"context_{name}", duration)

    def take_memory_snapshot(self, label: str = None) -> None:
        """Take a memory snapshot for analysis."""
        if not self.enabled:
            return

        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "label": label or "snapshot",
                "rss": memory_info.rss,  # Resident Set Size
                "vms": memory_info.vms,  # Virtual Memory Size
                "percent": process.memory_percent(),
                "available": psutil.virtual_memory().available,
            }

            self.memory_snapshots.append(snapshot)

            # Keep only recent snapshots
            if len(self.memory_snapshots) > self.max_snapshots:
                self.memory_snapshots = self.memory_snapshots[-self.max_snapshots :]

            log.debug(f"Memory snapshot taken: {snapshot}")

        except ImportError:
            log.warning("psutil not available for memory profiling")
        except Exception as e:
            log.error(f"Error taking memory snapshot: {e}")

    def get_memory_trend(self) -> list[dict[str, Any]]:
        """Get memory usage trend over time."""
        return self.memory_snapshots.copy()

    def clear_data(self) -> None:
        """Clear all profiling data."""
        self.profiles.clear()
        self.timing_data.clear()
        self.memory_snapshots.clear()
        log.info("Profiling data cleared")

    def get_summary(self) -> dict[str, Any]:
        """Get profiling summary."""
        return {
            "enabled": self.enabled,
            "active_profiles": len(self.profiles),
            "timed_functions": len(self.timing_data),
            "memory_snapshots": len(self.memory_snapshots),
            "top_slow_functions": self._get_top_slow_functions(5),
        }

    def _get_top_slow_functions(self, limit: int = 5) -> list[dict[str, Any]]:
        """Get top slowest functions by average time."""
        stats = self.get_all_timing_stats()
        sorted_functions = sorted(stats.items(), key=lambda x: x[1].get("average", 0), reverse=True)

        return [{"function": name, "stats": stats} for name, stats in sorted_functions[:limit]]

    def enable(self) -> None:
        """Enable profiling."""
        self.enabled = True
        log.info("Profiling enabled")

    def disable(self) -> None:
        """Disable profiling."""
        self.enabled = False
        log.info("Profiling disabled")


# Global profiler instance
profiler = Profiler(enabled=False)


def profile_function(name: str | None = None):
    """Decorator to profile function execution."""
    return profiler.time_function(name)


def profile_context(name: str):
    """Context manager for profiling code sections."""
    return profiler.profile_context(name)
