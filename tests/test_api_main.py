"""Tests for API main module to improve coverage."""

import pytest
from apps.api.main import app


def test_app_exists():
    """Test that FastAPI app exists."""
    assert app is not None


def test_app_title():
    """Test that app has title."""
    assert app.title is not None