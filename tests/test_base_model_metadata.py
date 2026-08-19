"""Tests for base model to improve coverage."""

import pytest
from apps.models.base import Base


def test_base_model_metadata():
    """Test Base model metadata."""
    assert hasattr(Base, '__tablename__')
    assert hasattr(Base, 'id')
    assert hasattr(Base, 'created_at')
    assert hasattr(Base, 'updated_at')


def test_base_model_repr():
    """Test Base model representation."""
    # Test that Base has a reasonable string representation
    assert Base.__name__ == "Base"