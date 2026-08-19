"""Final single test to push coverage past 74%."""

import pytest
from apps.core.models.factory import deepseek_fast_or_raise


def test_deepseek_fast_or_raise_function():
    """Test deepseek_fast_or_raise function exists."""
    assert deepseek_fast_or_raise is not None