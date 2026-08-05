"""
Embedding service for semantic search using sentence-transformers.
Loads a local model to avoid runtime downloads and ensure offline operation.
"""
import os
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from apps.api.config import settings

# Default model path (can be overridden by environment variable)
MODEL_DIR = settings.EMBEDDING_MODEL_DIR
MODEL_NAME = "all-MiniLM-L6-v2"

# Module-level singleton model instance
_model: Optional[SentenceTransformer] = None


def _get_model() -> SentenceTransformer:
    """Lazily load and return the sentence-transformer model singleton."""
    global _model
    if _model is None:
        # Try to load from local directory first (baked-in model)
        if os.path.exists(MODEL_DIR):
            _model = SentenceTransformer(MODEL_DIR)
        else:
            # Fallback to loading by name (will download if network available)
            _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_text(text: str) -> List[float]:
    """
    Embed a single text string into a 384-dimensional vector.
    
    Args:
        text: The text to embed
        
    Returns:
        A list of 384 float values representing the embedding
        
    Raises:
        ValueError: If text is None or empty
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty or None text")
    
    model = _get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed multiple text strings in batch for efficiency.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of 384-dimensional vectors (each as a list of floats)
        
    Raises:
        ValueError: If texts list is empty or contains empty strings
    """
    if not texts:
        raise ValueError("Cannot embed empty list of texts")
    
    # Filter out empty strings but keep original order for results
    valid_texts = []
    valid_indices = []
    for i, text in enumerate(texts):
        if text and text.strip():
            valid_texts.append(text)
            valid_indices.append(i)
    
    if not valid_texts:
        raise ValueError("All texts are empty or None")
    
    model = _get_model()
    embeddings = model.encode(valid_texts, convert_to_numpy=True)
    
    # Create result list with None for empty inputs
    result = [None] * len(texts)
    for idx, embedding in zip(valid_indices, embeddings):
        result[idx] = embedding.tolist()
    
    return result


def get_embedding_dimension() -> int:
    """Return the dimension of the embedding vectors."""
    return 384


def is_model_available() -> bool:
    """Check if the embedding model is available (local or can be loaded)."""
    try:
        _get_model()
        return True
    except Exception:
        return False