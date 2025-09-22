"""Debugging API endpoints for the Capsule Brain system."""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..security.admin import require_admin_token
from .advanced_debugger import advanced_debugger
from .error_tracker import error_tracker
from .health_checker import health_checker
from .memory_monitor import memory_monitor
from .performance_monitor import performance_monitor
from .profiler import profiler

log = logging.getLogger(__name__)

# Create debugging router
debug_router = APIRouter(prefix="/debug", tags=["debugging"])


class DebugRequest(BaseModel):
    """Debug request model."""
    issue_description: str
    context: dict[str, Any] | None = None


class PerformanceThresholdRequest(BaseModel):
    """Performance threshold request model."""
    metric_name: str
    warning: float | None = None
    critical: float | None = None


@debug_router.get("/status")
async def get_debug_status():
    """Get debugging system status."""
    try:
        return {
            "status": "success",
            "data": advanced_debugger.get_status(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to get debug status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.get("/health")
async def get_health_status():
    """Get system health status."""
    try:
        health_summary = health_checker.get_health_summary()
        return {
            "status": "success",
            "data": health_summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/health/run")
async def run_health_checks():
    """Run all health checks."""
    try:
        results = await health_checker.run_all_checks()
        return {
            "status": "success",
            "data": {
                "checks_performed": len(results),
                "results": [
                    {
                        "name": r.name,
                        "status": r.status,
                        "message": r.message,
                        "component": r.component,
                        "details": r.details
                    }
                    for r in results
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to run health checks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.get("/performance")
async def get_performance_status():
    """Get performance monitoring status."""
    try:
        overview = performance_monitor.get_performance_overview()
        score = performance_monitor.get_performance_score()
        return {
            "status": "success",
            "data": {
                "overview": overview,
                "score": score
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to get performance status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.get("/performance/metrics/{metric_name}")
async def get_metric_details(metric_name: str):
    """Get detailed metrics for a specific metric."""
    try:
        summary = performance_monitor.get_metric_summary(metric_name)
        recent = performance_monitor.get_recent_metrics(metric_name, minutes=60)
        return {
            "status": "success",
            "data": {
                "metric_name": metric_name,
                "summary": summary,
                "recent_metrics": recent
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to get metric details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/performance/thresholds")
async def set_performance_thresholds(
    request: PerformanceThresholdRequest,
    _: None = Depends(require_admin_token)
):
    """Set performance thresholds."""
    try:
        performance_monitor.set_threshold(
            request.metric_name,
            warning=request.warning,
            critical=request.critical
        )
        return {
            "status": "success",
            "message": f"Thresholds set for {request.metric_name}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to set performance thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.get("/errors")
async def get_error_status():
    """Get error tracking status."""
    try:
        summary = error_tracker.get_error_summary()
        health_score = error_tracker.get_health_score()
        return {
            "status": "success",
            "data": {
                "summary": summary,
                "health_score": health_score
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to get error status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.get("/errors/recent")
async def get_recent_errors(hours: int = 24):
    """Get recent errors."""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        errors = error_tracker.get_errors_by_time_range(cutoff_time, datetime.now())
        return {
            "status": "success",
            "data": {
                "errors": errors,
                "count": len(errors),
                "time_range_hours": hours
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to get recent errors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.get("/memory")
async def get_memory_status():
    """Get memory monitoring status."""
    try:
        stats = memory_monitor.get_memory_stats()
        trend = memory_monitor.get_memory_trend()
        leaks = memory_monitor.detect_memory_leaks()
        return {
            "status": "success",
            "data": {
                "stats": stats,
                "trend": trend[-10:] if trend else [],
                "leaks": leaks,
                "top_consumers": memory_monitor.get_top_memory_consumers()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to get memory status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/memory/gc")
async def force_garbage_collection():
    """Force garbage collection."""
    try:
        stats = memory_monitor.force_garbage_collection()
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to force garbage collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.get("/profiling")
async def get_profiling_status():
    """Get profiling status."""
    try:
        summary = profiler.get_profiling_summary()
        return {
            "status": "success",
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to get profiling status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/profiling/start")
async def start_profiling(
    _: None = Depends(require_admin_token)
):
    """Start profiling."""
    try:
        profiler.start_profiling()
        return {
            "status": "success",
            "message": "Profiling started",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to start profiling: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/profiling/stop")
async def stop_profiling(
    _: None = Depends(require_admin_token)
):
    """Stop profiling."""
    try:
        profiler.stop_profiling()
        return {
            "status": "success",
            "message": "Profiling stopped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to stop profiling: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/debug/issue")
async def debug_issue(
    request: DebugRequest,
    _: None = Depends(require_admin_token)
):
    """Debug a specific issue."""
    try:
        result = await advanced_debugger.debug_issue(
            request.issue_description,
            request.context
        )
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to debug issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/debug/analysis")
async def run_comprehensive_analysis(
    _: None = Depends(require_admin_token)
):
    """Run comprehensive system analysis."""
    try:
        result = await advanced_debugger.run_comprehensive_analysis()
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to run comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.get("/dashboard")
async def get_debugging_dashboard():
    """Get debugging dashboard data."""
    try:
        dashboard = advanced_debugger.get_debugging_dashboard()
        return {
            "status": "success",
            "data": dashboard,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to get debugging dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/export")
async def export_debugging_data(
    filepath: str,
    _: None = Depends(require_admin_token)
):
    """Export debugging data to file."""
    try:
        advanced_debugger.export_debugging_data(filepath)
        return {
            "status": "success",
            "message": f"Debugging data exported to {filepath}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to export debugging data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/enable")
async def enable_debugging(
    _: None = Depends(require_admin_token)
):
    """Enable debugging system."""
    try:
        advanced_debugger.enable()
        return {
            "status": "success",
            "message": "Debugging system enabled",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to enable debugging: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/disable")
async def disable_debugging(
    _: None = Depends(require_admin_token)
):
    """Disable debugging system."""
    try:
        advanced_debugger.disable()
        return {
            "status": "success",
            "message": "Debugging system disabled",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to disable debugging: {e}")
        raise HTTPException(status_code=500, detail=str(e))
