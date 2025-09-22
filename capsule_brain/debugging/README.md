# Capsule Brain Debugging System

A comprehensive debugging and monitoring system for the Capsule Brain AI platform.

## Overview

The debugging system provides advanced tools for monitoring, profiling, and troubleshooting the Capsule Brain system. It includes memory monitoring, performance tracking, error analysis, health checking, and comprehensive system analysis.

## Components

### 1. Advanced Debugger (`advanced_debugger.py`)
The main orchestrator that integrates all debugging tools and provides a unified interface.

**Features:**
- Comprehensive system analysis
- Issue-specific debugging
- Health score calculation
- Recommendation generation
- Data export capabilities

### 2. Debugger (`debugger.py`)
Core debugging utilities for interactive debugging and logging.

**Features:**
- Interactive debugging sessions
- Enhanced logging configuration
- Debug level management
- Session tracking

### 3. Profiler (`profiler.py`)
Performance profiling and analysis tools.

**Features:**
- CPU profiling
- Memory profiling
- Function-level performance tracking
- Bottleneck identification

### 4. Memory Monitor (`memory_monitor.py`)
Advanced memory monitoring and leak detection.

**Features:**
- Real-time memory tracking
- Memory leak detection
- Garbage collection monitoring
- Memory usage trends
- Object counting and analysis

### 5. Error Tracker (`error_tracker.py`)
Comprehensive error tracking and analysis.

**Features:**
- Error categorization and severity levels
- Error pattern analysis
- Rate monitoring and alerting
- Health score calculation
- Trend analysis

### 6. Performance Monitor (`performance_monitor.py`)
Performance metrics collection and analysis.

**Features:**
- Custom performance metrics
- Threshold-based alerting
- Performance scoring
- Trend analysis
- Baseline calculation

### 7. Health Checker (`health_checker.py`)
System health monitoring and validation.

**Features:**
- System resource monitoring
- Dependency checking
- Network connectivity tests
- Process health validation
- File system checks

### 8. Debugging API (`api.py`)
REST API endpoints for debugging system access.

**Endpoints:**
- `/debug/status` - System status
- `/debug/health` - Health checks
- `/debug/performance` - Performance metrics
- `/debug/errors` - Error tracking
- `/debug/memory` - Memory monitoring
- `/debug/profiling` - Profiling tools
- `/debug/dashboard` - Comprehensive dashboard

## Usage

### Basic Usage

```python
from capsule_brain.debugging import advanced_debugger

# Run comprehensive analysis
analysis = await advanced_debugger.run_comprehensive_analysis()

# Debug specific issue
debug_result = await advanced_debugger.debug_issue(
    "Memory usage is high",
    context={"component": "api", "timeframe": "last_hour"}
)

# Get debugging dashboard
dashboard = advanced_debugger.get_debugging_dashboard()
```

### Memory Monitoring

```python
from capsule_brain.debugging import memory_monitor

# Enable memory monitoring
memory_monitor.enable()

# Take memory snapshot
snapshot = memory_monitor.take_snapshot("before_operation")

# Detect memory leaks
leaks = memory_monitor.detect_memory_leaks()

# Force garbage collection
gc_stats = memory_monitor.force_garbage_collection()
```

### Performance Monitoring

```python
from capsule_brain.debugging import performance_monitor, record_metric

# Record custom metric
record_metric("api_response_time", 0.5, "api")

# Set performance thresholds
performance_monitor.set_threshold(
    "api_response_time", 
    warning=1.0, 
    critical=5.0
)

# Get performance score
score = performance_monitor.get_performance_score()
```

### Error Tracking

```python
from capsule_brain.debugging import error_tracker, track_error, ErrorSeverity, ErrorCategory

# Track an error
error_id = track_error(
    ValueError("Invalid input"),
    context={"user_id": "123", "endpoint": "/api/test"},
    severity=ErrorSeverity.MEDIUM,
    category=ErrorCategory.VALIDATION
)

# Get error summary
summary = error_tracker.get_error_summary()
```

### Health Checking

```python
from capsule_brain.debugging import health_checker

# Run all health checks
results = await health_checker.run_all_checks()

# Get health summary
summary = health_checker.get_health_summary()

# Start automatic health checking
await health_checker.start_auto_checks()
```

