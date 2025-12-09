"""
Rate Limiting Middleware

Rate limiting for API endpoints using slowapi.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from typing import Callable
import os

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=os.getenv("REDIS_URL", "memory://")  # Use Redis in production
)

# Rate limit configurations per endpoint type
RATE_LIMITS = {
    "standard": "100/minute",
    "optimization": "10/minute",
    "data_processing": "5/hour",
    "chat": "30/minute",
}


def get_rate_limit(limit_type: str = "standard") -> Callable:
    """Get rate limit decorator for specific limit type."""
    limit = RATE_LIMITS.get(limit_type, RATE_LIMITS["standard"])
    return limiter.limit(limit)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded."""
    raise HTTPException(
        status_code=429,
        detail={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit exceeded: {exc.detail}",
                "retry_after": exc.retry_after,
            }
        },
        headers={
            "X-RateLimit-Limit": str(exc.limit),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(exc.reset_at) if exc.reset_at else "",
            "Retry-After": str(exc.retry_after) if exc.retry_after else "60",
        }
    )
