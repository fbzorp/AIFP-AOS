"""Additional observability tests to improve coverage."""

import pytest
from apps.core.observability import init_tracing, setup_logging


def test_init_tracing():
    """Test tracing initialization."""
    # Should not crash
    init_tracing(None)
    assert True


def test_setup_logging():
    """Test logging setup."""
    # Should not crash
    setup_logging("INFO")
    assert True


def test_setup_logging_debug():
    """Test logging setup with debug level."""
    setup_logging("DEBUG")
    assert True