"""Advanced error tracking and analysis system."""

import json
import logging
import sys
import traceback
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

log = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""

    SYSTEM = "system"
    API = "api"
    DATABASE = "database"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    UNKNOWN = "unknown"


class ErrorTracker:
    """Advanced error tracking and analysis system."""

    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self.errors: list[dict[str, Any]] = []
        self.error_patterns: dict[str, dict[str, Any]] = {}
        self.error_rates: dict[str, float] = {}
        self.alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,  # Alert immediately
            ErrorSeverity.HIGH: 5,  # Alert after 5 occurrences
            ErrorSeverity.MEDIUM: 20,  # Alert after 20 occurrences
            ErrorSeverity.LOW: 100,  # Alert after 100 occurrences
        }
        self.rate_window = timedelta(minutes=5)  # 5-minute window for rate calculation

    def track_error(
        self,
        error: Exception,
        context: dict[str, Any] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        user_id: str = None,
        request_id: str = None,
        component: str = None,
    ) -> str:
        """Track an error with full context."""
        error_id = self._generate_error_id()

        error_data = {
            "id": error_id,
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "severity": severity.value,
            "category": category.value,
            "component": component or "unknown",
            "user_id": user_id,
            "request_id": request_id,
            "context": context or {},
            "traceback": traceback.format_exc(),
            "stack_trace": self._get_stack_trace(),
            "system_info": self._get_system_info(),
        }

        self.errors.append(error_data)

        # Keep only recent errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors :]

        # Update patterns and rates
        self._update_error_patterns(error_data)
        self._update_error_rates(error_data)

        # Check for alerts
        self._check_alerts(error_data)

        log.error(f"Error tracked: {error_id} - {error}")
        return error_id

    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"ERR_{timestamp}_{len(self.errors)}"

    def _get_stack_trace(self) -> list[dict[str, str]]:
        """Get current stack trace as structured data."""
        stack = []
        exc_tb = sys.exc_info()[2]

        if exc_tb is None:
            # Called outside exception context, use current stack
            frames = traceback.extract_stack()
        else:
            # Called within exception context, use exception traceback
            frames = traceback.extract_tb(exc_tb)

        for frame in frames:
            stack.append(
                {
                    "filename": frame.filename,
                    "line_number": frame.lineno,
                    "function_name": frame.name,
                    "code": frame.line,
                }
            )
        return stack

    def _get_system_info(self) -> dict[str, Any]:
        """Get current system information."""
        return {
            "python_version": sys.version,
            "platform": sys.platform,
            "executable": sys.executable,
            "argv": sys.argv,
        }

    def _update_error_patterns(self, error_data: dict[str, Any]) -> None:
        """Update error patterns for analysis."""
        pattern_key = f"{error_data['error_type']}:{error_data['component']}"

        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = {
                "count": 0,
                "first_seen": error_data["timestamp"],
                "last_seen": error_data["timestamp"],
                "severity_counts": {s.value: 0 for s in ErrorSeverity},
                "components": set(),
                "error_messages": set(),
            }

        pattern = self.error_patterns[pattern_key]
        pattern["count"] += 1
        pattern["last_seen"] = error_data["timestamp"]
        pattern["severity_counts"][error_data["severity"]] += 1
        pattern["components"].add(error_data["component"])
        pattern["error_messages"].add(error_data["error_message"])

    def _update_error_rates(self, error_data: dict[str, Any]) -> None:
        """Update error rates for monitoring."""
        now = datetime.now()
        cutoff_time = now - self.rate_window

        # Count errors in the rate window
        recent_errors = [
            e for e in self.errors if datetime.fromisoformat(e["timestamp"]) > cutoff_time
        ]

        # Calculate rates by component and severity
        for component in {e["component"] for e in recent_errors}:
            component_errors = [e for e in recent_errors if e["component"] == component]
            rate = len(component_errors) / self.rate_window.total_seconds() * 60  # per minute
            self.error_rates[f"{component}_total"] = rate

            for severity in ErrorSeverity:
                severity_errors = [e for e in component_errors if e["severity"] == severity.value]
                severity_rate = len(severity_errors) / self.rate_window.total_seconds() * 60
                self.error_rates[f"{component}_{severity.value}"] = severity_rate

    def _check_alerts(self, error_data: dict[str, Any]) -> None:
        """Check if error should trigger an alert."""
        severity = ErrorSeverity(error_data["severity"])
        threshold = self.alert_thresholds.get(severity, float("inf"))

        # Count recent errors of this severity
        now = datetime.now()
        cutoff_time = now - self.rate_window
        recent_same_severity = [
            e
            for e in self.errors
            if (
                datetime.fromisoformat(e["timestamp"]) > cutoff_time
                and e["severity"] == severity.value
            )
        ]

        if len(recent_same_severity) >= threshold:
            self._trigger_alert(error_data, recent_same_severity)

    def _trigger_alert(
        self, error_data: dict[str, Any], recent_errors: list[dict[str, Any]]
    ) -> None:
        """Trigger an alert for error threshold breach."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "severity": error_data["severity"],
            "component": error_data["component"],
            "error_count": len(recent_errors),
            "threshold": self.alert_thresholds.get(ErrorSeverity(error_data["severity"]), 0),
            "recent_errors": recent_errors[-5:],  # Last 5 errors
        }

        log.critical(f"ERROR ALERT: {alert}")
        # Here you could integrate with external alerting systems

    def get_error_summary(self) -> dict[str, Any]:
        """Get summary of all tracked errors."""
        if not self.errors:
            return {"total_errors": 0}

        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)

        recent_errors = [
            e for e in self.errors if datetime.fromisoformat(e["timestamp"]) > last_hour
        ]

        daily_errors = [e for e in self.errors if datetime.fromisoformat(e["timestamp"]) > last_24h]

        severity_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}
        component_counts: dict[str, int] = {}

        for error in self.errors:
            severity = error["severity"]
            category = error["category"]
            component = error["component"]

            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
            component_counts[component] = component_counts.get(component, 0) + 1

        return {
            "total_errors": len(self.errors),
            "recent_errors_1h": len(recent_errors),
            "recent_errors_24h": len(daily_errors),
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "component_breakdown": component_counts,
            "error_rates": self.error_rates,
            "top_patterns": self._get_top_error_patterns(),
        }

    def _get_top_error_patterns(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top error patterns by frequency."""
        patterns = []
        for pattern_key, pattern_data in self.error_patterns.items():
            patterns.append(
                {
                    "pattern": pattern_key,
                    "count": pattern_data["count"],
                    "first_seen": pattern_data["first_seen"],
                    "last_seen": pattern_data["last_seen"],
                    "severity_breakdown": pattern_data["severity_counts"],
                    "components": list(pattern_data["components"]),
                    "sample_messages": list(pattern_data["error_messages"])[:3],
                }
            )

        return sorted(patterns, key=lambda x: x["count"], reverse=True)[:limit]

    def get_errors_by_component(self, component: str) -> list[dict[str, Any]]:
        """Get all errors for a specific component."""
        return [e for e in self.errors if e["component"] == component]

    def get_errors_by_severity(self, severity: ErrorSeverity) -> list[dict[str, Any]]:
        """Get all errors of a specific severity."""
        return [e for e in self.errors if e["severity"] == severity.value]

    def get_errors_by_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> list[dict[str, Any]]:
        """Get errors within a time range."""
        return [
            e
            for e in self.errors
            if start_time <= datetime.fromisoformat(e["timestamp"]) <= end_time
        ]

    def get_error_trends(self, hours: int = 24) -> dict[str, list[tuple[str, int]]]:
        """Get error trends over time."""
        now = datetime.now()
        start_time = now - timedelta(hours=hours)

        # Group errors by hour
        hourly_counts = {}
        for error in self.errors:
            error_time = datetime.fromisoformat(error["timestamp"])
            if error_time >= start_time:
                hour_key = error_time.strftime("%Y-%m-%d %H:00")
                if hour_key not in hourly_counts:
                    hourly_counts[hour_key] = 0
                hourly_counts[hour_key] += 1

        # Convert to sorted list
        trends = sorted(hourly_counts.items())

        return {"total_errors": trends, "time_range": f"{hours} hours", "data_points": len(trends)}

    def clear_old_errors(self, days: int = 7) -> int:
        """Clear errors older than specified days."""
        cutoff_time = datetime.now() - timedelta(days=days)
        original_count = len(self.errors)

        self.errors = [
            e for e in self.errors if datetime.fromisoformat(e["timestamp"]) > cutoff_time
        ]

        cleared_count = original_count - len(self.errors)
        log.info(f"Cleared {cleared_count} old errors")
        return cleared_count

    def export_errors(self, filepath: str) -> None:
        """Export errors to JSON file."""
        with open(filepath, "w") as f:
            json.dump(
                {
                    "errors": self.errors,
                    "patterns": self.error_patterns,
                    "rates": self.error_rates,
                    "export_timestamp": datetime.now().isoformat(),
                },
                f,
                indent=2,
                default=str,
            )

        log.info(f"Errors exported to {filepath}")

    def get_health_score(self) -> dict[str, Any]:
        """Calculate system health score based on errors."""
        if not self.errors:
            return {"score": 100, "status": "healthy"}

        now = datetime.now()
        last_hour = now - timedelta(hours=1)

        recent_errors = [
            e for e in self.errors if datetime.fromisoformat(e["timestamp"]) > last_hour
        ]

        # Calculate penalty based on error severity and frequency
        penalty = 0
        for error in recent_errors:
            severity = ErrorSeverity(error["severity"])
            if severity == ErrorSeverity.CRITICAL:
                penalty += 20
            elif severity == ErrorSeverity.HIGH:
                penalty += 10
            elif severity == ErrorSeverity.MEDIUM:
                penalty += 5
            else:  # LOW
                penalty += 1

        score = max(0, 100 - penalty)

        if score >= 90:
            status = "healthy"
        elif score >= 70:
            status = "warning"
        elif score >= 50:
            status = "degraded"
        else:
            status = "critical"

        return {
            "score": score,
            "status": status,
            "recent_errors": len(recent_errors),
            "penalty": penalty,
        }


# Global error tracker instance
error_tracker = ErrorTracker()


def track_error(
    error: Exception,
    context: dict[str, Any] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    **kwargs,
) -> str:
    """Convenience function to track an error."""
    return error_tracker.track_error(error, context, severity, category, **kwargs)


def track_api_error(error: Exception, endpoint: str, **kwargs) -> str:
    """Track an API-related error."""
    return error_tracker.track_error(
        error,
        context={"endpoint": endpoint},
        severity=ErrorSeverity.MEDIUM,
        category=ErrorCategory.API,
        component="api",
        **kwargs,
    )


def track_system_error(error: Exception, component: str, **kwargs) -> str:
    """Track a system-related error."""
    return error_tracker.track_error(
        error,
        context={"component": component},
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.SYSTEM,
        component=component,
        **kwargs,
    )
