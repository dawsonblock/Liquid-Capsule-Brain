"""Performance optimization system with intelligent caching and resource management."""

import asyncio
import functools
import logging
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil

log = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    timestamp: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    ttl: float = 300.0  # 5 minutes default


@dataclass
class PerformanceMetrics:
    """Performance metrics for optimization."""
    response_time: float
    memory_usage: int
    cpu_usage: float
    cache_hit_rate: float
    throughput: float
    error_rate: float


class IntelligentCache:
    """Intelligent caching system with adaptive TTL and eviction policies."""

    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0):
        """Initialize the cache."""
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_patterns: Dict[str, List[float]] = defaultdict(list)
        self.hit_count = 0
        self.miss_count = 0
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.cache:
            self.miss_count += 1
            return None
        
        entry = self.cache[key]
        current_time = time.time()
        
        # Check TTL
        if current_time - entry.timestamp > entry.ttl:
            del self.cache[key]
            self.miss_count += 1
            return None
        
        # Update access info
        entry.access_count += 1
        entry.last_access = current_time
        self.access_patterns[key].append(current_time)
        
        self.hit_count += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache."""
        if len(self.cache) >= self.max_size:
            self._evict_least_used()
        
        current_time = time.time()
        self.cache[key] = CacheEntry(
            value=value,
            timestamp=current_time,
            ttl=ttl or self.default_ttl
        )
    
    def _evict_least_used(self) -> None:
        """Evict least recently used entry."""
        if not self.cache:
            return
        
        # Find entry with lowest score (access_count / age)
        current_time = time.time()
        least_used_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].access_count / max(current_time - self.cache[k].timestamp, 1)
        )
        
        del self.cache[least_used_key]
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.access_patterns.clear()
        self.hit_count = 0
        self.miss_count = 0


class ResourceManager:
    """Intelligent resource management system."""

    def __init__(self):
        """Initialize resource manager."""
        self.memory_threshold = int(os.getenv("MEMORY_THRESHOLD_MB", "500")) * 1024 * 1024
        self.cpu_threshold = float(os.getenv("CPU_THRESHOLD_PERCENT", "80.0"))
        self.resource_history: deque = deque(maxlen=100)
        self.optimization_suggestions: List[str] = []
        
    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "memory_usage_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(),
            "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
        }
    
    def check_resource_health(self) -> Dict[str, Any]:
        """Check resource health and generate recommendations."""
        metrics = self.get_system_metrics()
        self.resource_history.append(metrics)
        
        health_status = "healthy"
        issues = []
        
        # Check memory usage
        if metrics["memory_usage_mb"] > self.memory_threshold / 1024 / 1024:
            health_status = "warning"
            issues.append(f"High memory usage: {metrics['memory_usage_mb']:.2f}MB")
        
        # Check CPU usage
        if metrics["cpu_percent"] > self.cpu_threshold:
            health_status = "warning"
            issues.append(f"High CPU usage: {metrics['cpu_percent']:.2f}%")
        
        # Check load average
        if metrics["load_average"] > 2.0:
            health_status = "warning"
            issues.append(f"High load average: {metrics['load_average']:.2f}")
        
        return {
            "status": health_status,
            "metrics": metrics,
            "issues": issues,
            "recommendations": self._generate_resource_recommendations(metrics)
        }
    
    def _generate_resource_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """Generate resource optimization recommendations."""
        recommendations = []
        
        if metrics["memory_usage_mb"] > 400:  # 400MB
            recommendations.append("Consider implementing memory pooling or object reuse")
        
        if metrics["cpu_percent"] > 70:  # 70%
            recommendations.append("Consider implementing request queuing or rate limiting")
        
        if metrics["load_average"] > 1.5:
            recommendations.append("Consider horizontal scaling or load balancing")
        
        return recommendations


class PerformanceOptimizer:
    """Advanced performance optimization system."""

    def __init__(self):
        """Initialize performance optimizer."""
        self.cache = IntelligentCache()
        self.resource_manager = ResourceManager()
        self.performance_history: deque = deque(maxlen=1000)
        self.optimization_enabled = os.getenv("PERFORMANCE_OPTIMIZATION_ENABLED", "true").lower() == "true"
        
        # Performance thresholds
        self.slow_response_threshold = float(os.getenv("SLOW_RESPONSE_THRESHOLD", "1.0"))
        self.memory_growth_threshold = int(os.getenv("MEMORY_GROWTH_THRESHOLD", "50")) * 1024 * 1024
        
        log.info("Performance Optimizer initialized")

    def cache_decorator(self, ttl: Optional[float] = None, key_func: Optional[Callable] = None):
        """Decorator for caching function results."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.optimization_enabled:
                    return await func(*args, **kwargs)
                
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                # Try to get from cache
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                self.cache.set(cache_key, result, ttl)
                return result
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self.optimization_enabled:
                    return func(*args, **kwargs)
                
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                # Try to get from cache
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.cache.set(cache_key, result, ttl)
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

    def performance_monitor(self, operation_name: str):
        """Context manager for performance monitoring."""
        class PerformanceContext:
            def __init__(self, optimizer, name):
                self.optimizer = optimizer
                self.name = name
                self.start_time = None
                self.start_memory = None
            
            def __enter__(self):
                self.start_time = time.time()
                self.start_memory = psutil.Process().memory_info().rss
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.start_time:
                    duration = time.time() - self.start_time
                    end_memory = psutil.Process().memory_info().rss
                    memory_delta = end_memory - self.start_memory
                    
                    # Record performance metrics
                    metrics = PerformanceMetrics(
                        response_time=duration,
                        memory_usage=memory_delta,
                        cpu_usage=psutil.Process().cpu_percent(),
                        cache_hit_rate=self.optimizer.cache.get_hit_rate(),
                        throughput=1.0 / duration if duration > 0 else 0.0,
                        error_rate=1.0 if exc_type else 0.0
                    )
                    
                    self.optimizer.performance_history.append({
                        "operation": self.name,
                        "timestamp": time.time(),
                        "metrics": metrics
                    })
                    
                    # Check for performance issues
                    if duration > self.optimizer.slow_response_threshold:
                        log.warning(f"Slow operation detected: {self.name} took {duration:.2f}s")
                    
                    if memory_delta > self.optimizer.memory_growth_threshold:
                        log.warning(f"High memory usage: {self.name} used {memory_delta / 1024 / 1024:.2f}MB")
        
        return PerformanceContext(self, operation_name)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance optimization summary."""
        if not self.optimization_enabled:
            return {"optimization_enabled": False}
        
        # Calculate performance statistics
        recent_metrics = [entry["metrics"] for entry in list(self.performance_history)[-100:]]
        
        if recent_metrics:
            avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
            avg_memory_usage = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
            avg_cpu_usage = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_cache_hit_rate = sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics)
            avg_throughput = sum(m.throughput for m in recent_metrics) / len(recent_metrics)
            avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
        else:
            avg_response_time = avg_memory_usage = avg_cpu_usage = 0.0
            avg_cache_hit_rate = avg_throughput = avg_error_rate = 0.0
        
        # Get resource health
        resource_health = self.resource_manager.check_resource_health()
        
        return {
            "optimization_enabled": self.optimization_enabled,
            "cache_stats": {
                "size": len(self.cache.cache),
                "max_size": self.cache.max_size,
                "hit_rate": self.cache.get_hit_rate(),
                "hit_count": self.cache.hit_count,
                "miss_count": self.cache.miss_count
            },
            "performance_metrics": {
                "avg_response_time": avg_response_time,
                "avg_memory_usage_mb": avg_memory_usage / 1024 / 1024,
                "avg_cpu_usage": avg_cpu_usage,
                "avg_cache_hit_rate": avg_cache_hit_rate,
                "avg_throughput": avg_throughput,
                "avg_error_rate": avg_error_rate
            },
            "resource_health": resource_health,
            "total_operations": len(self.performance_history),
            "thresholds": {
                "slow_response_threshold": self.slow_response_threshold,
                "memory_growth_threshold_mb": self.memory_growth_threshold / 1024 / 1024
            }
        }

    def get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []
        
        # Cache recommendations
        if self.cache.get_hit_rate() < 0.7:  # Less than 70% hit rate
            recommendations.append("Consider increasing cache TTL or improving cache key generation")
        
        # Performance recommendations
        recent_metrics = [entry["metrics"] for entry in list(self.performance_history)[-50:]]
        if recent_metrics:
            avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
            if avg_response_time > self.slow_response_threshold:
                recommendations.append(f"Average response time ({avg_response_time:.2f}s) exceeds threshold")
        
        # Resource recommendations
        resource_health = self.resource_manager.check_resource_health()
        recommendations.extend(resource_health["recommendations"])
        
        # System-level recommendations
        system_metrics = self.resource_manager.get_system_metrics()
        if system_metrics["memory_percent"] > 80:
            recommendations.append("High memory usage detected - consider memory optimization")
        
        if system_metrics["cpu_percent"] > 80:
            recommendations.append("High CPU usage detected - consider load balancing")
        
        return recommendations

    def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache based on usage patterns."""
        if not self.optimization_enabled:
            return {"optimization_enabled": False}
        
        # Analyze access patterns
        current_time = time.time()
        optimization_results = {
            "cache_size_before": len(self.cache.cache),
            "hit_rate_before": self.cache.get_hit_rate(),
            "optimizations_applied": []
        }
        
        # Remove expired entries
        expired_keys = [
            key for key, entry in self.cache.cache.items()
            if current_time - entry.timestamp > entry.ttl
        ]
        
        for key in expired_keys:
            del self.cache.cache[key]
        
        if expired_keys:
            optimization_results["optimizations_applied"].append(f"Removed {len(expired_keys)} expired entries")
        
        # Adjust TTL based on access patterns
        for key, entry in self.cache.cache.items():
            if entry.access_count > 10:  # Frequently accessed
                entry.ttl = min(entry.ttl * 1.5, 3600.0)  # Increase TTL up to 1 hour
            elif entry.access_count < 2:  # Rarely accessed
                entry.ttl = max(entry.ttl * 0.8, 60.0)  # Decrease TTL down to 1 minute
        
        optimization_results.update({
            "cache_size_after": len(self.cache.cache),
            "hit_rate_after": self.cache.get_hit_rate(),
            "expired_entries_removed": len(expired_keys)
        })
        
        return optimization_results

    def export_performance_data(self, filepath: str) -> None:
        """Export performance data for analysis."""
        if not self.optimization_enabled:
            return
        
        import json
        
        performance_data = {
            "summary": self.get_performance_summary(),
            "recommendations": self.get_optimization_recommendations(),
            "cache_optimization": self.optimize_cache(),
            "performance_history": [
                {
                    "operation": entry["operation"],
                    "timestamp": entry["timestamp"],
                    "response_time": entry["metrics"].response_time,
                    "memory_usage": entry["metrics"].memory_usage,
                    "cpu_usage": entry["metrics"].cpu_usage,
                    "cache_hit_rate": entry["metrics"].cache_hit_rate,
                    "throughput": entry["metrics"].throughput,
                    "error_rate": entry["metrics"].error_rate
                }
                for entry in self.performance_history
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(performance_data, f, indent=2, default=str)
        
        log.info(f"Performance data exported to {filepath}")


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()
