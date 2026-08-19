"""Tests for model factory to improve coverage."""

import pytest
from unittest.mock import patch
from apps.core.models.factory import deepseek_fast, deepseek_reasoning


def test_deepseek_fast_no_key():
    """Test deepseek_fast without API key returns None."""
    with patch('apps.core.models.factory.settings') as mock_settings:
        mock_settings.deepseek_api_key = None
        result = deepseek_fast()
        assert result is None


def test_deepseek_reasoning_no_key():
    """Test deepseek_reasoning without API key returns None."""
    with patch('apps.core.models.factory.settings') as mock_settings:
        mock_settings.deepseek_api_key = None
        result = deepseek_reasoning()
        assert result is None