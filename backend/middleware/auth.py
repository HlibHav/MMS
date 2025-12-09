"""
Authentication Middleware

JWT-based authentication with RBAC support.
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional, List
import os
import logging
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Role(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    PROMO_LEAD = "promo_lead"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User:
    """User model."""
    def __init__(self, user_id: str, email: str, roles: List[Role]):
        self.user_id = user_id
        self.email = email
        self.roles = roles
    
    def has_role(self, role: Role) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def has_any_role(self, roles: List[Role]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    For development: Returns a mock user if no token provided.
    """
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Skip auth in development if no token provided
    if environment == "development" and not credentials:
        return User(
            user_id="dev_user",
            email="dev@example.com",
            roles=[Role.ADMIN]
        )
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id: str = payload.get("sub")
    email: str = payload.get("email", "")
    roles: List[str] = payload.get("roles", [Role.VIEWER.value])
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user_roles = [Role(role) for role in roles if role in [r.value for r in Role]]
    if not user_roles:
        user_roles = [Role.VIEWER]
    
    return User(user_id=user_id, email=email, roles=user_roles)


def require_role(*allowed_roles: Role):
    """Dependency factory for role-based access control."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_any_role(list(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker


# Convenience dependencies
require_admin = require_role(Role.ADMIN)
require_promo_lead = require_role(Role.ADMIN, Role.PROMO_LEAD)
require_analyst = require_role(Role.ADMIN, Role.PROMO_LEAD, Role.ANALYST)
