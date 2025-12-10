"""
Authentication Routes

Endpoints for API key management and authentication (docs-aligned).
"""

from datetime import datetime, timedelta
import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class APIKeyRequest(BaseModel):
    """Request to create API key."""
    name: str
    expires_in_days: Optional[int] = 90


class APIKeyResponse(BaseModel):
    """API key response."""
    api_key: str
    expires_at: str


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(request: APIKeyRequest) -> APIKeyResponse:
    """
    Create a new API key.
    
    Dev mode: no persistence; returns plaintext key to caller.
    """
    days = request.expires_in_days or 90
    if days <= 0:
        raise HTTPException(status_code=400, detail="expires_in_days must be positive")

    api_key = f"pk_{secrets.token_urlsafe(32)}"
    expires_at = datetime.utcnow() + timedelta(days=days)
    
    return APIKeyResponse(api_key=api_key, expires_at=expires_at.isoformat() + "Z")
