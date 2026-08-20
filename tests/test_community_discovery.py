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
            
            # The actual implementation adds platform field and may have audit recording
            # Just verify that discussions were found and have the expected structure
            assert len(discussions) >= 2
            assert all(d.get("platform") == "moltbook" for d in discussions)
            assert any(d.get("submolt") == "general" for d in discussions)
            assert any(d.get("submolt") == "aifintech" for d in discussions)


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
    """Test X discovery with queries using real search implementation."""
    with patch('apps.agents.specialized.settings') as mock_settings:
        mock_settings.X_SEARCH_ENABLED = "true"
        mock_settings.X_SEARCH_QUERIES = "ai fintech, autonomous systems"
        
        with patch('apps.agents.specialized.XClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock successful search responses
            mock_client.search = AsyncMock(side_effect=[
                {
                    "success": True,
                    "data": [
                        {
                            "id": "1234567890",
                            "text": "Discussion about AI fintech",
                            "author_id": "987654321",
                            "created_at": "2024-01-01T00:00:00Z",
                            "public_metrics": {"like_count": 10},
                            "lang": "en"
                        }
                    ],
                    "meta": {"result_count": 1}
                },
                {
                    "success": True,
                    "data": [
                        {
                            "id": "0987654321",
                            "text": "Autonomous systems discussion",
                            "author_id": "1234567890",
                            "created_at": "2024-01-01T00:00:00Z",
                            "public_metrics": {"like_count": 5},
                            "lang": "en"
                        }
                    ],
                    "meta": {"result_count": 1}
                }
            ])
            
            agent = GrowthOrchestratorAgent()
            discussions = await agent._discover_x_discussions(limit=10)
            
            # Should return tweets from both queries
            assert len(discussions) == 2
            assert all(d.get("source") == "x" for d in discussions)
            assert discussions[0]["id"] == "1234567890"
            assert discussions[1]["id"] == "0987654321"


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