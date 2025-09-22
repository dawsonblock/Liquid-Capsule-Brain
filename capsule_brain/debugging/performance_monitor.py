"""Performance monitoring and optimization system."""

import asyncio
import functools
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
import statistics
import threading
from collections import defaultdict, deque

log = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    timestamp: datetime
    component: str
    metadata: Dict[str, Any] = None


@dataclass
class PerformanceAlert:
    """Performance alert data structure."""
    metric_name: str
    threshold: float
    actual_value: float
    severity: str
    timestamp: datetime
    component: str
    message: str


class PerformanceMonitor:
    """Advanced performance monitoring and optimization system."""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.alerts: List[PerformanceAlert] = []
        self.thresholds: Dict[str, Dict[str, float]] = {}
        self.baselines: Dict[str, float] = {}
        self.performance_history: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
        
        # Default thresholds
        self.set_default_thresholds()
        
    def set_default_thresholds(self) -> None:
        """Set default performance thresholds."""
        self.thresholds = {
            "response_time": {
                "warning": 1.0,  # 1 second
                "critical": 5.0  # 5 seconds
            },
            "memory_usage": {
                "warning": 100 * 1024 * 1024,  # 100MB
                "critical": 500 * 1024 * 1024   # 500MB
            },
            "cpu_usage": {
                "warning": 80.0,  # 80%
                "critical": 95.0  # 95%
            },
            "error_rate": {
                "warning": 0.05,  # 5%
                "critical": 0.20  # 20%
            },
            "throughput": {
                "warning": 10.0,  # 10 requests/second
                "critical": 1.0   # 1 request/second
            }
        }
    
    def record_metric(
        self,
        name: str,
        value: float,
        component: str = "unknown",
        metadata: Dict[str, Any] = None
    ) -> None:
        """Record a performance metric."""
        with self.lock:
            metric = PerformanceMetric(
                name=name,
                value=value,
                timestamp=datetime.now(),
                component=component,
                metadata=metadata or {}
            )
            
            self.metrics.append(metric)
            self.performance_history[name].append(value)
            
            # Keep only recent history
            if len(self.performance_history[name]) > 1000:
                self.performance_history[name] = self.performance_history[name][-1000:]
            
            # Check thresholds
            self._check_thresholds(metric)
    
    def _check_thresholds(self, metric: PerformanceMetric) -> None:
        """Check if metric exceeds thresholds."""
        if metric.name not in self.thresholds:
            return
        
        thresholds = self.thresholds[metric.name]
        value = metric.value
        
        # Check critical threshold
        if "critical" in thresholds and value >= thresholds["critical"]:
            self._create_alert(
                metric, "critical", thresholds["critical"], value
            )
        # Check warning threshold
        elif "warning" in thresholds and value >= thresholds["warning"]:
            self._create_alert(
                metric, "warning", thresholds["warning"], value
            )
    
    def _create_alert(
        self, 
        metric: PerformanceMetric, 
        severity: str, 
        threshold: float, 
        actual_value: float
    ) -> None:
        """Create a performance alert."""
        alert = PerformanceAlert(
            metric_name=metric.name,
            threshold=threshold,
            actual_value=actual_value,
            severity=severity,
            timestamp=datetime.now(),
            component=metric.component,
            message=f"{metric.name} exceeded {severity} threshold: {actual_value} >= {threshold}"
        )
        
        self.alerts.append(alert)
        log.warning(f"Performance alert: {alert.message}")
    
    def set_threshold(
        self, 
        metric_name: str, 
        warning: float = None, 
        critical: float = None
    ) -> None:
        """Set custom thresholds for a metric."""
        if metric_name not in self.thresholds:
            self.thresholds[metric_name] = {}
        
        if warning is not None:
            self.thresholds[metric_name]["warning"] = warning
        if critical is not None:
            self.thresholds[metric_name]["critical"] = critical
        
        log.info(f"Thresholds set for {metric_name}: warning={warning}, critical={critical}")
    
    def get_metric_summary(self, metric_name: str) -> Dict[str, Any]:
        """Get summary statistics for a metric."""
        if metric_name not in self.performance_history:
            return {"error": "Metric not found"}
        
        values = self.performance_history[metric_name]
        if not values:
            return {"error": "No data available"}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "percentile_95": self._percentile(values, 95),
            "percentile_99": self._percentile(values, 99),
            "recent_trend": self._calculate_trend(values[-10:]) if len(values) >= 10 else None
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from recent values."""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple linear regression slope
        n = len(values)
        x = list(range(n))
        y = values
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def get_performance_overview(self) -> Dict[str, Any]:
        """Get overall performance overview."""
        with self.lock:
            if not self.metrics:
                return {"error": "No metrics available"}
            
            # Get unique metric names
            metric_names = list(set(m.name for m in self.metrics))
            
            overview = {
                "total_metrics": len(self.metrics),
                "metric_types": len(metric_names),
                "active_alerts": len([a for a in self.alerts if a.timestamp > datetime.now() - timedelta(hours=1)]),
                "metrics": {}
            }
            
            # Calculate summary for each metric
            for metric_name in metric_names:
                overview["metrics"][metric_name] = self.get_metric_summary(metric_name)
            
            return overview
    
    def get_recent_metrics(
        self, 
        metric_name: str = None, 
        component: str = None,
        minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Get recent metrics with optional filtering."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            filtered_metrics = [
                m for m in self.metrics
                if (m.timestamp > cutoff_time and
                    (metric_name is None or m.name == metric_name) and
                    (component is None or m.component == component))
            ]
            
            return [
                {
                    "name": m.name,
                    "value": m.value,
                    "timestamp": m.timestamp.isoformat(),
                    "component": m.component,
                    "metadata": m.metadata
                }
                for m in filtered_metrics
            ]
    
    def get_alerts(
        self, 
        severity: str = None, 
        component: str = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get performance alerts with optional filtering."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_alerts = [
            a for a in self.alerts
            if (a.timestamp > cutoff_time and
                (severity is None or a.severity == severity) and
                (component is None or a.component == component))
        ]
        
        return [
            {
                "metric_name": a.metric_name,
                "threshold": a.threshold,
                "actual_value": a.actual_value,
                "severity": a.severity,
                "timestamp": a.timestamp.isoformat(),
                "component": a.component,
                "message": a.message
            }
            for a in filtered_alerts
        ]
    
    def calculate_baseline(self, metric_name: str, days: int = 7) -> float:
        """Calculate baseline performance for a metric."""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self.lock:
            recent_values = [
                m.value for m in self.metrics
                if m.name == metric_name and m.timestamp > cutoff_time
            ]
        
        if not recent_values:
            return 0
        
        # Use 95th percentile as baseline (excluding outliers)
        baseline = self._percentile(recent_values, 95)
        self.baselines[metric_name] = baseline
        
        log.info(f"Baseline calculated for {metric_name}: {baseline}")
        return baseline
    
    def get_performance_score(self) -> Dict[str, Any]:
        """Calculate overall performance score."""
        if not self.metrics:
            return {"score": 0, "status": "no_data"}
        
        # Get recent metrics (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"score": 0, "status": "no_recent_data"}
        
        # Calculate score based on threshold violations
        total_metrics = len(recent_metrics)
        violations = 0
        
        for metric in recent_metrics:
            if metric.name in self.thresholds:
                thresholds = self.thresholds[metric.name]
                if "critical" in thresholds and metric.value >= thresholds["critical"]:
                    violations += 2  # Critical violations count double
                elif "warning" in thresholds and metric.value >= thresholds["warning"]:
                    violations += 1
        
        # Calculate score (0-100)
        if total_metrics == 0:
            score = 100
        else:
            score = max(0, 100 - (violations / total_metrics) * 100)
        
        # Determine status
        if score >= 90:
            status = "excellent"
        elif score >= 70:
            status = "good"
        elif score >= 50:
            status = "fair"
        elif score >= 30:
            status = "poor"
        else:
            status = "critical"
        
        return {
            "score": round(score, 2),
            "status": status,
            "total_metrics": total_metrics,
            "violations": violations,
            "violation_rate": round(violations / total_metrics * 100, 2) if total_metrics > 0 else 0
        }
    
    def clear_old_data(self, days: int = 30) -> int:
        """Clear old metrics and alerts."""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self.lock:
            # Clear old metrics
            original_count = len(self.metrics)
            self.metrics = deque(
                [m for m in self.metrics if m.timestamp > cutoff_time],
                maxlen=self.max_metrics
            )
            metrics_cleared = original_count - len(self.metrics)
            
            # Clear old alerts
            original_alerts = len(self.alerts)
            self.alerts = [a for a in self.alerts if a.timestamp > cutoff_time]
            alerts_cleared = original_alerts - len(self.alerts)
        
        total_cleared = metrics_cleared + alerts_cleared
        log.info(f"Cleared {total_cleared} old performance records")
        return total_cleared
    
    def export_data(self, filepath: str) -> None:
        """Export performance data to file."""
        import json
        
        with self.lock:
            data = {
                "metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "timestamp": m.timestamp.isoformat(),
                        "component": m.component,
                        "metadata": m.metadata
                    }
                    for m in self.metrics
                ],
                "alerts": [
                    {
                        "metric_name": a.metric_name,
                        "threshold": a.threshold,
                        "actual_value": a.actual_value,
                        "severity": a.severity,
                        "timestamp": a.timestamp.isoformat(),
                        "component": a.component,
                        "message": a.message
                    }
                    for a in self.alerts
                ],
                "thresholds": self.thresholds,
                "baselines": self.baselines,
                "export_timestamp": datetime.now().isoformat()
            }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        log.info(f"Performance data exported to {filepath}")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(metric_name: str, component: str = "unknown") -> Callable:
    """Decorator to monitor function performance."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                performance_monitor.record_metric(
                    metric_name, duration, component
                )
                return result
            except Exception:
                duration = time.time() - start_time
                performance_monitor.record_metric(
                    f"{metric_name}_error", duration, component
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                performance_monitor.record_metric(
                    metric_name, duration, component
                )
                return result
            except Exception:
                duration = time.time() - start_time
                performance_monitor.record_metric(
                    f"{metric_name}_error", duration, component
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def record_metric(name: str, value: float, component: str = "unknown", **metadata) -> None:
    """Convenience function to record a metric."""
    performance_monitor.record_metric(name, value, component, metadata)
