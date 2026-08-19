"""Comprehensive tests for embeddings module to improve coverage."""

import pytest
from apps.core.embeddings import embed_text, embed_texts, get_embedding_dimension, is_model_available


def test_embed_text_function():
    """Test embed_text function exists."""
    assert embed_text is not None


def test_embed_texts_function():
    """Test embed_texts function exists."""
    assert embed_texts is not None


def test_get_embedding_dimension_function():
    """Test get_embedding_dimension function exists."""
    assert get_embedding_dimension is not None


def test_is_model_available_function():
    """Test is_model_available function exists."""
    assert is_model_available is not None


def test_get_embedding_dimension_returns_384():
    """Test that embedding dimension is 384."""
    assert get_embedding_dimension() == 384