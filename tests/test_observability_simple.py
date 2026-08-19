"""Test for observability module to improve coverage."""

import pytest
from apps.core.observability import setup_logging, RequestIDMiddleware


def test_setup_logging():
    """Test logging setup function."""
    setup_logging("INFO")
    # Should not raise any exception


def test_request_id_middleware_init():
    """Test RequestIDMiddleware initialization."""
    middleware = RequestIDMiddleware(None)
    assert middleware is not None