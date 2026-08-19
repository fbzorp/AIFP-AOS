"""Test for policy engine to improve coverage."""

import pytest
from apps.core.policy.engine import compute_draft_hash, PolicyEngine


def test_compute_draft_hash():
    """Test draft hash computation."""
    class MockContent:
        title = "Test Title"
        body = "Test body content"
        channel = "test"
        objective = "test objective"
    
    content = MockContent()
    hash1 = compute_draft_hash(content)
    hash2 = compute_draft_hash(content)
    assert hash1 == hash2
    
    content.body = "different content"
    hash3 = compute_draft_hash(content)
    assert hash1 != hash3


def test_policy_engine_init():
    """Test PolicyEngine initialization."""
    engine = PolicyEngine()
    assert engine is not None