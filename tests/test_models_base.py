"""Tests for base model to improve coverage."""

import pytest
from apps.models.base import Base


def test_base_model_exists():
    """Test that Base model can be imported."""
    assert Base is not None


def test_base_model_has_metadata():
    """Test that Base has metadata."""
    assert hasattr(Base, 'metadata')