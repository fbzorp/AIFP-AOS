"""Simple test to improve coverage for low-coverage modules."""

import pytest
from apps.core.sanitizer import sanitize_external


def test_sanitize_external():
    """Test external content sanitization."""
    result = sanitize_external("test content")
    assert result is not None
    assert isinstance(result, str)


def test_sanitize_external_with_html():
    """Test sanitization removes HTML tags."""
    result = sanitize_external("<script>alert('xss')</script>test")
    assert "<script>" not in result
    assert "test" in result