### Profiling

```python
from capsule_brain.debugging import profiler, monitor_performance

# Start profiling
profiler.start_profiling()

# Profile a function
@monitor_performance("slow_function", "api")
def slow_function():
    # Your code here
    pass

# Stop profiling and get results
profiler.stop_profiling()
summary = profiler.get_profiling_summary()
```

## API Usage

### Get System Status
```bash
curl -X GET "http://localhost:8000/debug/status"
```

### Run Health Checks
```bash
curl -X POST "http://localhost:8000/debug/health/run"
```

### Get Performance Metrics
```bash
curl -X GET "http://localhost:8000/debug/performance"
```

### Debug Specific Issue
```bash
curl -X POST "http://localhost:8000/debug/debug/issue" \
  -H "Content-Type: application/json" \
  -H "x-admin-token: your-admin-token" \
  -d '{"issue_description": "High memory usage", "context": {"component": "api"}}'
```

### Run Comprehensive Analysis
```bash
curl -X POST "http://localhost:8000/debug/debug/analysis" \
  -H "x-admin-token: your-admin-token"
```

## Configuration

### Environment Variables

```bash
# Enable debugging system
DEBUGGING_ENABLED=true

# Memory monitoring
MEMORY_MONITORING_ENABLED=true

# Performance monitoring
PERFORMANCE_MONITORING_ENABLED=true

# Error tracking
ERROR_TRACKING_ENABLED=true

# Health checking
HEALTH_CHECKING_ENABLED=true
```

### Thresholds

You can customize performance thresholds:

```python
performance_monitor.set_threshold("response_time", warning=1.0, critical=5.0)
performance_monitor.set_threshold("memory_usage", warning=100*1024*1024, critical=500*1024*1024)
```

## Monitoring and Alerting

The debugging system provides several levels of monitoring:

1. **Real-time Monitoring**: Continuous monitoring of system metrics
2. **Threshold-based Alerting**: Alerts when metrics exceed configured thresholds
3. **Health Checks**: Regular validation of system components
4. **Error Tracking**: Comprehensive error analysis and pattern detection
5. **Performance Profiling**: Detailed performance analysis and optimization recommendations

## Data Export

All debugging data can be exported for analysis:

```python
# Export all debugging data
advanced_debugger.export_debugging_data("debug_data.json")

# Export specific component data
memory_monitor.export_data("memory_data.json")
error_tracker.export_errors("error_data.json")
performance_monitor.export_data("performance_data.json")
```

## Best Practices

1. **Enable Early**: Start debugging system early in development
2. **Monitor Continuously**: Use automatic monitoring for production systems
3. **Set Appropriate Thresholds**: Configure thresholds based on your system requirements
4. **Regular Analysis**: Run comprehensive analysis regularly
5. **Export Data**: Export debugging data for historical analysis
6. **Act on Recommendations**: Follow system-generated recommendations for improvements

## Troubleshooting

### Common Issues

1. **High Memory Usage**: Use memory monitor to identify leaks and optimize
2. **Performance Issues**: Use profiler to identify bottlenecks
3. **Frequent Errors**: Use error tracker to identify patterns and root causes
4. **System Health Issues**: Use health checker to validate system components

### Debug Commands

```bash
# Check system health
curl -X GET "http://localhost:8000/debug/health"

# Force garbage collection
curl -X POST "http://localhost:8000/debug/memory/gc"

# Get recent errors
curl -X GET "http://localhost:8000/debug/errors/recent?hours=24"

# Run comprehensive analysis
curl -X POST "http://localhost:8000/debug/debug/analysis" \
  -H "x-admin-token: your-admin-token"
```

## Integration

The debugging system integrates seamlessly with the Capsule Brain platform:

- **Automatic Integration**: Debugging is automatically enabled when the system starts
- **API Integration**: All debugging tools are accessible via REST API
- **Admin Integration**: Debugging controls require admin authentication
- **Logging Integration**: Debugging system uses the platform's logging infrastructure

## Future Enhancements

- Machine learning-based anomaly detection
- Predictive performance analysis
- Advanced visualization dashboards
- Integration with external monitoring systems
- Automated remediation suggestions
