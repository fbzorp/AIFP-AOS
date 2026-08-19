"""Comprehensive tests for dispatcher to improve coverage."""

import pytest
from apps.integrations.publishing.dispatcher import get_publisher


def test_get_publisher_moltbook():
    """Test get_publisher for moltbook."""
    publisher = get_publisher("moltbook")
    assert publisher is not None


def test_get_publisher_x():
    """Test get_publisher for x."""
    publisher = get_publisher("x")
    assert publisher is not None


def test_get_publisher_telegram():
    """Test get_publisher for telegram."""
    publisher = get_publisher("telegram")
    assert publisher is not None


def test_get_publisher_google():
    """Test get_publisher for google/seo."""
    publisher = get_publisher("google")
    assert publisher is not None


def test_get_publisher_seo():
    """Test get_publisher for seo."""
    publisher = get_publisher("seo")
    assert publisher is not None


def test_get_publisher_blog():
    """Test get_publisher for blog."""
    publisher = get_publisher("blog")
    assert publisher is not None