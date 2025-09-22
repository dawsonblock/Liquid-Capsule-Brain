"""Advanced debugging system that integrates all debugging tools."""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any

from .debugger import Debugger
from .error_tracker import error_tracker
from .health_checker import health_checker
from .memory_monitor import memory_monitor
from .performance_monitor import performance_monitor
from .profiler import Profiler

log = logging.getLogger(__name__)


class AdvancedDebugger:
    """Advanced debugging system that integrates all debugging tools."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.debugger = Debugger()
        self.profiler = Profiler()
        self.memory_monitor = memory_monitor
        self.error_tracker = error_tracker
        self.performance_monitor = performance_monitor
        self.health_checker = health_checker

        # Integration settings
        self.auto_health_checks = True
        self.auto_memory_monitoring = True
        self.auto_performance_monitoring = True
        self.auto_error_tracking = True
        self._health_checks_pending = False

        # Debugging session data
        self.session_start = datetime.now()
        self.session_data: dict[str, Any] = {}

        if self.enabled:
            self._initialize_debugging()

    def _initialize_debugging(self) -> None:
        """Initialize all debugging components."""
        try:
            # Enable memory monitoring
            if self.auto_memory_monitoring:
                self.memory_monitor.enable()

            # Start health checking (will be started when event loop is available)
            if self.auto_health_checks:
                # Store flag to start health checks when event loop is available
                self._health_checks_pending = True

            # Set up performance monitoring thresholds
            self.performance_monitor.set_threshold("response_time", warning=1.0, critical=5.0)
            self.performance_monitor.set_threshold("memory_usage", warning=100*1024*1024, critical=500*1024*1024)

            log.info("Advanced debugging system initialized")
        except Exception as e:
            log.error(f"Failed to initialize debugging system: {e}")

    async def run_comprehensive_analysis(self) -> dict[str, Any]:
        """Run comprehensive system analysis."""
        if not self.enabled:
            return {"error": "Debugging system disabled"}

        # Start health checks if pending
        if self._health_checks_pending:
            await self.health_checker.start_auto_checks()
            self._health_checks_pending = False

        log.info("Starting comprehensive system analysis")
        start_time = time.time()

        try:
            # Run all health checks
            health_results = await self.health_checker.run_all_checks()
            health_summary = self.health_checker.get_health_summary()

            # Get performance overview
            performance_overview = self.performance_monitor.get_performance_overview()
            performance_score = self.performance_monitor.get_performance_score()

            # Get error summary
            error_summary = self.error_tracker.get_error_summary()
            error_health = self.error_tracker.get_health_score()

            # Get memory statistics
            memory_stats = self.memory_monitor.get_memory_stats()
            memory_trend = self.memory_monitor.get_memory_trend()

            # Detect memory leaks
            memory_leaks = self.memory_monitor.detect_memory_leaks()

            # Get profiling data
            profiling_data = self.profiler.get_profiling_summary()

            # Calculate overall system health
            overall_health = self._calculate_overall_health(
                health_summary, performance_score, error_health
            )

            analysis = {
                "timestamp": datetime.now().isoformat(),
                "session_duration": (datetime.now() - self.session_start).total_seconds(),
                "overall_health": overall_health,
                "health_checks": {
                    "summary": health_summary,
                    "results": [
                        {
                            "name": r.name,
                            "status": r.status,
                            "message": r.message,
                            "component": r.component,
                            "details": r.details
                        }
                        for r in health_results
                    ]
                },
                "performance": {
                    "overview": performance_overview,
                    "score": performance_score,
                    "alerts": self.performance_monitor.get_alerts(hours=1)
                },
                "errors": {
                    "summary": error_summary,
                    "health_score": error_health,
                    "recent_errors": self.error_tracker.get_errors_by_time_range(
                        datetime.now() - timedelta(hours=1),
                        datetime.now()
                    )
                },
                "memory": {
                    "stats": memory_stats,
                    "trend": memory_trend[-10:] if memory_trend else [],
                    "leaks": memory_leaks,
                    "top_consumers": self.memory_monitor.get_top_memory_consumers()
                },
                "profiling": profiling_data,
                "recommendations": self._generate_recommendations(
                    health_summary, performance_score, error_health, memory_leaks
                )
            }

            duration = time.time() - start_time
            log.info(f"Comprehensive analysis completed in {duration:.2f} seconds")

            return analysis

        except Exception as e:
            log.error(f"Comprehensive analysis failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _calculate_overall_health(
        self,
        health_summary: dict[str, Any],
        performance_score: dict[str, Any],
        error_health: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate overall system health score."""
        # Health check score (0-100)
        health_score = 100
        if health_summary["status"] == "critical":
            health_score = 20
        elif health_summary["status"] == "warning":
            health_score = 60
        elif health_summary["status"] == "healthy":
            health_score = 100

        # Performance score (already 0-100)
        perf_score = performance_score.get("score", 50)

        # Error health score (already 0-100)
        error_score = error_health.get("score", 50)

        # Weighted average
        overall_score = (health_score * 0.4 + perf_score * 0.3 + error_score * 0.3)

        if overall_score >= 90:
            status = "excellent"
        elif overall_score >= 70:
            status = "good"
        elif overall_score >= 50:
            status = "fair"
        elif overall_score >= 30:
            status = "poor"
        else:
            status = "critical"

        return {
            "score": round(overall_score, 2),
            "status": status,
            "breakdown": {
                "health_checks": health_score,
                "performance": perf_score,
                "errors": error_score
            }
        }

    def _generate_recommendations(
        self,
        health_summary: dict[str, Any],
        performance_score: dict[str, Any],
        error_health: dict[str, Any],
        memory_leaks: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Generate system improvement recommendations."""
        recommendations = []

        # Health check recommendations
        if health_summary["status"] == "critical":
            recommendations.append({
                "category": "health",
                "priority": "high",
                "title": "Critical Health Issues",
                "description": f"System has {health_summary.get('critical', 0)} critical health issues that need immediate attention."
            })

        # Performance recommendations
        if performance_score["score"] < 70:
            recommendations.append({
                "category": "performance",
                "priority": "medium",
                "title": "Performance Optimization",
                "description": f"System performance score is {performance_score['score']}. Consider optimizing slow operations."
            })

        # Error recommendations
        if error_health["score"] < 80:
            recommendations.append({
                "category": "errors",
                "priority": "high",
                "title": "Error Rate High",
                "description": f"Error health score is {error_health['score']}. Review and fix frequent errors."
            })

        # Memory leak recommendations
        if memory_leaks:
            recommendations.append({
                "category": "memory",
                "priority": "high",
                "title": "Memory Leaks Detected",
                "description": f"Detected {len(memory_leaks)} potential memory leaks. Review object lifecycle management."
            })

        # Memory usage recommendations
        memory_stats = self.memory_monitor.get_memory_stats()
        if memory_stats.get("traced_current", 0) > 200 * 1024 * 1024:  # 200MB
            recommendations.append({
                "category": "memory",
                "priority": "medium",
                "title": "High Memory Usage",
                "description": "Memory usage is high. Consider implementing memory optimization strategies."
            })

        return recommendations

    async def debug_issue(
        self,
        issue_description: str,
        context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Debug a specific issue with comprehensive analysis."""
        if not self.enabled:
            return {"error": "Debugging system disabled"}

        log.info(f"Debugging issue: {issue_description}")

        try:
            # Take memory snapshot before debugging
            self.memory_monitor.take_snapshot("debug_start")

            # Run health checks
            health_results = await self.health_checker.run_all_checks()

            # Get recent errors related to the issue
            recent_errors = self.error_tracker.get_errors_by_time_range(
                datetime.now() - timedelta(hours=24),
                datetime.now()
            )

            # Get performance metrics
            performance_data = self.performance_monitor.get_recent_metrics(minutes=60)

            # Analyze memory usage
            memory_analysis = self.memory_monitor.analyze_memory_patterns()

            # Take memory snapshot after analysis
            self.memory_monitor.take_snapshot("debug_end")

            debug_result = {
                "issue_description": issue_description,
                "context": context or {},
                "timestamp": datetime.now().isoformat(),
                "health_status": self.health_checker.get_health_summary(),
                "recent_errors": recent_errors,
                "performance_metrics": performance_data,
                "memory_analysis": memory_analysis,
                "memory_snapshots": self.memory_monitor.get_memory_trend()[-2:],
                "recommendations": self._generate_issue_recommendations(
                    issue_description, health_results, recent_errors
                )
            }

            return debug_result

        except Exception as e:
            log.error(f"Issue debugging failed: {e}")
            return {
                "error": str(e),
                "issue_description": issue_description,
                "timestamp": datetime.now().isoformat()
            }

    def _generate_issue_recommendations(
        self,
        issue_description: str,
        health_results: list[Any],
        recent_errors: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Generate specific recommendations for an issue."""
        recommendations = []

        # Analyze health results
        critical_issues = [r for r in health_results if r.status == "critical"]
        if critical_issues:
            recommendations.append({
                "priority": "critical",
                "title": "Address Critical Health Issues",
                "description": f"Found {len(critical_issues)} critical health issues that may be related to the problem."
            })

        # Analyze recent errors
        error_patterns = {}
        for error in recent_errors:
            error_type = error.get("error_type", "Unknown")
            error_patterns[error_type] = error_patterns.get(error_type, 0) + 1

        if error_patterns:
            most_common_error = max(error_patterns.items(), key=lambda x: x[1])
            recommendations.append({
                "priority": "high",
                "title": "Investigate Common Errors",
                "description": f"Most common error type: {most_common_error[0]} ({most_common_error[1]} occurrences). This may be related to the issue."
            })

        # Generic recommendations based on issue description
        if "memory" in issue_description.lower():
            recommendations.append({
                "priority": "medium",
                "title": "Memory Analysis",
                "description": "Run memory leak detection and analyze memory usage patterns."
            })

        if "performance" in issue_description.lower() or "slow" in issue_description.lower():
            recommendations.append({
                "priority": "medium",
                "title": "Performance Profiling",
                "description": "Use the profiler to identify performance bottlenecks."
            })

        return recommendations

    def get_debugging_dashboard(self) -> dict[str, Any]:
        """Get comprehensive debugging dashboard data."""
        if not self.enabled:
            return {"error": "Debugging system disabled"}

        return {
            "timestamp": datetime.now().isoformat(),
            "session_duration": (datetime.now() - self.session_start).total_seconds(),
            "health": self.health_checker.get_health_summary(),
            "performance": self.performance_monitor.get_performance_score(),
            "errors": self.error_tracker.get_error_summary(),
            "memory": self.memory_monitor.get_memory_stats(),
            "profiling": {"status": "profiler_available", "enabled": True},
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": os.getcwd()
            }
        }

    def export_debugging_data(self, filepath: str) -> None:
        """Export all debugging data to a file."""
        if not self.enabled:
            return

        data = {
            "session_info": {
                "start_time": self.session_start.isoformat(),
                "duration": (datetime.now() - self.session_start).total_seconds(),
                "enabled": self.enabled
            },
            "health_data": self.health_checker.get_health_summary(),
            "performance_data": self.performance_monitor.get_performance_overview(),
            "error_data": self.error_tracker.get_error_summary(),
            "memory_data": self.memory_monitor.get_memory_stats(),
            "profiling_data": self.profiler.get_profiling_summary(),
            "export_timestamp": datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        log.info(f"Debugging data exported to {filepath}")

    def enable(self) -> None:
        """Enable the debugging system."""
        self.enabled = True
        self._initialize_debugging()
        log.info("Advanced debugging system enabled")

    def disable(self) -> None:
        """Disable the debugging system."""
        self.enabled = False
        self.memory_monitor.disable()
        asyncio.create_task(self.health_checker.stop_auto_checks())
        log.info("Advanced debugging system disabled")

    def get_status(self) -> dict[str, Any]:
        """Get debugging system status."""
        return {
            "enabled": self.enabled,
            "auto_health_checks": self.auto_health_checks,
            "auto_memory_monitoring": self.auto_memory_monitoring,
            "auto_performance_monitoring": self.auto_performance_monitoring,
            "auto_error_tracking": self.auto_error_tracking,
            "session_duration": (datetime.now() - self.session_start).total_seconds(),
            "components": {
                "debugger": {"enabled": True, "status": "active"},
                "profiler": {"enabled": True, "status": "active"},
                "memory_monitor": self.memory_monitor.get_summary(),
                "error_tracker": self.error_tracker.get_error_summary(),
                "performance_monitor": self.performance_monitor.get_performance_score(),
                "health_checker": self.health_checker.get_health_summary()
            }
        }


# Global advanced debugger instance
advanced_debugger = AdvancedDebugger(enabled=True)
