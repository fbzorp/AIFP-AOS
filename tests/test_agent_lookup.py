import pytest
from apps.agents.registry import get_agent

def test_get_agent_by_display_name():
    """
    Test that get_agent correctly resolves agents using their display name.
    """
    orchestrator = get_agent("Growth Orchestrator")
    assert orchestrator is not None
    assert orchestrator.name == "Growth Orchestrator"
    
    market_intel = get_agent("Market Intelligence")
    assert market_intel is not None
    assert market_intel.name == "Market Intelligence"

def test_get_agent_not_found():
    """
    Test that get_agent returns None for non-existent agent names.
    """
    assert get_agent("Non Existent Agent") is None
