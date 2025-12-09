"""
<<<<<<< HEAD
Authentication and API key management routes.

These endpoints align with docs/API_SPECIFICATION.md for issuing API keys.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from secrets import token_urlsafe
from datetime import datetime, timedelta
from backend.api.auth_store import add_key, revoke_key


class ApiKeyRequest(BaseModel):
    name: str
    expires_in_days: int = 90


class ApiKeyResponse(BaseModel):
    api_key: str
    expires_at: datetime
    role: str = "read"


router = APIRouter()

# In-memory key store for demo purposes.
_API_KEYS: dict[str, ApiKeyResponse] = {}


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(payload: ApiKeyRequest) -> ApiKeyResponse:
    """
    Issue a new API key (demo only, no persistence).
    """
    if payload.expires_in_days <= 0:
        raise HTTPException(status_code=400, detail="expires_in_days must be positive")
    rec = add_key(name=payload.name, role="read", ttl_days=payload.expires_in_days)
    res = ApiKeyResponse(api_key=rec["api_key"], expires_at=datetime.fromisoformat(rec["expires_at"]), role=rec["role"])
    _API_KEYS[res.api_key] = res
    return res


@router.delete("/api-keys/{token}")
async def delete_api_key(token: str):
    revoke_key(token)
    _API_KEYS.pop(token, None)
    return {"revoked": True}
=======
Authentication Routes

Endpoints for API key management and authentication.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import secrets

from middleware.auth import create_access_token, get_current_user, User, Role, require_admin

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
async def create_api_key(
    request: APIKeyRequest,
    current_user: User = Depends(require_admin)
) -> APIKeyResponse:
    """
    Create a new API key.
    
    Requires admin role.
    """
    # Generate API key
    api_key = f"pk_{secrets.token_urlsafe(32)}"
    
    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
    
    # TODO: Store API key in database with user association
    # For now, return the key (in production, hash and store)
    
    return APIKeyResponse(
        api_key=api_key,
        expires_at=expires_at.isoformat() + "Z"
    )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get current user information."""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "roles": [role.value for role in current_user.roles]
    }
>>>>>>> dbf51a57d90587fa2ae6397ac9a6c322b870fe89
