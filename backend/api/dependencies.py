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


def _mask_token(token: Optional[str]) -> str:
    """Return a masked version of the token for safe logging."""
    if not token:
        return "<none>"
    if len(token) <= 8:
        return f"{token[:2]}...{token[-2:]}"
    return f"{token[:4]}...{token[-4:]}"


async def auth_guard(
    authorization: Optional[str] = Header(default=None),
    required_role: Optional[str] = None,
    request: Request = None,
):
    """
    Very lightweight auth guard to mimic Bearer token validation.

    Dev convenience: if ENVIRONMENT=development and no token provided, allow passthrough
    (mirrors docs behaviour). In non-dev, Bearer is required.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if not authorization or not authorization.startswith(API_KEY_PREFIX):
        if environment == "development":
            if request:
                request.state.user_role = required_role or "promo_lead"
            logger.info(
                "auth_guard: dev passthrough (no token). path=%s role=%s client=%s",
                request.url.path if request else "<none>",
                required_role,
                request.client.host if request and request.client else "<none>",
            )
            return True
        logger.warning(
            "auth_guard: missing/invalid prefix. env=%s path=%s role=%s client=%s auth=%s",
            environment,
            request.url.path if request else "<none>",
            required_role,
            request.client.host if request and request.client else "<none>",
            _mask_token(authorization),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    token = authorization[len(API_KEY_PREFIX):]
    if environment == "development" and token in {None, "", "test", "dev", "local"}:
        if request:
            request.state.user_role = required_role or "promo_lead"
        logger.info(
            "auth_guard: dev token passthrough. path=%s role=%s client=%s token=%s",
            request.url.path if request else "<none>",
            required_role,
            request.client.host if request and request.client else "<none>",
            _mask_token(token),
        )
        return True
    env_key = os.getenv("API_KEY")
    rec = _API_KEYS.get(token) or get_key(token)
    role = rec.get("role") if isinstance(rec, dict) else None
    if env_key and token == env_key:
        role = role or "admin"
        if request:
            request.state.user_role = role
        logger.info(
            "auth_guard: env key accepted. path=%s role=%s client=%s token=%s",
            request.url.path if request else "<none>",
            role,
            request.client.host if request and request.client else "<none>",
            _mask_token(token),
        )
        return True
    if not rec:
        logger.warning(
            "auth_guard: token not found. path=%s role=%s client=%s token=%s",
            request.url.path if request else "<none>",
            required_role,
            request.client.host if request and request.client else "<none>",
            _mask_token(token),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    if required_role and rec.get("role") not in {required_role, "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role",
        )
    if request:
        request.state.user_role = role or "promo_lead"
    logger.info(
        "auth_guard: success. path=%s role=%s client=%s token=%s",
        request.url.path if request else "<none>",
        role or "promo_lead",
        request.client.host if request and request.client else "<none>",
        _mask_token(token),
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
