"""Simple test to improve coverage for low-coverage modules."""

import pytest
from apps.core.sanitizer import sanitize_external
from apps.core.news_fetcher import NewsFetcher


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


def test_news_fetcher_initialization():
    """Test NewsFetcher initialization."""
    fetcher = NewsFetcher()
    assert fetcher is not None


def test_news_fetcher_no_keys():
    """Test NewsFetcher when no API keys are configured."""
    fetcher = NewsFetcher()
    assert fetcher.news_api_key is None
    assert fetcher.serper_api_key is None