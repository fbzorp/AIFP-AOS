"""Test for orchestrator engine to improve coverage."""

import pytest
from apps.core.orchestrator.engine import Orchestrator


def test_orchestrator_init():
    """Test Orchestrator initialization."""
    orchestrator = Orchestrator()
    assert orchestrator is not None