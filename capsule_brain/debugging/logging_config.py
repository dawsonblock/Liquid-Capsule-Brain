"""Advanced logging configuration with structured logging and performance monitoring."""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data."""
        # Base log data
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "getMessage"
            }:
                log_data[key] = value

        return json.dumps(log_data, default=str)


class PerformanceFilter(logging.Filter):
    """Filter for performance-related logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter performance logs."""
        return "performance" in record.name.lower() or "perf" in record.getMessage().lower()


class SecurityFilter(logging.Filter):
    """Filter for security-related logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter security logs."""
        return "security" in record.name.lower() or "auth" in record.getMessage().lower()


class ErrorTrackingFilter(logging.Filter):
    """Filter for error tracking."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter error logs."""
        return record.levelno >= logging.ERROR


def setup_advanced_logging() -> None:
    """Setup advanced logging configuration."""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with structured formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "application.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)
    
    # Performance logs handler
    perf_handler = logging.handlers.RotatingFileHandler(
        log_dir / "performance.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(StructuredFormatter())
    perf_handler.addFilter(PerformanceFilter())
    root_logger.addHandler(perf_handler)
    
    # Security logs handler
    security_handler = logging.handlers.RotatingFileHandler(
        log_dir / "security.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(StructuredFormatter())
    security_handler.addFilter(SecurityFilter())
    root_logger.addHandler(security_handler)
    
    # Error logs handler
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    error_handler.addFilter(ErrorTrackingFilter())
    root_logger.addHandler(error_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class LoggingMiddleware:
    """Middleware for request/response logging."""

    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("http")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = scope
        start_time = datetime.now(timezone.utc)
        
        # Extract headers safely
        headers = dict(request.get("headers", []))
        user_agent = headers.get(b"user-agent", b"unknown").decode() if b"user-agent" in headers else "unknown"
        client_ip = request.get("client", ["unknown"])[0] if request.get("client") else "unknown"
        
        # Log request
        self.logger.info(
            "Request started: %s %s from %s (%s)",
            request["method"],
            request["path"],
            client_ip,
            user_agent,
            extra={
                "method": request["method"],
                "path": request["path"],
                "query_string": request["query_string"].decode(),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "request_id": id(request)
            }
        )

        # Process request
        response_sent = False
        response_status = None
        
        async def send_wrapper(message):
            nonlocal response_sent, response_status
            
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_sent = True
                
                # Log response
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                self.logger.info(
                    "Request completed: %s %s -> %d (%.3fs)",
                    request["method"],
                    request["path"],
                    response_status,
                    duration,
                    extra={
                        "method": request["method"],
                        "path": request["path"],
                        "status_code": response_status,
                        "duration": duration,
                        "request_id": id(request)
                    }
                )
            
            await send(message)

        await self.app(scope, receive, send_wrapper)


class PerformanceLogger:
    """Logger for performance metrics."""

    def __init__(self):
        self.logger = logging.getLogger("performance")

    def log_operation(self, operation: str, duration: float, **kwargs) -> None:
        """Log performance operation."""
        self.logger.info(
            "Operation completed",
            operation=operation,
            duration=duration,
            **kwargs
        )

    def log_memory_usage(self, operation: str, memory_mb: float) -> None:
        """Log memory usage."""
        self.logger.info(
            "Memory usage",
            operation=operation,
            memory_mb=memory_mb
        )

    def log_cpu_usage(self, operation: str, cpu_percent: float) -> None:
        """Log CPU usage."""
        self.logger.info(
            "CPU usage",
            operation=operation,
            cpu_percent=cpu_percent
        )


class SecurityLogger:
    """Logger for security events."""

    def __init__(self):
        self.logger = logging.getLogger("security")

    def log_auth_attempt(self, user: str, success: bool, ip: str, **kwargs) -> None:
        """Log authentication attempt."""
        self.logger.info(
            "Authentication attempt",
            user=user,
            success=success,
            ip=ip,
            **kwargs
        )

    def log_security_event(self, event_type: str, severity: str, **kwargs) -> None:
        """Log security event."""
        self.logger.warning(
            "Security event",
            event_type=event_type,
            severity=severity,
            **kwargs
        )

    def log_file_upload(self, filename: str, size: int, allowed: bool, **kwargs) -> None:
        """Log file upload attempt."""
        self.logger.info(
            "File upload attempt",
            filename=filename,
            size=size,
            allowed=allowed,
            **kwargs
        )


# Global logger instances
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()
