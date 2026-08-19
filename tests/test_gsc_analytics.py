"""Test for Google Search Console analytics integration."""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, patch
from apps.integrations.analytics.gsc_client import GoogleSearchConsoleClient


def test_gsc_client_not_configured():
    """Test GSC client when credentials are not configured."""
    with patch('apps.integrations.analytics.gsc_client.settings') as mock_settings:
        mock_settings.GOOGLE_SEARCH_CONSOLE_JSON_KEY = None
        
        client = GoogleSearchConsoleClient()
        assert client.is_configured is False


def test_gsc_client_configured():
    """Test GSC client when credentials are configured."""
    with patch('apps.integrations.analytics.gsc_client.settings') as mock_settings:
        mock_settings.GOOGLE_SEARCH_CONSOLE_JSON_KEY = "fake_json_key"
        
        client = GoogleSearchConsoleClient()
        assert client.is_configured is True


@pytest.mark.asyncio
async def test_gsc_fetch_search_analytics_not_configured():
    """Test fetching search analytics when not configured."""
    with patch('apps.integrations.analytics.gsc_client.settings') as mock_settings:
        mock_settings.GOOGLE_SEARCH_CONSOLE_JSON_KEY = None
        
        client = GoogleSearchConsoleClient()
        result = await client.fetch_search_analytics(
            url="https://example.com",
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        
        assert result["available"] is False
        assert result["data_source"] == "Google Search Console"
        assert result["message"] == "unavailable/not configured"
        assert "error" in result


@pytest.mark.asyncio
async def test_gsc_fetch_search_analytics_configured():
    """Test fetching search analytics when configured (returns unavailable due to missing lib)."""
    with patch('apps.integrations.analytics.gsc_client.settings') as mock_settings:
        mock_settings.GOOGLE_SEARCH_CONSOLE_JSON_KEY = "fake_json_key"
        
        client = GoogleSearchConsoleClient()
        result = await client.fetch_search_analytics(
            url="https://example.com",
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        
        # Should return unavailable due to missing google-auth library
        assert result["available"] is False
        assert result["data_source"] == "Google Search Console"
        assert "error" in result


@pytest.mark.asyncio
async def test_gsc_get_site_metrics_not_configured():
    """Test getting site metrics when not configured."""
    with patch('apps.integrations.analytics.gsc_client.settings') as mock_settings:
        mock_settings.GOOGLE_SEARCH_CONSOLE_JSON_KEY = None
        
        client = GoogleSearchConsoleClient()
        result = await client.get_site_metrics("https://example.com")
        
        assert result["available"] is False
        assert result["data_source"] == "Google Search Console"
        assert result["message"] == "unavailable/not configured"


@pytest.mark.asyncio
async def test_gsc_get_site_metrics_configured():
    """Test getting site metrics when configured (returns unavailable due to missing lib)."""
    with patch('apps.integrations.analytics.gsc_client.settings') as mock_settings:
        mock_settings.GOOGLE_SEARCH_CONSOLE_JSON_KEY = "fake_json_key"
        
        client = GoogleSearchConsoleClient()
        result = await client.get_site_metrics("https://example.com")
        
        # Should return unavailable due to missing google-auth library
        assert result["available"] is False
        assert result["data_source"] == "Google Search Console"
        assert "error" in result