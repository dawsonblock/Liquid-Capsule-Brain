"""Advanced monitoring dashboard with real-time metrics and alerting."""

import asyncio
import json
import logging
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import psutil

log = logging.getLogger(__name__)


@dataclass
class Metric:
    """Metric data structure."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class Alert:
    """Alert data structure."""
    alert_id: str
    metric_name: str
    severity: str
    message: str
    timestamp: float
    threshold: float
    current_value: float
    resolved: bool = False
    resolved_at: Optional[float] = None


@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    refresh_interval: float = 5.0
    max_metrics_history: int = 1000
    alert_cooldown: float = 300.0  # 5 minutes
    enabled: bool = True


class MetricsCollector:
    """Advanced metrics collection system."""

    def __init__(self):
        """Initialize metrics collector."""
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.collection_enabled = True
        self.collection_interval = 5.0  # seconds
        
    def collect_system_metrics(self) -> List[Metric]:
        """Collect system metrics."""
        if not self.collection_enabled:
            return []
        
        current_time = time.time()
        metrics = []
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(Metric("cpu.usage", cpu_percent, current_time, unit="percent"))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics.append(Metric("memory.usage", memory.percent, current_time, unit="percent"))
            metrics.append(Metric("memory.available", memory.available / 1024 / 1024, current_time, unit="MB"))
            metrics.append(Metric("memory.used", memory.used / 1024 / 1024, current_time, unit="MB"))
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics.append(Metric("disk.usage", disk.percent, current_time, unit="percent"))
            metrics.append(Metric("disk.free", disk.free / 1024 / 1024, current_time, unit="MB"))
            
            # Process metrics
            process = psutil.Process()
            metrics.append(Metric("process.memory", process.memory_info().rss / 1024 / 1024, current_time, unit="MB"))
            metrics.append(Metric("process.cpu", process.cpu_percent(), current_time, unit="percent"))
            
            # Network metrics
            network = psutil.net_io_counters()
            metrics.append(Metric("network.bytes_sent", network.bytes_sent / 1024 / 1024, current_time, unit="MB"))
            metrics.append(Metric("network.bytes_recv", network.bytes_recv / 1024 / 1024, current_time, unit="MB"))
            
        except Exception as e:
            log.error(f"Error collecting system metrics: {e}")
        
        return metrics
    
    def collect_application_metrics(self) -> List[Metric]:
        """Collect application-specific metrics."""
        if not self.collection_enabled:
            return []
        
        current_time = time.time()
        metrics = []
        
        try:
            # Application-specific metrics would go here
            # For now, we'll add some placeholder metrics
            
            # Active connections (placeholder)
            metrics.append(Metric("app.active_connections", 0, current_time, unit="count"))
            
            # Request rate (placeholder)
            metrics.append(Metric("app.request_rate", 0, current_time, unit="requests/sec"))
            
            # Error rate (placeholder)
            metrics.append(Metric("app.error_rate", 0, current_time, unit="errors/sec"))
            
        except Exception as e:
            log.error(f"Error collecting application metrics: {e}")
        
        return metrics
    
    def store_metrics(self, metrics: List[Metric]) -> None:
        """Store metrics in history."""
        for metric in metrics:
            self.metrics_history[metric.name].append(metric)
    
    def get_metric_history(self, metric_name: str, limit: int = 100) -> List[Metric]:
        """Get metric history."""
        return list(self.metrics_history.get(metric_name, []))[-limit:]
    
    def get_metric_summary(self, metric_name: str) -> Dict[str, Any]:
        """Get metric summary statistics."""
        history = self.metrics_history.get(metric_name, [])
        
        if not history:
            return {"metric_name": metric_name, "count": 0}
        
        values = [m.value for m in history]
        
        return {
            "metric_name": metric_name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "unit": history[-1].unit if history else ""
        }


class AlertManager:
    """Advanced alerting system."""

    def __init__(self):
        """Initialize alert manager."""
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.alert_cooldowns: Dict[str, float] = {}
        
        # Load default alert rules
        self._load_default_rules()
        
        log.info("Alert Manager initialized")

    def _load_default_rules(self) -> None:
        """Load default alert rules."""
        default_rules = {
            "high_cpu": {
                "metric": "cpu.usage",
                "threshold": 80.0,
                "severity": "warning",
                "message": "High CPU usage detected"
            },
            "high_memory": {
                "metric": "memory.usage",
                "threshold": 85.0,
                "severity": "warning",
                "message": "High memory usage detected"
            },
            "critical_memory": {
                "metric": "memory.usage",
                "threshold": 95.0,
                "severity": "critical",
                "message": "Critical memory usage detected"
            },
            "high_disk": {
                "metric": "disk.usage",
                "threshold": 90.0,
                "severity": "warning",
                "message": "High disk usage detected"
            }
        }
        
        self.alert_rules.update(default_rules)

    def check_alerts(self, metrics: List[Metric]) -> List[Alert]:
        """Check metrics against alert rules."""
        new_alerts = []
        current_time = time.time()
        
        for metric in metrics:
            for rule_name, rule in self.alert_rules.items():
                if metric.name != rule["metric"]:
                    continue
                
                # Check if alert is in cooldown
                cooldown_key = f"{rule_name}_{metric.name}"
                if cooldown_key in self.alert_cooldowns:
                    if current_time - self.alert_cooldowns[cooldown_key] < 300:  # 5 minute cooldown
                        continue
                
                # Check threshold
                if metric.value >= rule["threshold"]:
                    alert_id = f"{rule_name}_{int(current_time * 1000)}"
                    
                    # Check if alert already exists and is unresolved
                    existing_alert = None
                    for alert in self.alerts.values():
                        if (alert.metric_name == metric.name and 
                            alert.severity == rule["severity"] and 
                            not alert.resolved):
                            existing_alert = alert
                            break
                    
                    if existing_alert:
                        # Update existing alert
                        existing_alert.current_value = metric.value
                        existing_alert.timestamp = current_time
                    else:
                        # Create new alert
                        alert = Alert(
                            alert_id=alert_id,
                            metric_name=metric.name,
                            severity=rule["severity"],
                            message=rule["message"],
                            timestamp=current_time,
                            threshold=rule["threshold"],
                            current_value=metric.value
                        )
                        
                        self.alerts[alert_id] = alert
                        self.alert_history.append(alert)
                        new_alerts.append(alert)
                        
                        # Set cooldown
                        self.alert_cooldowns[cooldown_key] = current_time
                        
                        log.warning(f"Alert triggered: {alert.message} (value: {metric.value}, threshold: {rule['threshold']})")
        
        return new_alerts

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = time.time()
        
        log.info(f"Alert resolved: {alert.message}")
        return True

    def get_active_alerts(self) -> List[Alert]:
        """Get active (unresolved) alerts."""
        return [alert for alert in self.alerts.values() if not alert.resolved]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary."""
        active_alerts = self.get_active_alerts()
        
        alerts_by_severity = defaultdict(int)
        for alert in active_alerts:
            alerts_by_severity[alert.severity] += 1
        
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len(active_alerts),
            "alerts_by_severity": dict(alerts_by_severity),
            "total_rules": len(self.alert_rules)
        }


