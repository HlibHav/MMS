"""
Error Handling Middleware

Standardized error responses and exception handlers.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error class."""
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: Dict[str, Any] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Validation error."""
    def __init__(self, message: str, field: str = None, constraint: str = None):
        details = {}
        if field:
            details["field"] = field
        if constraint:
            details["constraint"] = constraint
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=400,
            details=details
        )


class NotFoundError(APIError):
    """Resource not found error."""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource_type} not found: {resource_id}",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class UnauthorizedError(APIError):
    """Unauthorized error."""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=401
        )


class ForbiddenError(APIError):
    """Forbidden error."""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=403
        )


class ProcessingError(APIError):
    """Data processing error."""
    def __init__(self, message: str, job_id: str = None):
        details = {}
        if job_id:
            details["job_id"] = job_id
        super().__init__(
            code="PROCESSING_ERROR",
            message=message,
            status_code=500,
            details=details
        )


def format_error_response(
    code: str,
    message: str,
    status_code: int,
    details: Dict[str, Any] = None,
    request_id: str = None
) -> Dict[str, Any]:
    """Format error response according to API specification."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": request_id or str(uuid.uuid4())
        }
    }


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions."""
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            request_id=request_id
        )
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException."""
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    
    # Map status codes to error codes
    error_codes = {
        400: "VALIDATION_ERROR",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
    }
    
    code = error_codes.get(exc.status_code, "INTERNAL_ERROR")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            code=code,
            message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            status_code=exc.status_code,
            request_id=request_id
        )
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=400,
        content=format_error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            status_code=400,
            details={"errors": errors},
            request_id=request_id
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    
    logger.exception(f"Unhandled exception: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content=format_error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            status_code=500,
            request_id=request_id
        )
    )
