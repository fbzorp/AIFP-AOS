"""Test for orchestrator engine to improve coverage."""

import pytest
from unittest.mock import Mock
from apps.core.orchestrator.engine import Orchestrator


def test_orchestrator_init():
    """Test Orchestrator initialization."""
    mock_session = Mock()
    orchestrator = Orchestrator(mock_session)
    assert orchestrator is not None
    assert orchestrator.session == mock_session