class MonitoringDashboard:
    """Advanced monitoring dashboard."""

    def __init__(self):
        """Initialize monitoring dashboard."""
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.config = DashboardConfig()
        self.collection_task: Optional[asyncio.Task] = None
        self.dashboard_enabled = os.getenv("MONITORING_DASHBOARD_ENABLED", "true").lower() == "true"
        
        log.info("Monitoring Dashboard initialized")

    async def start_collection(self) -> None:
        """Start metrics collection."""
        if not self.dashboard_enabled or self.collection_task:
            return
        
        self.collection_task = asyncio.create_task(self._collection_loop())
        log.info("Metrics collection started")

    async def stop_collection(self) -> None:
        """Stop metrics collection."""
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
            self.collection_task = None
            log.info("Metrics collection stopped")

    async def _collection_loop(self) -> None:
        """Main collection loop."""
        while True:
            try:
                # Collect metrics
                system_metrics = self.metrics_collector.collect_system_metrics()
                app_metrics = self.metrics_collector.collect_application_metrics()
                
                all_metrics = system_metrics + app_metrics
                
                # Store metrics
                self.metrics_collector.store_metrics(all_metrics)
                
                # Check alerts
                new_alerts = self.alert_manager.check_alerts(all_metrics)
                
                # Wait for next collection
                await asyncio.sleep(self.config.refresh_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Error in collection loop: {e}")
                await asyncio.sleep(self.config.refresh_interval)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        if not self.dashboard_enabled:
            return {"dashboard_enabled": False}
        
        # Get current metrics
        current_metrics = self.metrics_collector.collect_system_metrics()
        
        # Get metric summaries
        metric_summaries = {}
        for metric in current_metrics:
            metric_summaries[metric.name] = self.metrics_collector.get_metric_summary(metric.name)
        
        # Get alerts
        active_alerts = self.alert_manager.get_active_alerts()
        alert_summary = self.alert_manager.get_alert_summary()
        
        return {
            "dashboard_enabled": self.dashboard_enabled,
            "timestamp": time.time(),
            "current_metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "tags": m.tags
                }
                for m in current_metrics
            ],
            "metric_summaries": metric_summaries,
            "active_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "metric_name": alert.metric_name,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                    "threshold": alert.threshold,
                    "current_value": alert.current_value
                }
                for alert in active_alerts
            ],
            "alert_summary": alert_summary,
            "collection_status": {
                "running": self.collection_task is not None and not self.collection_task.done(),
                "interval": self.config.refresh_interval
            }
        }

    def get_metric_history(self, metric_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get metric history for charts."""
        history = self.metrics_collector.get_metric_history(metric_name, limit)
        
        return [
            {
                "timestamp": m.timestamp,
                "value": m.value,
                "unit": m.unit
            }
            for m in history
        ]

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        if not self.dashboard_enabled:
            return {"status": "disabled"}
        
        # Get current metrics
        current_metrics = self.metrics_collector.collect_system_metrics()
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        for metric in current_metrics:
            if metric.name == "cpu.usage" and metric.value > 80:
                health_status = "warning"
                issues.append(f"High CPU usage: {metric.value:.1f}%")
            elif metric.name == "memory.usage" and metric.value > 85:
                health_status = "warning"
                issues.append(f"High memory usage: {metric.value:.1f}%")
            elif metric.name == "disk.usage" and metric.value > 90:
                health_status = "critical"
                issues.append(f"High disk usage: {metric.value:.1f}%")
        
        # Check for critical alerts
        active_alerts = self.alert_manager.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.severity == "critical"]
        
        if critical_alerts:
            health_status = "critical"
            issues.append(f"{len(critical_alerts)} critical alerts active")
        
        return {
            "status": health_status,
            "issues": issues,
            "timestamp": time.time(),
            "metrics_count": len(current_metrics),
            "active_alerts_count": len(active_alerts)
        }

    def export_dashboard_data(self, filepath: str) -> None:
        """Export dashboard data for analysis."""
        if not self.dashboard_enabled:
            return
        
        dashboard_data = {
            "dashboard_data": self.get_dashboard_data(),
            "health_status": self.get_health_status(),
            "metric_histories": {
                metric_name: self.get_metric_history(metric_name, 100)
                for metric_name in self.metrics_collector.metrics_history.keys()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        
        log.info(f"Dashboard data exported to {filepath}")


# Global monitoring dashboard instance
monitoring_dashboard = MonitoringDashboard()
