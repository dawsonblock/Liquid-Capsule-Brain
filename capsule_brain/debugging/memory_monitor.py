"""Memory monitoring and leak detection system."""

import gc
import logging
import tracemalloc
from datetime import datetime
from typing import Any

log = logging.getLogger(__name__)


class MemoryMonitor:
    """Advanced memory monitoring and leak detection system."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.memory_snapshots: list[dict[str, Any]] = []
        self.leak_suspects: list[dict[str, Any]] = []
        self.object_counts: dict[str, int] = {}
        self.max_snapshots = 100
        self.tracemalloc_started = False
        # Track garbage collection counts over time
        self._initial_gc_counts: tuple[int, int, int] | None = None
        self._last_gc_counts: tuple[int, int, int] | None = None

    def start_monitoring(self) -> None:
        """Start memory monitoring."""
        if not self.enabled:
            return

        if not self.tracemalloc_started:
            tracemalloc.start()
            self.tracemalloc_started = True
            # Initialize GC collection tracking
            self._initial_gc_counts = gc.get_count()
            self._last_gc_counts = self._initial_gc_counts
            log.info("Memory monitoring started")

    def stop_monitoring(self) -> None:
        """Stop memory monitoring."""
        if self.tracemalloc_started:
            tracemalloc.stop()
            self.tracemalloc_started = False
            log.info("Memory monitoring stopped")

    def take_snapshot(self, label: str | None = None) -> dict[str, Any]:
        """Take a memory snapshot."""
        if not self.enabled:
            return {}

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "label": label or "snapshot",
            "gc_counts": gc.get_count(),
            "gc_threshold": gc.get_threshold(),
            "object_counts": self._count_objects(),
        }

        if self.tracemalloc_started:
            current, peak = tracemalloc.get_traced_memory()
            snapshot.update(
                {
                    "traced_current": current,
                    "traced_peak": peak,
                    "traced_difference": current
                    - (
                        self.memory_snapshots[-1]["traced_current"]
                        if self.memory_snapshots and "traced_current" in self.memory_snapshots[-1]
                        else 0
                    ),
                }
            )

        self.memory_snapshots.append(snapshot)

        # Keep only recent snapshots
        if len(self.memory_snapshots) > self.max_snapshots:
            self.memory_snapshots = self.memory_snapshots[-self.max_snapshots :]

        log.debug(f"Memory snapshot taken: {snapshot}")
        return snapshot

    def _count_objects(self) -> dict[str, int]:
        """Count objects by type."""
        counts: dict[str, int] = {}
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            counts[obj_type] = counts.get(obj_type, 0) + 1
        return counts

    def detect_memory_leaks(self) -> list[dict[str, Any]]:
        """Detect potential memory leaks."""
        if len(self.memory_snapshots) < 2:
            return []

        leaks = []
        current = self.memory_snapshots[-1]
        previous = self.memory_snapshots[-2]

        # Check for growing object counts
        for obj_type, current_count in current["object_counts"].items():
            previous_count = previous["object_counts"].get(obj_type, 0)
            if current_count > previous_count * 1.5:  # 50% growth
                leaks.append(
                    {
                        "type": "growing_objects",
                        "object_type": obj_type,
                        "previous_count": previous_count,
                        "current_count": current_count,
                        "growth_rate": (current_count - previous_count) / max(previous_count, 1),
                    }
                )

        # Check for growing traced memory
        if "traced_current" in current and "traced_current" in previous:
            current_mem = current["traced_current"]
            previous_mem = previous["traced_current"]
            if current_mem > previous_mem * 1.2:  # 20% growth
                leaks.append(
                    {
                        "type": "growing_memory",
                        "previous_memory": previous_mem,
                        "current_memory": current_mem,
                        "growth_rate": (current_mem - previous_mem) / max(previous_mem, 1),
                    }
                )

        self.leak_suspects.extend(leaks)
        return leaks

    def get_memory_stats(self) -> dict[str, Any]:
        """Get current memory statistics."""
        if not self.enabled:
            return {}

        stats = {
            "gc_counts": gc.get_count(),
            "gc_threshold": gc.get_threshold(),
            "object_counts": self._count_objects(),
            "snapshots_count": len(self.memory_snapshots),
            "leak_suspects_count": len(self.leak_suspects),
        }

        if self.tracemalloc_started:
            current, peak = tracemalloc.get_traced_memory()
            stats.update({"traced_current": current, "traced_peak": peak})

        return stats

    def get_top_memory_consumers(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get top memory consuming object types."""
        if not self.memory_snapshots:
            return []

        current_counts = self.memory_snapshots[-1]["object_counts"]
        return sorted(current_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def force_garbage_collection(self) -> dict[str, int]:
        """Force garbage collection and return collection stats."""
        if not self.enabled:
            return {}

        before_counts = gc.get_count()
        collected = gc.collect()
        after_counts = gc.get_count()

        # Update collection tracking
        if self._last_gc_counts is not None:
            self._last_gc_counts = after_counts

        stats = {
            "collected_objects": collected,
            "before_counts": before_counts,
            "after_counts": after_counts,
            "reduction": tuple(b - a for a, b in zip(after_counts, before_counts, strict=False)),
        }

        log.info(f"Garbage collection: {collected} objects collected")
        return stats

    def get_memory_trend(self) -> list[dict[str, Any]]:
        """Get memory usage trend over time."""
        return self.memory_snapshots.copy()

    def get_leak_suspects(self) -> list[dict[str, Any]]:
        """Get all detected leak suspects."""
        return self.leak_suspects.copy()

    def clear_leak_suspects(self) -> None:
        """Clear leak suspects list."""
        self.leak_suspects.clear()
        log.info("Leak suspects cleared")

    def analyze_memory_patterns(self) -> dict[str, Any]:
        """Analyze memory usage patterns."""
        if len(self.memory_snapshots) < 3:
            return {"error": "Not enough snapshots for analysis"}

        analysis = {
            "total_snapshots": len(self.memory_snapshots),
            "time_span": self._calculate_time_span(),
            "memory_growth_rate": self._calculate_memory_growth_rate(),
            "object_growth_patterns": self._analyze_object_growth(),
            "gc_efficiency": self._analyze_gc_efficiency(),
        }

        return analysis

    def _calculate_time_span(self) -> float:
        """Calculate time span of snapshots in seconds."""
        if len(self.memory_snapshots) < 2:
            return 0

        first = datetime.fromisoformat(self.memory_snapshots[0]["timestamp"])
        last = datetime.fromisoformat(self.memory_snapshots[-1]["timestamp"])
        return (last - first).total_seconds()

    def _calculate_memory_growth_rate(self) -> float:
        """Calculate memory growth rate per second."""
        if len(self.memory_snapshots) < 2:
            return 0

        time_span = self._calculate_time_span()
        if time_span == 0:
            return 0

        first_mem = self.memory_snapshots[0].get("traced_current", 0)
        last_mem = self.memory_snapshots[-1].get("traced_current", 0)

        if first_mem == 0:
            return 0

        growth = (last_mem - first_mem) / time_span
        return growth

    def _analyze_object_growth(self) -> dict[str, float]:
        """Analyze object growth patterns."""
        if len(self.memory_snapshots) < 2:
            return {}

        first_counts = self.memory_snapshots[0]["object_counts"]
        last_counts = self.memory_snapshots[-1]["object_counts"]

        growth_rates = {}
        for obj_type in set(first_counts.keys()) | set(last_counts.keys()):
            first_count = first_counts.get(obj_type, 0)
            last_count = last_counts.get(obj_type, 0)

            if first_count > 0:
                growth_rate = (last_count - first_count) / first_count
                growth_rates[obj_type] = growth_rate

        return growth_rates

    def _analyze_gc_efficiency(self) -> dict[str, Any]:
        """Analyze garbage collection efficiency."""
        if len(self.memory_snapshots) < 2:
            return {}

        # Calculate actual collection counts since monitoring started
        current_counts = gc.get_count()
        if self._initial_gc_counts is not None:
            # Calculate collections by generation (current - initial)
            collection_counts = tuple(
                c - i for c, i in zip(current_counts, self._initial_gc_counts, strict=False)
            )
            total_collections = sum(collection_counts)
        else:
            # Fallback: use current object counts if tracking not initialized
            collection_counts = current_counts
            total_collections = sum(current_counts)

        time_span = self._calculate_time_span()

        return {
            "total_collections": total_collections,
            "collections_per_second": total_collections / max(time_span, 1),
            "collection_counts_by_generation": collection_counts,
            "current_object_counts": current_counts,
            "thresholds": gc.get_threshold(),
        }

    def enable(self) -> None:
        """Enable memory monitoring."""
        self.enabled = True
        self.start_monitoring()
        log.info("Memory monitoring enabled")

    def disable(self) -> None:
        """Disable memory monitoring."""
        self.enabled = False
        self.stop_monitoring()
        log.info("Memory monitoring disabled")

    def get_summary(self) -> dict[str, Any]:
        """Get memory monitoring summary."""
        return {
            "enabled": self.enabled,
            "tracemalloc_active": self.tracemalloc_started,
            "snapshots_count": len(self.memory_snapshots),
            "leak_suspects_count": len(self.leak_suspects),
            "current_stats": self.get_memory_stats(),
        }


# Global memory monitor instance
memory_monitor = MemoryMonitor(enabled=False)


def monitor_memory(label: str = None):
    """Decorator to monitor memory usage of functions."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not memory_monitor.enabled:
                return func(*args, **kwargs)

            memory_monitor.take_snapshot(f"before_{label or func.__name__}")
            try:
                result = func(*args, **kwargs)
                memory_monitor.take_snapshot(f"after_{label or func.__name__}")
                return result
            except Exception:
                memory_monitor.take_snapshot(f"error_{label or func.__name__}")
                raise

        return wrapper

    return decorator
