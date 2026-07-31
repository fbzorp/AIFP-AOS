"""
Authentication and authorization tests.
RBAC implementation deferred to Day 14 - tests skipped until then.
"""

import pytest


@pytest.mark.skip(reason="RBAC implementation deferred to Day 14")
def test_unauthenticated_access_protection():
    """Test that protected endpoints require authentication.
    This test will be implemented in Day 14 when JWT authentication is added."""
    pass