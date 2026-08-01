"""
Authentication and authorization tests.
Tests JWT-based authentication and RBAC functionality.
"""

import pytest
from apps.api.auth import create_access_token, ROLES, require_role


def test_jwt_token_creation():
    """Test that JWT tokens can be created successfully."""
    token = create_access_token({"sub": "test_user", "role": "admin"})
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_jwt_token_with_expiration():
    """Test that JWT tokens can be created with custom expiration."""
    from datetime import timedelta
    token = create_access_token({"sub": "test_user", "role": "admin"}, expires_delta=timedelta(hours=1))
    assert token is not None
    assert isinstance(token, str)


def test_role_definitions():
    """Test that role definitions are properly configured."""
    assert "admin" in ROLES
    assert "operator" in ROLES
    assert "viewer" in ROLES
    assert "read" in ROLES["admin"]
    assert "write" in ROLES["admin"]
    assert "approve" in ROLES["admin"]
    assert "execute" in ROLES["admin"]
    assert "execute" not in ROLES["operator"]
    assert "execute" not in ROLES["viewer"]


def test_require_role_dependency():
    """Test that require_role creates proper dependency."""
    # Test admin dependency
    admin_dependency = require_role(["read", "write", "approve", "execute"])
    assert admin_dependency is not None
    
    # Test operator dependency
    operator_dependency = require_role(["read", "write", "approve"])
    assert operator_dependency is not None
    
    # Test viewer dependency
    viewer_dependency = require_role(["read"])
    assert viewer_dependency is not None