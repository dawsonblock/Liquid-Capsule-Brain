"""Comprehensive health checking and system monitoring."""

import asyncio
import json
import logging
import os
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import psutil

log = logging.getLogger(__name__)


@dataclass
class HealthCheck:
    """Health check result data structure."""
    name: str
    status: str  # "healthy", "warning", "critical", "unknown"
    message: str
    timestamp: datetime
    component: str
    details: dict[str, Any] = None


class HealthChecker:
    """Comprehensive health checking and system monitoring."""

    def __init__(self):
        self.checks: list[HealthCheck] = []
        self.check_functions: dict[str, callable] = {}
        self.auto_check_interval = 60  # seconds
        self.auto_check_task: asyncio.Task | None = None
        self.is_running = False

        # Register default health checks
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register default health check functions."""
        self.check_functions = {
            "system_resources": self._check_system_resources,
            "python_environment": self._check_python_environment,
            "disk_space": self._check_disk_space,
            "memory_usage": self._check_memory_usage,
            "cpu_usage": self._check_cpu_usage,
            "network_connectivity": self._check_network_connectivity,
            "process_health": self._check_process_health,
            "file_system": self._check_file_system,
            "dependencies": self._check_dependencies
        }

    async def run_all_checks(self) -> list[HealthCheck]:
        """Run all registered health checks."""
        results = []

        for check_name, check_func in self.check_functions.items():
            try:
                result = await check_func()
                results.append(result)
            except Exception as e:
                error_result = HealthCheck(
                    name=check_name,
                    status="critical",
                    message=f"Health check failed: {str(e)}",
                    timestamp=datetime.now(),
                    component="health_checker",
                    details={
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                )
                results.append(error_result)
                log.error(f"Health check {check_name} failed: {e}")

        self.checks.extend(results)

        # Keep only recent checks (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.checks = [c for c in self.checks if c.timestamp > cutoff_time]

        return results

    async def _check_system_resources(self) -> HealthCheck:
        """Check overall system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Determine status based on resource usage
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = "critical"
                message = "System resources critically high"
            elif cpu_percent > 70 or memory.percent > 70 or disk.percent > 70:
                status = "warning"
                message = "System resources moderately high"
            else:
                status = "healthy"
                message = "System resources normal"

            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                timestamp=datetime.now(),
                component="system",
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available": memory.available,
                    "disk_percent": disk.percent,
                    "disk_free": disk.free
                }
            )
        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status="critical",
                message=f"Failed to check system resources: {str(e)}",
                timestamp=datetime.now(),
                component="system"
            )

    async def _check_python_environment(self) -> HealthCheck:
        """Check Python environment health."""
        try:
            python_version = sys.version_info
            python_path = sys.executable

            # Check if we're in a virtual environment
            in_venv = hasattr(sys, 'real_prefix') or (
                hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
            )

            # Check Python version compatibility
            if python_version.major < 3 or python_version.minor < 8:
                status = "warning"
                message = f"Python version {python_version.major}.{python_version.minor} may not be optimal"
            else:
                status = "healthy"
                message = f"Python {python_version.major}.{python_version.minor}.{python_version.micro} environment healthy"

            return HealthCheck(
                name="python_environment",
                status=status,
                message=message,
                timestamp=datetime.now(),
                component="python",
                details={
                    "version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                    "executable": python_path,
                    "in_virtual_env": in_venv,
                    "platform": sys.platform
                }
            )
        except Exception as e:
            return HealthCheck(
                name="python_environment",
                status="critical",
                message=f"Failed to check Python environment: {str(e)}",
                timestamp=datetime.now(),
                component="python"
            )

    async def _check_disk_space(self) -> HealthCheck:
        """Check disk space availability."""
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            total_gb = disk.total / (1024**3)
            percent_free = (disk.free / disk.total) * 100

            if percent_free < 5:
                status = "critical"
                message = f"Disk space critically low: {free_gb:.1f}GB free ({percent_free:.1f}%)"
            elif percent_free < 15:
                status = "warning"
                message = f"Disk space low: {free_gb:.1f}GB free ({percent_free:.1f}%)"
            else:
                status = "healthy"
                message = f"Disk space adequate: {free_gb:.1f}GB free ({percent_free:.1f}%)"

            return HealthCheck(
                name="disk_space",
                status=status,
                message=message,
                timestamp=datetime.now(),
                component="storage",
                details={
                    "free_gb": round(free_gb, 2),
                    "total_gb": round(total_gb, 2),
                    "percent_free": round(percent_free, 2),
                    "used_gb": round((disk.used / (1024**3)), 2)
                }
            )
        except Exception as e:
            return HealthCheck(
                name="disk_space",
                status="critical",
                message=f"Failed to check disk space: {str(e)}",
                timestamp=datetime.now(),
                component="storage"
            )

    async def _check_memory_usage(self) -> HealthCheck:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            memory_gb = memory.total / (1024**3)
            memory_used_gb = memory.used / (1024**3)
            memory_percent = memory.percent

            if memory_percent > 90:
                status = "critical"
                message = f"Memory usage critically high: {memory_percent:.1f}%"
            elif memory_percent > 75:
                status = "warning"
                message = f"Memory usage high: {memory_percent:.1f}%"
            else:
                status = "healthy"
                message = f"Memory usage normal: {memory_percent:.1f}%"

            return HealthCheck(
                name="memory_usage",
                status=status,
                message=message,
                timestamp=datetime.now(),
                component="memory",
                details={
                    "total_gb": round(memory_gb, 2),
                    "used_gb": round(memory_used_gb, 2),
                    "percent_used": memory_percent,
                    "available_gb": round(memory.available / (1024**3), 2),
                    "swap_total_gb": round(swap.total / (1024**3), 2),
                    "swap_used_gb": round(swap.used / (1024**3), 2)
                }
            )
        except Exception as e:
            return HealthCheck(
                name="memory_usage",
                status="critical",
                message=f"Failed to check memory usage: {str(e)}",
                timestamp=datetime.now(),
                component="memory"
            )

    async def _check_cpu_usage(self) -> HealthCheck:
        """Check CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None

            if cpu_percent > 90:
                status = "critical"
                message = f"CPU usage critically high: {cpu_percent:.1f}%"
            elif cpu_percent > 70:
                status = "warning"
                message = f"CPU usage high: {cpu_percent:.1f}%"
            else:
                status = "healthy"
                message = f"CPU usage normal: {cpu_percent:.1f}%"

            return HealthCheck(
                name="cpu_usage",
                status=status,
                message=message,
                timestamp=datetime.now(),
                component="cpu",
                details={
                    "cpu_percent": cpu_percent,
                    "cpu_count": cpu_count,
                    "load_average": load_avg
                }
            )
        except Exception as e:
            return HealthCheck(
                name="cpu_usage",
                status="critical",
                message=f"Failed to check CPU usage: {str(e)}",
                timestamp=datetime.now(),
                component="cpu"
            )

    async def _check_network_connectivity(self) -> HealthCheck:
        """Check network connectivity."""
        try:
            import socket

            # Test DNS resolution
            socket.gethostbyname("google.com")

            # Test if we can create a socket
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            test_socket.connect(("8.8.8.8", 53))
            test_socket.close()

            return HealthCheck(
                name="network_connectivity",
                status="healthy",
                message="Network connectivity normal",
                timestamp=datetime.now(),
                component="network",
                details={
                    "dns_resolution": True,
                    "tcp_connectivity": True
                }
            )
        except Exception as e:
            return HealthCheck(
                name="network_connectivity",
                status="warning",
                message=f"Network connectivity issues: {str(e)}",
                timestamp=datetime.now(),
                component="network",
                details={"error": str(e)}
            )

    async def _check_process_health(self) -> HealthCheck:
        """Check current process health."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()

            # Check if process is responsive
            if cpu_percent > 100:  # Unusually high CPU usage
                status = "warning"
                message = f"Process CPU usage high: {cpu_percent:.1f}%"
            else:
                status = "healthy"
                message = f"Process health normal (CPU: {cpu_percent:.1f}%)"

            return HealthCheck(
                name="process_health",
                status=status,
                message=message,
                timestamp=datetime.now(),
                component="process",
                details={
                    "pid": process.pid,
                    "cpu_percent": cpu_percent,
                    "memory_rss": memory_info.rss,
                    "memory_vms": memory_info.vms,
                    "num_threads": process.num_threads(),
                    "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
                }
            )
        except Exception as e:
            return HealthCheck(
                name="process_health",
                status="critical",
                message=f"Failed to check process health: {str(e)}",
                timestamp=datetime.now(),
                component="process"
            )

    async def _check_file_system(self) -> HealthCheck:
        """Check file system health."""
        try:
            # Check if we can read/write to current directory
            test_file = "health_check_test.tmp"

            with open(test_file, 'w') as f:
                f.write("health check test")

            with open(test_file) as f:
                content = f.read()

            os.remove(test_file)

            if content == "health check test":
                status = "healthy"
                message = "File system operations normal"
            else:
                status = "warning"
                message = "File system read/write test failed"

            return HealthCheck(
                name="file_system",
                status=status,
                message=message,
                timestamp=datetime.now(),
                component="filesystem",
                details={
                    "read_write_test": True,
                    "current_directory": os.getcwd()
                }
            )
        except Exception as e:
            return HealthCheck(
                name="file_system",
                status="critical",
                message=f"File system check failed: {str(e)}",
                timestamp=datetime.now(),
                component="filesystem"
            )

    async def _check_dependencies(self) -> HealthCheck:
        """Check critical dependencies."""
        try:
            critical_deps = [
                "fastapi",
                "uvicorn",
                "openai",
                "pydantic",
                "psutil"
            ]

            missing_deps = []
            for dep in critical_deps:
                try:
                    __import__(dep)
                except ImportError:
                    missing_deps.append(dep)

            if missing_deps:
                status = "critical"
                message = f"Missing critical dependencies: {', '.join(missing_deps)}"
            else:
                status = "healthy"
                message = "All critical dependencies available"

            return HealthCheck(
                name="dependencies",
                status=status,
                message=message,
                timestamp=datetime.now(),
                component="dependencies",
                details={
                    "checked_dependencies": critical_deps,
                    "missing_dependencies": missing_deps
                }
            )
        except Exception as e:
            return HealthCheck(
                name="dependencies",
                status="critical",
                message=f"Failed to check dependencies: {str(e)}",
                timestamp=datetime.now(),
                component="dependencies"
            )

    def get_health_summary(self) -> dict[str, Any]:
        """Get overall health summary."""
        if not self.checks:
            return {"status": "unknown", "message": "No health checks performed"}

        # Get most recent check for each type
        latest_checks = {}
        for check in self.checks:
            if check.name not in latest_checks or check.timestamp > latest_checks[check.name].timestamp:
                latest_checks[check.name] = check

        # Determine overall status
        critical_count = sum(1 for c in latest_checks.values() if c.status == "critical")
        warning_count = sum(1 for c in latest_checks.values() if c.status == "warning")
        healthy_count = sum(1 for c in latest_checks.values() if c.status == "healthy")

        if critical_count > 0:
            overall_status = "critical"
            message = f"{critical_count} critical issues detected"
        elif warning_count > 0:
            overall_status = "warning"
            message = f"{warning_count} warnings detected"
        else:
            overall_status = "healthy"
            message = "All systems healthy"

        return {
            "status": overall_status,
            "message": message,
            "total_checks": len(latest_checks),
            "healthy": healthy_count,
            "warnings": warning_count,
            "critical": critical_count,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "message": c.message,
                    "component": c.component,
                    "timestamp": c.timestamp.isoformat()
                }
                for c in latest_checks.values()
            ]
        }

    async def start_auto_checks(self) -> None:
        """Start automatic health checking."""
        if self.is_running:
            return

        self.is_running = True
        self.auto_check_task = asyncio.create_task(self._auto_check_loop())
        log.info("Auto health checking started")

    async def stop_auto_checks(self) -> None:
        """Stop automatic health checking."""
        if not self.is_running:
            return

        self.is_running = False
        if self.auto_check_task:
            self.auto_check_task.cancel()
            try:
                await self.auto_check_task
            except asyncio.CancelledError:
                pass
        log.info("Auto health checking stopped")

    async def _auto_check_loop(self) -> None:
        """Auto health check loop."""
        while self.is_running:
            try:
                await self.run_all_checks()
                await asyncio.sleep(self.auto_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Auto health check failed: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    def get_recent_checks(self, hours: int = 1) -> list[dict[str, Any]]:
        """Get recent health checks."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_checks = [
            c for c in self.checks
            if c.timestamp > cutoff_time
        ]

        return [
            {
                "name": c.name,
                "status": c.status,
                "message": c.message,
                "timestamp": c.timestamp.isoformat(),
                "component": c.component,
                "details": c.details
            }
            for c in recent_checks
        ]

    def export_health_data(self, filepath: str) -> None:
        """Export health check data to file."""
        data = {
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "message": c.message,
                    "timestamp": c.timestamp.isoformat(),
                    "component": c.component,
                    "details": c.details
                }
                for c in self.checks
            ],
            "summary": self.get_health_summary(),
            "export_timestamp": datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        log.info(f"Health data exported to {filepath}")


# Global health checker instance
health_checker = HealthChecker()
