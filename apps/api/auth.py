"""
JWT-based authentication and authorization for AIFP-AOS API.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from apps.api.config import settings

logger = logging.getLogger(__name__)

# Security configuration
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Role definitions
ROLES = {
    "founder_admin": ["read", "write", "approve", "execute", "publish", "admin"],
    "smm_manager": ["read", "write", "approve", "publish"],
    "viewer": ["read"],
    "service_agent": ["read", "execute"]
}

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def require_role(required_permissions: list[str]):
    """Dependency to require specific role permissions."""
    def role_checker(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                credentials.credentials, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_role = payload.get("role", "viewer")
        user_permissions = ROLES.get(user_role, [])
        
        # Check if user has all required permissions
        if not all(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permissions}"
            )
        return payload
    return role_checker

# Permission-based dependencies
require_approver = require_role(["approve"])
require_publisher = require_role(["publish"])
require_writer = require_role(["write"])
require_viewer = require_role(["read"])
require_admin = require_role(["admin"])

# Backward-compatible aliases for existing imports
require_operator = require_writer  # Maps old operator to write permission
require_reader = require_viewer  # Alias for consistency

def create_test_token(role: str = "founder_admin") -> str:
    """Create a test JWT token for testing purposes."""
    return create_access_token({"sub": "test_user", "role": role})