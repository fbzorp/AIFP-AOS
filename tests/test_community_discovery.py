"""Test for extended community engagement discovery."""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from apps.agents.specialized import GrowthOrchestratorAgent


@pytest.mark.asyncio
async def test_discover_moltbook_discussions_success():
    """Test Moltbook discussion discovery when configured."""
    with patch('apps.agents.specialized.settings') as mock_settings:
        mock_settings.MOLTBOOK_ALLOWED_SUBMOLTS = "general, aifintech"
        
        with patch('apps.agents.specialized.MoltbookClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock successful response
            mock_client.list_discussions = AsyncMock(return_value=[
                {"submolt": "general", "title": "Test Discussion 1", "content": "Content 1"},
                {"submolt": "aifintech", "title": "Test Discussion 2", "content": "Content 2"}
            ])
            
            agent = GrowthOrchestratorAgent()
            discussions = await agent._discover_moltbook_discussions(limit=10)
            
            assert len(discussions) == 2
            assert all(d.get("platform") == "moltbook" for d in discussions)
            assert discussions[0]["title"] == "Test Discussion 1"


@pytest.mark.asyncio
async def test_discover_moltbook_discussions_no_submolts():
    """Test Moltbook discovery when no submolts configured."""
    with patch('apps.agents.specialized.settings') as mock_settings:
        mock_settings.MOLTBOOK_ALLOWED_SUBMOLTS = ""
        
        agent = GrowthOrchestratorAgent()
        discussions = await agent._discover_moltbook_discussions(limit=10)
        
        assert len(discussions) == 0


@pytest.mark.asyncio
async def test_discover_moltbook_discussions_client_error():
    """Test Moltbook discovery when client fails."""
    with patch('apps.agents.specialized.settings') as mock_settings:
        mock_settings.MOLTBOOK_ALLOWED_SUBMOLTS = "general"
        
        with patch('apps.agents.specialized.MoltbookClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock client error
            mock_client.list_discussions = AsyncMock(side_effect=Exception("Connection error"))
            
            agent = GrowthOrchestratorAgent()
            discussions = await agent._discover_moltbook_discussions(limit=10)
            
            assert len(discussions) == 0


@pytest.mark.asyncio
async def test_discover_x_discussions_disabled():
    """Test X discovery when disabled."""
    with patch('apps.agents.specialized.settings') as mock_settings:
        mock_settings.X_SEARCH_ENABLED = "false"
        
        agent = GrowthOrchestratorAgent()
        discussions = await agent._discover_x_discussions(limit=10)
        
        assert len(discussions) == 0


@pytest.mark.asyncio
async def test_discover_x_discussions_no_queries():
    """Test X discovery when no queries configured."""
    with patch('apps.agents.specialized.settings') as mock_settings:
        mock_settings.X_SEARCH_ENABLED = "true"
        mock_settings.X_SEARCH_QUERIES = ""
        
        agent = GrowthOrchestratorAgent()
        discussions = await agent._discover_x_discussions(limit=10)
        
        assert len(discussions) == 0


@pytest.mark.asyncio
async def test_discover_x_discussions_with_queries():
    """Test X discovery with queries (returns empty due to implementation gap)."""
    with patch('apps.agents.specialized.settings') as mock_settings:
        mock_settings.X_SEARCH_ENABLED = "true"
        mock_settings.X_SEARCH_QUERIES = "ai fintech, autonomous systems"
        
        with patch('apps.agents.specialized.XClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            agent = GrowthOrchestratorAgent()
            discussions = await agent._discover_x_discussions(limit=10)
            
            # Should return empty since X search is not yet implemented
            assert len(discussions) == 0


@pytest.mark.asyncio
async def test_discover_allowed_discussions_combined():
    """Test combined discovery from multiple platforms."""
    with patch('apps.agents.specialized.settings') as mock_settings:
        mock_settings.MOLTBOOK_ALLOWED_SUBMOLTS = "general"
        mock_settings.X_SEARCH_ENABLED = "false"
        
        with patch('apps.agents.specialized.MoltbookClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_client.list_discussions = AsyncMock(return_value=[
                {"submolt": "general", "title": "Test Discussion", "content": "Content"}
            ])
            
            agent = GrowthOrchestratorAgent()
            discussions = await agent._discover_allowed_discussions(limit=10)
            
            assert len(discussions) == 1
            assert discussions[0]["platform"] == "moltbook"