import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from apps.models.base import Base, get_sync_session
from apps.models.engagement_proposal import EngagementProposalModel
from apps.agents.specialized import CommunityEngagementAgent

# Setup in-memory SQLite for testing
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@patch("apps.agents.specialized.get_sync_session")
@patch("apps.agents.specialized.complete_json")
@pytest.mark.asyncio
async def test_community_engagement_agent_creates_proposals(mock_complete_json, mock_get_session):
    session = TestingSessionLocal()
    mock_get_session.return_value.__enter__.return_value = session
    
    mock_complete_json.return_value = {
        "discussion_summary": "Users talking about SDK",
        "proposed_reply": "Check out our latest SDK update!"
    }
    
    agent = CommunityEngagementAgent()
    input_data = {
        "discussions": [
            {"url": "https://moltbook.com/posts/1", "submolt": "aifintech", "content": "How do I use x402?"}
        ]
    }
    
    result = await agent.execute(input_data)
    
    assert result["outcome"] == "proposals_created"
    assert len(result["proposal_ids"]) == 1
    
    proposal = session.query(EngagementProposalModel).first()
    assert proposal is not None
    assert proposal.status == "proposed"
    assert proposal.submolt == "aifintech"
    assert "x402" in proposal.proposed_reply or "SDK" in proposal.proposed_reply
