"""Tests for worker startup modules."""

from unittest.mock import patch
from apps.workers.startup import initialize_worker
from apps.workers.worker_bootstrap import broker


def test_initialize_worker():
    """Test worker initialization function."""
    with patch('apps.workers.startup.setup_scheduled_tasks') as mock_setup:
        initialize_worker()
        mock_setup.assert_called_once()


def test_worker_bootstrap_exports_broker():
    """Test that worker_bootstrap exports broker."""
    assert broker is not None
