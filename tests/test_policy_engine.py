"""Tests for policy engine to improve coverage."""

import pytest
from apps.core.policy.engine import PolicyEngine, compute_draft_hash


def test_policy_engine_initialization():
    """Test policy engine initialization."""
    engine = PolicyEngine()
    assert engine is not None


def test_compute_draft_hash():
    """Test draft hash computation."""
    class MockContentItem:
        def __init__(self):
            self.title = "Test Title"
            self.body = "Test Body"
            self.channel = "test"
            self.objective = "test objective"
    
    content = MockContentItem()
    hash_value = compute_draft_hash(content)
    assert hash_value is not None
    assert len(hash_value) == 64  # SHA256 hash length


def test_compute_draft_hash_deterministic():
    """Test that hash computation is deterministic."""
    class MockContentItem:
        def __init__(self):
            self.title = "Test Title"
            self.body = "Test Body"
            self.channel = "test"
            self.objective = "test objective"
    
    content1 = MockContentItem()
    content2 = MockContentItem()
    
    hash1 = compute_draft_hash(content1)
    hash2 = compute_draft_hash(content2)
    
    assert hash1 == hash2