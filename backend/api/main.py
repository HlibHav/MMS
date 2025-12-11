"""
FastAPI Application

Main FastAPI application setup and configuration.
"""

import os
import uuid
import time
import logging

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import auth_guard, rate_limit_guard
from middleware.errors import (
    APIError,
    api_error_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from .routes import discovery, scenarios, optimization, creative, data, auth, chat, webhooks

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Promo Scenario Co-Pilot API",
    description="AI-powered promotional campaign planning and optimization system",
    version="1.0.0",
)

# CORS middleware
environment = os.getenv("ENVIRONMENT", "development").lower()
dev_environments = {"development", "dev", "local"}
default_dev_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
elif environment in dev_environments:
    allowed_origins = default_dev_origins
else:
    allowed_origins = []

logger.info("CORS allow_origins=%s (env=%s)", allowed_origins, environment)
cors_kwargs = {
    "allow_origins": allowed_origins,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    # Always allow localhost/127.* with any port to avoid dev port collisions.
    "allow_origin_regex": r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
}
app.add_middleware(CORSMiddleware, **cors_kwargs)


# Lightweight request logger to trace auth + CORS/debug context
@app.middleware("http")
async def debug_request_logger(request: Request, call_next):
    origin = request.headers.get("origin")
    auth = request.headers.get("authorization")
    masked_auth = "<none>" if not auth else (auth[:10] + "..." if len(auth) > 14 else auth)
    logger.info(
        "request:start method=%s path=%s origin=%s auth=%s client=%s",
        request.method,
        request.url.path,
        origin,
        masked_auth,
        request.client.host if request.client else "<none>",
    )
    response = await call_next(request)
    logger.info(
        "request:end method=%s path=%s status=%s origin=%s",
        request.method,
        request.url.path,
        response.status_code,
        origin,
    )
    return response


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    """Attach request_id and add default rate-limit headers."""
    request.state.request_id = str(uuid.uuid4())
    start = time.time()
    response = await call_next(request)
    response.headers.setdefault("X-RateLimit-Limit", "100")
    response.headers.setdefault("X-RateLimit-Remaining", "95")
    response.headers.setdefault("X-RateLimit-Reset", "0")
    response.headers["X-Response-Time-ms"] = f"{(time.time() - start)*1000:.1f}"
    logger.info("%s %s -> %s [%s]", request.method, request.url.path, response.status_code, request.state.request_id)
    return response


# Exception handlers for consistent error schema
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Shared dependencies to enforce auth + rate limits
secured_deps = [Depends(auth_guard), Depends(rate_limit_guard)]

app.include_router(discovery.router, prefix="/api/v1/discovery", tags=["discovery"], dependencies=secured_deps)
app.include_router(scenarios.router, prefix="/api/v1/scenarios", tags=["scenarios"], dependencies=secured_deps)
app.include_router(optimization.router, prefix="/api/v1/optimization", tags=["optimization"], dependencies=secured_deps)
app.include_router(creative.router, prefix="/api/v1/creative", tags=["creative"], dependencies=secured_deps)
app.include_router(data.router, prefix="/api/v1/data", tags=["data"], dependencies=secured_deps)
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"], dependencies=secured_deps)
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"], dependencies=secured_deps)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Promo Scenario Co-Pilot API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
