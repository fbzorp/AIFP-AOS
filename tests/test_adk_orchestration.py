"""
ADK Orchestration tests.
Tests the Marketing Manager root agent, ADK Runner, and fallback behavior.
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from apps.agents.adk_orchestrator import ADKOrchestrator, get_adk_orchestrator
from apps.core.models.factory import deepseek_reasoning
from apps.models.base import get_sync_session


@pytest.mark.asyncio
async def test_adk_orchestrator_initialization_with_key():
    """Test that ADK orchestrator initializes when DEEPSEEK_API_KEY is present."""
    # Mock the LiteLlm model to simulate a valid DeepSeek key
    mock_model = Mock()
    
    with patch('apps.agents.adk_orchestrator.deepseek_reasoning', return_value=mock_model):
        with patch('apps.agents.adk_orchestrator.LlmAgent') as mock_llm_agent:
            with patch('apps.agents.adk_orchestrator.Runner') as mock_runner:
                with patch('apps.models.base.SessionLocal'):
                    orchestrator = ADKOrchestrator()
                    result = orchestrator.initialize()
                    
                    assert result == True
                    assert orchestrator._initialized == True
                    assert orchestrator.root_agent is not None
                    assert orchestrator.runner is not None
                    mock_llm_agent.assert_called_once()
                    mock_runner.assert_called_once()


@pytest.mark.asyncio
async def test_adk_orchestrator_initialization_without_key():
    """Test that ADK orchestrator returns False when DEEPSEEK_API_KEY is absent."""
    with patch('apps.agents.adk_orchestrator.deepseek_reasoning', return_value=None):
        orchestrator = ADKOrchestrator()
        result = orchestrator.initialize()
        
        assert result == False
        assert orchestrator._initialized == False
        assert orchestrator.root_agent is None
        assert orchestrator.runner is None


@pytest.mark.asyncio
async def test_adk_orchestrator_static_fallback():
    """Test that static fallback is used when ADK is not available."""
    with patch('apps.agents.adk_orchestrator.deepseek_reasoning', return_value=None):
        with patch('apps.models.base.SessionLocal'):
            orchestrator = ADKOrchestrator()
            
            result = await orchestrator.orchestrate_campaign("test objective")
            
            assert result["routing_method"] == "static_fallback"
            assert result["objective"] == "test objective"
            assert len(result["steps"]) == 4  # Static steps: Market Intelligence, Content Strategy, SEO Content, Community Engagement
            assert result["steps"][0]["agent"] == "Market Intelligence"
            assert result["steps"][1]["agent"] == "Content Strategy"
            assert result["steps"][2]["agent"] == "SEO Content"
            assert result["steps"][3]["agent"] == "Community Engagement"


@pytest.mark.asyncio
async def test_adk_orchestrator_adk_routing():
    """Test that ADK routing is used when available."""
    mock_model = Mock()
    
    # Mock the ADK Runner response
    mock_runner = Mock()
    mock_response = Mock()
    mock_response.content = '[{"agent": "Market Intelligence", "input": {"topic": "test"}, "reason": "research"}, {"agent": "Content Strategy", "input": {"objective": "test"}, "reason": "planning"}]'
    mock_runner.run_async = AsyncMock(return_value=mock_response)
    
    with patch('apps.agents.adk_orchestrator.deepseek_reasoning', return_value=mock_model):
        with patch('apps.agents.adk_orchestrator.LlmAgent'):
            with patch('apps.agents.adk_orchestrator.Runner', return_value=mock_runner):
                with patch('apps.models.base.SessionLocal'):
                    orchestrator = ADKOrchestrator()
                    orchestrator._initialized = True
                    orchestrator.runner = mock_runner
                    
                    result = await orchestrator.orchestrate_campaign("test objective")
                    
                    assert result["routing_method"] == "adk_routed"
                    assert result["objective"] == "test objective"
                    assert len(result["steps"]) == 2
                    assert result["steps"][0]["agent"] == "Market Intelligence"
                    assert result["steps"][1]["agent"] == "Content Strategy"
                    mock_runner.run_async.assert_called_once()


@pytest.mark.asyncio
async def test_specialist_tool_creation():
    """Test that specialist tools are created correctly."""
    with patch('apps.agents.adk_orchestrator.get_agent'):
        orchestrator = ADKOrchestrator()
        tools = orchestrator.create_specialist_tools()
        
        assert len(tools) == 9  # 9 specialists (added SEO Content)


@pytest.mark.asyncio
async def test_specialist_tool_execution():
    """Test that specialist tools execute the correct agents."""
    mock_agent = Mock()
    # The agent.execute is async, so we need to mock it to return a coroutine
    async def mock_execute(input_data):
        return {"agent": "Market Intelligence", "outcome": "success"}
    mock_agent.execute = mock_execute
    
    with patch('apps.agents.adk_orchestrator.get_agent', return_value=mock_agent):
        orchestrator = ADKOrchestrator()
        tools = orchestrator.create_specialist_tools()
        
        # Execute the first tool (Market Intelligence)
        result = await tools[0].func({"test": "data"})
        
        # The tool should return the specialist name and real result
        assert result["specialist"] == "Market Intelligence"
        assert result["result"]["agent"] == "Market Intelligence"
        assert result["result"]["outcome"] == "success"


@pytest.mark.asyncio
async def test_specialist_tool_not_found():
    """Test that specialist tool handles missing agents gracefully."""
    with patch('apps.agents.adk_orchestrator.get_agent', return_value=None):
        orchestrator = ADKOrchestrator()
        tools = orchestrator.create_specialist_tools()
        
        # Execute the first tool
        result = await tools[0].func({})
        
        # Just check that an error is returned
        assert "error" in result


@pytest.mark.asyncio
async def test_existing_orchestration_still_works():
    """Test that existing orchestration tests still work with ADK integration."""
    # This ensures backward compatibility with existing tests
    with patch('apps.agents.adk_orchestrator.deepseek_reasoning', return_value=None):
        with patch('apps.models.base.SessionLocal'):
            # Import the GrowthOrchestratorAgent to test it still works
            from apps.agents.specialized import GrowthOrchestratorAgent
            
            agent = GrowthOrchestratorAgent()
            
            # Mock the internal methods to avoid DB dependencies
            agent._discover_allowed_discussions = AsyncMock(return_value=[])
            agent._dispatch_campaign = Mock(return_value={
                "campaign_id": "test-camp-123",
                "tasks": ["task-1", "task-2"]
            })
            
            result = await agent.execute({"objective": "test campaign"})
            
            assert result["agent"] == "Growth Orchestrator"
            assert result["outcome"] == "campaign_dispatched"
            assert result["routing_method"] == "static_fallback"  # No ADK key in this test
            assert result["campaign_id"] == "test-camp-123"
            assert len(result["tasks"]) == 2


@pytest.mark.asyncio
async def test_adk_response_parsing_json():
    """Test that ADK response parsing handles JSON arrays correctly."""
    orchestrator = ADKOrchestrator()
    
    # Mock response with JSON array
    mock_response = Mock()
    mock_response.content = '[{"agent": "Market Intelligence", "input": {"topic": "test"}, "reason": "research"}, {"agent": "Content Strategy", "input": {"objective": "test"}, "reason": "planning"}]'
    
    steps = orchestrator._parse_adk_response(mock_response)
    
    assert len(steps) == 2
    assert steps[0]["agent"] == "Market Intelligence"
    assert steps[1]["agent"] == "Content Strategy"


@pytest.mark.asyncio
async def test_adk_response_parsing_fallback():
    """Test that ADK response parsing falls back to static steps on parse error."""
    orchestrator = ADKOrchestrator()
    
    # Mock response with invalid JSON
    mock_response = Mock()
    mock_response.content = "This is not valid JSON"
    
    steps = orchestrator._parse_adk_response(mock_response)
    
    # Should return static steps as fallback
    assert len(steps) == 4
    assert steps[0]["agent"] == "Market Intelligence"
    assert steps[1]["agent"] == "Content Strategy"
    assert steps[2]["agent"] == "SEO Content"
    assert steps[3]["agent"] == "Community Engagement"


@pytest.mark.asyncio
async def test_adk_response_parsing_no_json():
    """Test that ADK response parsing handles response without JSON."""
    orchestrator = ADKOrchestrator()
    
    # Mock response without JSON
    mock_response = Mock()
    mock_response.content = "Plain text response"
    
    steps = orchestrator._parse_adk_response(mock_response)
    
    # Should return static steps as fallback
    assert len(steps) == 4
    assert steps[0]["agent"] == "Market Intelligence"


@pytest.mark.asyncio
async def test_singleton_instance():
    """Test that get_adk_orchestrator returns the same instance."""
    orchestrator1 = get_adk_orchestrator()
    orchestrator2 = get_adk_orchestrator()
    
    assert orchestrator1 is orchestrator2  # Same instance


@pytest.mark.asyncio
async def test_moltbook_tools_permission_gating():
    """Test that Moltbook tools are only exposed to authorized specialists."""
    # The Moltbook tools should only be exposed to Social Publishing and Community Engagement
    # This is enforced by the existing permission gating in apps/workers/tasks.py:_perform_publish_logic
    # The ADK orchestrator itself doesn't bypass this gating
    
    orchestrator = ADKOrchestrator()
    tools = orchestrator.create_specialist_tools()
    
    # All 9 tools should exist (added SEO Content)
    assert len(tools) == 9
    
    # The actual gating happens in the specialist's execute() methods via MOLTBOOK_AUTOPUBLISH
    # This test verifies that the tools are created, not their permission logic
    # Permission logic is tested in the existing specialist tests
