"""Test for dispatcher to improve coverage."""

import pytest
from apps.integrations.publishing.dispatcher import get_publisher


def test_get_publisher_moltbook():
    """Test getting Moltbook publisher."""
    publisher = get_publisher("moltbook")
    assert publisher is not None


def test_get_publisher_x():
    """Test getting X publisher."""
    publisher = get_publisher("x")
    assert publisher is not None


def test_get_publisher_telegram():
    """Test getting Telegram publisher."""
    publisher = get_publisher("telegram")
    assert publisher is not None


def test_get_publisher_seo():
    """Test getting SEO publisher."""
    publisher = get_publisher("seo")
    assert publisher is not None