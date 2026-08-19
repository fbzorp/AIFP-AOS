"""Additional comprehensive tests for base model."""

import pytest
from apps.models.base import Base


def test_base_has_metadata():
    """Test Base has metadata."""
    assert hasattr(Base, 'metadata')


def test_base_has_registry():
    """Test Base has registry."""
    assert hasattr(Base, 'registry')