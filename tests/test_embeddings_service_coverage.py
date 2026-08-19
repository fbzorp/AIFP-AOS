"""Tests for embeddings module to improve coverage."""

import pytest
from unittest.mock import Mock, patch
from apps.core.embeddings import EmbeddingService


def test_embedding_service_initialization():
    """Test EmbeddingService initialization."""
    with patch('apps.core.embeddings.SentenceTransformer') as mock_model:
        mock_instance = Mock()
        mock_instance.encode = Mock(return_value=[[0.1, 0.2, 0.3]])
        mock_model.return_value = mock_instance
        
        service = EmbeddingService()
        assert service is not None


def test_embedding_service_encode():
    """Test text encoding."""
    with patch('apps.core.embeddings.SentenceTransformer') as mock_model:
        mock_instance = Mock()
        mock_instance.encode = Mock(return_value=[[0.1, 0.2, 0.3]])
        mock_model.return_value = mock_instance
        
        service = EmbeddingService()
        result = service.encode("test text")
        
        assert result is not None
        mock_instance.encode.assert_called_once()


def test_embedding_service_encode_batch():
    """Test batch text encoding."""
    with patch('apps.core.embeddings.SentenceTransformer') as mock_model:
        mock_instance = Mock()
        mock_instance.encode = Mock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_model.return_value = mock_instance
        
        service = EmbeddingService()
        result = service.encode_batch(["text1", "text2"])
        
        assert result is not None
        assert len(result) == 2