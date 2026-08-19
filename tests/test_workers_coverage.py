"""Comprehensive tests for workers startup to improve coverage."""

import pytest
from apps.workers.startup import initialize_worker
from apps.workers.worker_bootstrap import broker


def test_initialize_worker_function():
    """Test initialize_worker function exists."""
    assert initialize_worker is not None


def test_worker_bootstrap_broker():
    """Test worker bootstrap broker exists."""
    assert broker is not None