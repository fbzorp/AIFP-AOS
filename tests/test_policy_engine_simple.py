"""Test for policy engine to improve coverage."""

import pytest
from apps.core.policy.engine import compute_draft_hash, validate_approval


def test_compute_draft_hash():
    """Test draft hash computation."""
    hash1 = compute_draft_hash("test content")
    hash2 = compute_draft_hash("test content")
    assert hash1 == hash2
    
    hash3 = compute_draft_hash("different content")
    assert hash1 != hash3


def test_validate_approval():
    """Test approval validation."""
    # Test with matching hash
    is_valid = validate_approval("test_content", "test_content")
    assert is_valid is True
    
    # Test with different content
    is_invalid = validate_approval("test_content", "modified content")
    assert is_invalid is False