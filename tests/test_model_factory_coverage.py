"""Tests for model factory to improve coverage."""

import pytest
from unittest.mock import patch
from apps.core.models.factory import deepseek_fast, deepseek_reasoning


def test_deepseek_fast_without_key():
    """Test deepseek_fast function without API key."""
    with patch('apps.core.models.factory.settings') as mock_settings:
        mock_settings.deepseek_api_key = None
        result = deepseek_fast()
        assert result is None


def test_deepseek_fast_with_key():
    """Test deepseek_fast function with API key."""
    with patch('apps.core.models.factory.settings') as mock_settings:
        mock_settings.deepseek_api_key = "test_key"
        mock_settings.deepseek_primary_model = "deepseek/deepseek-v4-flash"
        mock_settings.deepseek_api_base = "https://api.deepseek.com"
        
        with patch('apps.core.models.factory.LiteLlm') as mock_llm:
            mock_instance = Mock()
            mock_llm.return_value = mock_instance
            
            result = deepseek_fast()
            assert result is not None


def test_deepseek_reasoning_without_key():
    """Test deepseek_reasoning function without API key."""
    with patch('apps.core.models.factory.settings') as mock_settings:
        mock_settings.deepseek_api_key = None
        result = deepseek_reasoning()
        assert result is None


def test_deepseek_reasoning_with_key():
    """Test deepseek_reasoning function with API key."""
    with patch('apps.core.models.factory.settings') as mock_settings:
        mock_settings.deepseek_api_key = "test_key"
        mock_settings.deepseek_reasoning_model = "deepseek/deepseek-v4-pro"
        mock_settings.deepseek_api_base = "https://api.deepseek.com"
        
        with patch('apps.core.models.factory.LiteLlm') as mock_llm:
            mock_instance = Mock()
            mock_llm.return_value = mock_instance
            
            result = deepseek_reasoning()
            assert result is not None