"""Rate limiting implementation for API protection."""

import logging
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import HTTPException, Request, status

log = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter using sliding window algorithm."""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        block_duration: int = 300,
    ) -> None:
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            block_duration: Duration to block IP after exceeding limit
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_duration = block_duration
        self.requests: dict[str, deque] = defaultdict(deque)
        self.blocked_ips: dict[str, float] = {}

    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for the given IP.

        Args:
            client_ip: Client IP address

        Returns:
            True if request is allowed, False otherwise
        """
        current_time = time.time()

        # Check if IP is currently blocked
        if client_ip in self.blocked_ips:
            if current_time < self.blocked_ips[client_ip]:
                return False
            else:
                # Block period expired, remove from blocked list
                del self.blocked_ips[client_ip]

        # Clean old requests outside the window
        cutoff_time = current_time - self.window_seconds
        while self.requests[client_ip] and self.requests[client_ip][0] < cutoff_time:
            self.requests[client_ip].popleft()

        # Check if under rate limit
        if len(self.requests[client_ip]) < self.max_requests:
            self.requests[client_ip].append(current_time)
            return True
        else:
            # Exceeded rate limit, block IP
            self.blocked_ips[client_ip] = current_time + self.block_duration
            log.warning(f"Rate limit exceeded for IP: {client_ip}")
            return False

    def get_remaining_requests(self, client_ip: str) -> int:
        """Get remaining requests for the given IP.

        Args:
            client_ip: Client IP address

        Returns:
            Number of remaining requests
        """
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds

        # Clean old requests
        while self.requests[client_ip] and self.requests[client_ip][0] < cutoff_time:
            self.requests[client_ip].popleft()

        return max(0, self.max_requests - len(self.requests[client_ip]))


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(request: Request) -> None:
    """Check rate limit for the request.

    Args:
        request: FastAPI request object

    Raises:
        HTTPException: If rate limit is exceeded
    """
    client_ip = request.client.host if request.client else "unknown"

    if not rate_limiter.is_allowed(client_ip):
        remaining = rate_limiter.get_remaining_requests(client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "retry_after": 60,
                "remaining_requests": remaining,
            },
        )


def get_rate_limit_info(request: Request) -> dict[str, Any]:
    """Get rate limit information for the request.

    Args:
        request: FastAPI request object

    Returns:
        Rate limit information
    """
    client_ip = request.client.host if request.client else "unknown"
    remaining = rate_limiter.get_remaining_requests(client_ip)

    return {
        "remaining_requests": remaining,
        "max_requests": rate_limiter.max_requests,
        "window_seconds": rate_limiter.window_seconds,
        "is_blocked": client_ip in rate_limiter.blocked_ips,
    }
