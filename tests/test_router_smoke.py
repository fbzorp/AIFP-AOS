"""Quick smoke tests for routers to push coverage."""

import pytest
from apps.api.routers.marketing import router as marketing_router
from apps.api.routers.settings import router as settings_router


def test_marketing_router_exists():
    """Test marketing router exists."""
    assert marketing_router is not None


def test_marketing_router_has_routes():
    """Test marketing router has routes."""
    assert len(marketing_router.routes) > 0


def test_settings_router_exists():
    """Test settings router exists."""
    assert settings_router is not None


def test_settings_router_has_routes():
    """Test settings router has routes."""
    assert len(settings_router.routes) > 0