"""Tests for embeddings module to improve coverage."""

import pytest
import numpy as np
from unittest.mock import patch, Mock
from apps.core.embeddings import embed_text, embed_texts, get_embedding_dimension, is_model_available


def test_embed_text():
    """Test text embedding."""
    with patch('apps.core.embeddings.SentenceTransformer') as mock_model:
        mock_instance = Mock()
        # Return numpy array that has tolist() method
        mock_array = np.array([0.1] * 384)
        mock_instance.encode = Mock(return_value=mock_array)
        mock_model.return_value = mock_instance
        
        result = embed_text("test text")
        assert result is not None
        assert len(result) == 384  # Actual embedding dimension


def test_embed_text_empty():
    """Test text embedding with empty string raises error."""
    with pytest.raises(ValueError):
        embed_text("")


def test_embed_texts():
    """Test batch text embedding."""
    with patch('apps.core.embeddings.SentenceTransformer') as mock_model:
        mock_instance = Mock()
        # Return numpy array that has tolist() method
        mock_array = np.array([[0.1] * 384, [0.2] * 384])
        mock_instance.encode = Mock(return_value=mock_array)
        mock_model.return_value = mock_instance
        
        result = embed_texts(["text1", "text2"])
        assert result is not None
        assert len(result) == 2


def test_embed_texts_empty():
    """Test batch text embedding with empty list raises error."""
    with pytest.raises(ValueError):
        embed_texts([])


def test_get_embedding_dimension():
    """Test getting embedding dimension."""
    result = get_embedding_dimension()
    assert result == 384


def test_is_model_available():
    """Test checking if model is available."""
    with patch('apps.core.embeddings.SentenceTransformer') as mock_model:
        mock_instance = Mock()
        mock_model.return_value = mock_instance
        
        result = is_model_available()
        assert result is True