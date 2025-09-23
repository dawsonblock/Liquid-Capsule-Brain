"""Security enhancements for the GUI system."""

import logging
import re

from fastapi import HTTPException, status
from fastapi.responses import HTMLResponse

log = logging.getLogger(__name__)


class GUISecurityManager:
    """Security manager for GUI components."""

    # Content Security Policy for GUI
    CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none'; "
        "base-uri 'self';"
    )

    # Allowed file extensions for uploads
    ALLOWED_EXTENSIONS = {".pdf", ".txt", ".zip", ".json", ".csv", ".md"}

    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(self) -> None:
        """Initialize GUI security manager."""
        self.blocked_ips: set[str] = set()
        self.rate_limits: dict[str, int] = {}

    def validate_file_upload(self, filename: str, content_length: int) -> None:
        """Validate file upload request.

        Args:
            filename: Name of the uploaded file
            content_length: Size of the file in bytes

        Raises:
            HTTPException: If file is invalid
        """
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
            )

        # Check file extension
        file_ext = filename.lower().split(".")[-1] if "." in filename else ""
        if f".{file_ext}" not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type .{file_ext} not allowed. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}",
            )

        # Check file size
        if content_length > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {self.MAX_FILE_SIZE} bytes",
            )

        # Check for dangerous filename patterns
        dangerous_patterns = [
            r"\.\./",  # Path traversal
            r"<script",  # XSS attempts
            r"javascript:",  # JavaScript URLs
            r"data:text/html",  # HTML data URLs
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid filename pattern detected",
                )

    def sanitize_user_input(self, user_input: str) -> str:
        """Sanitize user input for GUI display.

        Args:
            user_input: Raw user input

        Returns:
            Sanitized input safe for display
        """
        if not user_input:
            return ""

        # Remove HTML tags
        sanitized = re.sub(r"<[^>]+>", "", user_input)

        # Escape special characters
        sanitized = sanitized.replace("&", "&amp;")
        sanitized = sanitized.replace("<", "&lt;")
        sanitized = sanitized.replace(">", "&gt;")
        sanitized = sanitized.replace('"', "&quot;")
        sanitized = sanitized.replace("'", "&#x27;")

        # Limit length
        if len(sanitized) > 4000:
            sanitized = sanitized[:4000] + "..."

        return sanitized

    def validate_websocket_message(self, message: str) -> bool:
        """Validate WebSocket message content.

        Args:
            message: WebSocket message content

        Returns:
            True if message is valid, False otherwise
        """
        if not message:
            return False

        # Check message length
        if len(message) > 10000:  # 10KB limit
            return False

        # Check for malicious patterns
        malicious_patterns = [
            r"<script[^>]*>.*?</script>",  # Script tags
            r"javascript:",  # JavaScript URLs
            r"data:text/html",  # HTML data URLs
            r"eval\s*\(",  # eval() calls
            r"Function\s*\(",  # Function constructor
        ]

        for pattern in malicious_patterns:
            if re.search(pattern, message, re.IGNORECASE | re.DOTALL):
                log.warning(f"Malicious WebSocket message detected: {pattern}")
                return False

        return True

    def add_security_headers(self, response: HTMLResponse) -> HTMLResponse:
        """Add security headers to GUI responses.

        Args:
            response: HTML response to secure

        Returns:
            Response with security headers
        """
        response.headers["Content-Security-Policy"] = self.CSP_POLICY
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=(), "
            "accelerometer=(), ambient-light-sensor=()"
        )

        return response

    def check_rate_limit(self, client_ip: str) -> bool:
        """Check rate limit for client IP.

        Args:
            client_ip: Client IP address

        Returns:
            True if within rate limit, False otherwise
        """
        import time

        current_time = int(time.time())
        minute_key = f"{client_ip}:{current_time // 60}"

        # Allow 60 requests per minute per IP
        if minute_key not in self.rate_limits:
            self.rate_limits[minute_key] = 0

        self.rate_limits[minute_key] += 1

        # Clean old entries (older than 5 minutes)
        cutoff_time = current_time // 60 - 5
        self.rate_limits = {
            k: v for k, v in self.rate_limits.items() if int(k.split(":")[1]) > cutoff_time
        }

        return self.rate_limits[minute_key] <= 60

    def block_ip(self, client_ip: str) -> None:
        """Block an IP address.

        Args:
            client_ip: IP address to block
        """
        self.blocked_ips.add(client_ip)
        log.warning(f"Blocked IP address: {client_ip}")

    def is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is blocked.

        Args:
            client_ip: IP address to check

        Returns:
            True if IP is blocked, False otherwise
        """
        return client_ip in self.blocked_ips


# Global security manager instance
gui_security = GUISecurityManager()
