"""Advanced memory debugging and leak detection system."""

from __future__ import annotations

import gc
import logging
import os
import sys
import time
import tracemalloc
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import psutil

log = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """Memory snapshot data."""
    timestamp: float
    memory_usage: int
    memory_percent: float
    objects_count: int
    gc_counts: Tuple[int, int, int]
    top_objects: List[Tuple[str, int]]
    tracemalloc_snapshot: Optional[Any] = None


@dataclass
class MemoryLeak:
    """Memory leak detection result."""
    leak_id: str
    start_time: float
    end_time: Optional[float] = None
    memory_growth: int = 0
    objects_growth: int = 0
    severity: str = "low"
    description: str = ""
    stack_trace: Optional[str] = None


class MemoryDebugger:
    """Advanced memory debugging system with leak detection."""

    def __init__(self) -> None:
        """Initialize the memory debugger."""
        self.snapshots: deque = deque(maxlen=100)
        self.memory_leaks: Dict[str, MemoryLeak] = {}
        self.object_tracking: Dict[str, int] = defaultdict(int)
        self.memory_threshold = int(os.getenv("MEMORY_LEAK_THRESHOLD", "50")) * 1024 * 1024  # 50MB
        self.growth_threshold = int(os.getenv("MEMORY_GROWTH_THRESHOLD", "10")) * 1024 * 1024  # 10MB
        # Enable by default to surface diagnostics in tests and dev
        self.debug_enabled = os.getenv("MEMORY_DEBUG_ENABLED", "true").lower() == "true"
        self.tracemalloc_enabled = os.getenv("TRACEMALLOC_ENABLED", "false").lower() == "true"
        
        # Start tracemalloc if enabled
        if self.tracemalloc_enabled and not tracemalloc.is_tracing():
            tracemalloc.start()
            log.info("Tracemalloc started")
        
        log.info("Memory Debugger initialized")

    def take_snapshot(self, label: str = "") -> MemorySnapshot:
        """Take a memory snapshot."""
        if not self.debug_enabled:
            return None
        
        # Get memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # Get object count
        objects_count = len(gc.get_objects())
        
        # Get GC counts
        gc_counts = gc.get_count()
        
        # Get top memory-consuming objects
        top_objects = self._get_top_objects()
        
        # Get tracemalloc snapshot if enabled
        tracemalloc_snapshot = None
        if self.tracemalloc_enabled:
            tracemalloc_snapshot = tracemalloc.take_snapshot()
        
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            memory_usage=memory_info.rss,
            memory_percent=memory_percent,
            objects_count=objects_count,
            gc_counts=gc_counts,
            top_objects=top_objects,
            tracemalloc_snapshot=tracemalloc_snapshot
        )
        
        self.snapshots.append(snapshot)
        
        # Check for memory leaks
        self._check_memory_leaks(snapshot, label)
        
        log.debug(f"Memory snapshot taken: {label} - {memory_info.rss / 1024 / 1024:.2f}MB")
        
        return snapshot

    def _get_top_objects(self) -> List[Tuple[str, int]]:
        """Get top memory-consuming object types."""
        if not self.debug_enabled:
            return []
        
        object_counts = defaultdict(int)
        object_sizes = defaultdict(int)
        
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            object_counts[obj_type] += 1
            
            try:
                size = sys.getsizeof(obj)
                object_sizes[obj_type] += size
            except (TypeError, ValueError):
                pass
        
        # Sort by total size
        sorted_objects = sorted(object_sizes.items(), key=lambda x: x[1], reverse=True)
        return sorted_objects[:20]  # Top 20

    def _check_memory_leaks(self, snapshot: MemorySnapshot, label: str) -> None:
        """Check for memory leaks."""
        if len(self.snapshots) < 2:
            return
        
        previous_snapshot = self.snapshots[-2]
        
        # Calculate memory growth
        memory_growth = snapshot.memory_usage - previous_snapshot.memory_usage
        objects_growth = snapshot.objects_count - previous_snapshot.objects_count
        
        # Check if growth exceeds threshold
        if memory_growth > self.growth_threshold:
            leak_id = f"{label}_{int(snapshot.timestamp)}"
            
            if leak_id not in self.memory_leaks:
                # Determine severity
                severity = "high" if memory_growth > self.memory_threshold else "medium"
                
                leak = MemoryLeak(
                    leak_id=leak_id,
                    start_time=snapshot.timestamp,
                    memory_growth=memory_growth,
                    objects_growth=objects_growth,
                    severity=severity,
                    description=f"Memory growth detected: {memory_growth / 1024 / 1024:.2f}MB"
                )
                
                self.memory_leaks[leak_id] = leak
                
                log.warning(
                    f"Potential memory leak detected: {leak_id} - "
                    f"Growth: {memory_growth / 1024 / 1024:.2f}MB, "
                    f"Objects: +{objects_growth}"
                )

    def track_object(self, obj: Any, label: str = "") -> str:
        """Track an object for memory debugging."""
        if not self.debug_enabled:
            return ""
        
        obj_id = f"{label}_{id(obj)}_{time.time()}"
        self.object_tracking[obj_id] = sys.getsizeof(obj)
        
        return obj_id

    def untrack_object(self, obj_id: str) -> None:
        """Stop tracking an object."""
        if obj_id in self.object_tracking:
            del self.object_tracking[obj_id]

    def force_garbage_collection(self) -> Dict[str, int]:
        """Force garbage collection and return statistics."""
        if not self.debug_enabled:
            return {}
        
        # Take snapshot before GC
        before_snapshot = self.take_snapshot("before_gc")
        
        # Force garbage collection
        collected = gc.collect()
        
        # Take snapshot after GC
        after_snapshot = self.take_snapshot("after_gc")
        
        # Calculate differences
        memory_freed = before_snapshot.memory_usage - after_snapshot.memory_usage
        objects_freed = before_snapshot.objects_count - after_snapshot.objects_count
        
        log.info(
            f"Garbage collection completed: {collected} objects collected, "
            f"{memory_freed / 1024 / 1024:.2f}MB freed, "
            f"{objects_freed} objects freed"
        )
        
        return {
            "objects_collected": collected,
            "memory_freed_bytes": memory_freed,
            "objects_freed": objects_freed
        }

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get memory usage summary."""
        if not self.debug_enabled:
            return {"debug_enabled": False}
        
        # Get current memory info
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Calculate statistics from snapshots
        if self.snapshots:
            memory_values = [s.memory_usage for s in self.snapshots]
            object_counts = [s.objects_count for s in self.snapshots]
            
            avg_memory = sum(memory_values) / len(memory_values)
            max_memory = max(memory_values)
            min_memory = min(memory_values)
            
            avg_objects = sum(object_counts) / len(object_counts)
            max_objects = max(object_counts)
            min_objects = min(object_counts)
        else:
            avg_memory = max_memory = min_memory = memory_info.rss
            avg_objects = max_objects = min_objects = len(gc.get_objects())
        
        # Get current top objects
        current_top_objects = self._get_top_objects()
        
        return {
            "debug_enabled": self.debug_enabled,
            "tracemalloc_enabled": self.tracemalloc_enabled,
            "current_memory": {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent()
            },
            "statistics": {
                "avg_memory_mb": avg_memory / 1024 / 1024,
                "max_memory_mb": max_memory / 1024 / 1024,
                "min_memory_mb": min_memory / 1024 / 1024,
                "avg_objects": avg_objects,
                "max_objects": max_objects,
                "min_objects": min_objects
            },
            "gc_info": {
                "counts": gc.get_count(),
                "thresholds": gc.get_threshold()
            },
            "top_objects": current_top_objects[:10],
            "memory_leaks_detected": len(self.memory_leaks),
            "tracked_objects": len(self.object_tracking),
            "thresholds": {
                "memory_leak_threshold_mb": self.memory_threshold / 1024 / 1024,
                "growth_threshold_mb": self.growth_threshold / 1024 / 1024
            }
        }

    def get_memory_leaks_report(self) -> Dict[str, Any]:
        """Get detailed memory leaks report."""
        if not self.debug_enabled:
            return {"debug_enabled": False}
        
        # Analyze memory leaks
        leak_analysis = {}
        for leak_id, leak in self.memory_leaks.items():
            leak_analysis[leak_id] = {
                "start_time": leak.start_time,
                "end_time": leak.end_time,
                "memory_growth_mb": leak.memory_growth / 1024 / 1024,
                "objects_growth": leak.objects_growth,
                "severity": leak.severity,
                "description": leak.description,
                "duration": (leak.end_time or time.time()) - leak.start_time
            }
        
        # Generate recommendations
        recommendations = self._generate_memory_recommendations()
        
        return {
            "leak_analysis": leak_analysis,
            "recommendations": recommendations,
            "summary": {
                "total_leaks": len(self.memory_leaks),
                "high_severity_leaks": sum(1 for l in self.memory_leaks.values() if l.severity == "high"),
                "medium_severity_leaks": sum(1 for l in self.memory_leaks.values() if l.severity == "medium"),
                "low_severity_leaks": sum(1 for l in self.memory_leaks.values() if l.severity == "low")
            }
        }

    def _generate_memory_recommendations(self) -> List[str]:
        """Generate memory optimization recommendations."""
        recommendations = []
        
        # Check for high memory usage
        if self.snapshots:
            current_memory = self.snapshots[-1].memory_usage / 1024 / 1024
            if current_memory > 500:  # 500MB
                recommendations.append(f"High memory usage detected: {current_memory:.2f}MB - consider optimization")
        
        # Check for memory leaks
        if self.memory_leaks:
            high_severity_leaks = [l for l in self.memory_leaks.values() if l.severity == "high"]
            if high_severity_leaks:
                recommendations.append(f"Address {len(high_severity_leaks)} high-severity memory leaks")
        
        # Check for object count growth
        if len(self.snapshots) > 10:
            recent_objects = [s.objects_count for s in list(self.snapshots)[-10:]]
            if len(set(recent_objects)) > 1:  # Objects count is changing
                avg_growth = (recent_objects[-1] - recent_objects[0]) / len(recent_objects)
                if avg_growth > 1000:  # Growing by more than 1000 objects per snapshot
                    recommendations.append("Object count is growing rapidly - check for object leaks")
        
        # Check GC effectiveness
        gc_counts = gc.get_count()
        if gc_counts[0] > 100:  # Generation 0 collections
            recommendations.append("High garbage collection frequency - consider memory optimization")
        
        return recommendations

    def export_memory_data(self, filepath: str) -> None:
        """Export memory debugging data to file."""
        if not self.debug_enabled:
            return
        
        import json
        
        memory_data = {
            "summary": self.get_memory_summary(),
            "leaks_report": self.get_memory_leaks_report(),
            "snapshots": [
                {
                    "timestamp": s.timestamp,
                    "memory_usage": s.memory_usage,
                    "memory_percent": s.memory_percent,
                    "objects_count": s.objects_count,
                    "gc_counts": s.gc_counts,
                    "top_objects": s.top_objects
                }
                for s in self.snapshots
            ],
            "tracked_objects": dict(self.object_tracking)
        }
        
        with open(filepath, 'w') as f:
            json.dump(memory_data, f, indent=2, default=str)
        
        log.info(f"Memory data exported to {filepath}")

    def get_tracemalloc_stats(self) -> Dict[str, Any]:
        """Get tracemalloc statistics if enabled."""
        if not self.tracemalloc_enabled:
            return {"tracemalloc_enabled": False}
        
        if not self.snapshots or not self.snapshots[-1].tracemalloc_snapshot:
            return {"tracemalloc_enabled": True, "no_snapshot": True}
        
        snapshot = self.snapshots[-1].tracemalloc_snapshot
        
        # Get top memory allocations
        top_stats = snapshot.statistics('lineno')[:10]
        
        return {
            "tracemalloc_enabled": True,
            "current_size": tracemalloc.get_traced_memory()[0],
            "peak_size": tracemalloc.get_traced_memory()[1],
            "top_allocations": [
                {
                    "filename": stat.traceback.format()[0],
                    "size": stat.size,
                    "count": stat.count
                }
                for stat in top_stats
            ]
        }


# Global memory debugger instance
memory_debugger = MemoryDebugger()
