"""Tests for model factory to improve coverage."""

import pytest
from apps.core.models.factory import deepseek_fast, deepseek_reasoning


def test_deepseek_fast_without_key():
    """Test deepseek_fast function without API key."""
    with patch.dict('os.environ', {}, clear=True):
        result = deepseek_fast()
        assert result is None


def test_deepseek_fast_with_key():
    """Test deepseek_fast function with API key."""
    with patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test_key'}):
        result = deepseek_fast()
        assert result is not None


def test_deepseek_reasoning_without_key():
    """Test deepseek_reasoning function without API key."""
    with patch.dict('os.environ', {}, clear=True):
        result = deepseek_reasoning()
        assert result is None


def test_deepseek_reasoning_with_key():
    """Test deepseek_reasoning function with API key."""
    with patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test_key'}):
        result = deepseek_reasoning()
        assert result is not None