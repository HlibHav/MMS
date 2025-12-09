"""
Shared API dependencies for auth and rate limiting.
"""

from fastapi import Header, HTTPException, Request, status
from typing import Optional
import time
import os
import logging
from backend.api.auth_store import get_key
try:
    from backend.api.routes.auth import _API_KEYS
except Exception:
    _API_KEYS = {}


API_KEY_PREFIX = "Bearer "
logger = logging.getLogger(__name__)


async def auth_guard(
    authorization: Optional[str] = Header(default=None),
    required_role: Optional[str] = None,
):
    """
    Very lightweight auth guard to mimic Bearer token validation.
    """
    if not authorization or not authorization.startswith(API_KEY_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    token = authorization[len(API_KEY_PREFIX):]
    env_key = os.getenv("API_KEY")
    if env_key and token == env_key:
        return True
    rec = _API_KEYS.get(token) or get_key(token)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    if required_role and rec.get("role") not in {required_role, "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role",
        )
    return True


# Simple in-memory token bucket stub keyed by client IP or token.
_RATE_LIMIT = {"window": 60, "limit": 100, "hits": {}}

_redis_client = None
try:
    import redis  # type: ignore

    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        _redis_client = redis.Redis.from_url(redis_url)
except Exception:
    _redis_client = None


async def rate_limit_guard(request: Request, authorization: Optional[str] = Header(default=None)):
    """
    Naive rate limiter to align with documented rate limits.
    """
    client_ip = request.client.host if request.client else "unknown"
    token = authorization[len(API_KEY_PREFIX):] if authorization and authorization.startswith(API_KEY_PREFIX) else None
    bucket_key = token or client_ip
    now = int(time.time())
    window = _RATE_LIMIT["window"]
    limit = _RATE_LIMIT["limit"]
    if _redis_client:
        pipe = _redis_client.pipeline()
        pipe.incr(bucket_key)
        pipe.expire(bucket_key, window)
        count, _ = pipe.execute()
        if int(count) > limit:
            logger.warning("Rate limit exceeded for key=%s", bucket_key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        return True

    bucket = _RATE_LIMIT["hits"].setdefault(bucket_key, {"start": now, "count": 0})
    if now - bucket["start"] >= window:
        bucket["start"] = now
        bucket["count"] = 0
    bucket["count"] += 1
    if bucket["count"] > limit:
        logger.warning("Rate limit exceeded for key=%s", bucket_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
    return True
