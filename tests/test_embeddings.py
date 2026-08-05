import pytest
from unittest.mock import patch
from apps.core.embeddings import embed_text, embed_texts, get_embedding_dimension, is_model_available

@pytest.mark.skipif(
    not is_model_available(),
    reason="Embedding model not available (requires baked-in model or network access)"
)
def test_embed_text_returns_384_dimensions():
    """Test that embed_text returns a 384-dimensional vector."""
    text = "Test text for embedding."
    embedding = embed_text(text)
    
    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)

@pytest.mark.skipif(
    not is_model_available(),
    reason="Embedding model not available (requires baked-in model or network access)"
)
def test_embed_text_with_empty_text():
    """Test that embed_text raises ValueError for empty text."""
    with pytest.raises(ValueError, match="Cannot embed empty or None text"):
        embed_text("")
    
    with pytest.raises(ValueError, match="Cannot embed empty or None text"):
        embed_text(None)

@pytest.mark.skipif(
    not is_model_available(),
    reason="Embedding model not available (requires baked-in model or network access)"
)
def test_embed_texts_batch():
    """Test that embed_texts handles multiple texts in batch."""
    texts = [
        "First test text.",
        "Second test text.",
        "Third test text."
    ]
    
    embeddings = embed_texts(texts)
    
    assert len(embeddings) == 3
    for embedding in embeddings:
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

@pytest.mark.skipif(
    not is_model_available(),
    reason="Embedding model not available (requires baked-in model or network access)"
)
def test_embed_texts_with_empty_list():
    """Test that embed_texts raises ValueError for empty list."""
    with pytest.raises(ValueError, match="Cannot embed empty list of texts"):
        embed_texts([])

@pytest.mark.skipif(
    not is_model_available(),
    reason="Embedding model not available (requires baked-in model or network access)"
)
def test_embed_texts_with_all_empty_strings():
    """Test that embed_texts raises ValueError when all texts are empty."""
    with pytest.raises(ValueError, match="All texts are empty or None"):
        embed_texts(["", "   ", None])

def test_get_embedding_dimension():
    """Test that get_embedding_dimension returns 384."""
    assert get_embedding_dimension() == 384

def test_embed_text_with_mock():
    """Test embed_text with mocked model for testing without actual model."""
    with patch("apps.core.embeddings._get_model") as mock_model:
        import numpy as np
        mock_model.return_value.encode.return_value = np.array([0.1] * 384)
        
        embedding = embed_text("Test text")
        
        assert len(embedding) == 384
        assert embedding == [0.1] * 384
        mock_model.return_value.encode.assert_called_once()

def test_embed_texts_with_mock():
    """Test embed_texts with mocked model for testing without actual model."""
    with patch("apps.core.embeddings._get_model") as mock_model:
        import numpy as np
        mock_model.return_value.encode.return_value = np.array([[0.1] * 384, [0.2] * 384])
        
        embeddings = embed_texts(["Text 1", "Text 2"])
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384
        assert len(embeddings[1]) == 384
        assert embeddings[0] == [0.1] * 384
        assert embeddings[1] == [0.2] * 384