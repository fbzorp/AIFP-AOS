import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock, patch

from apps.agents.specialized import AnalyticsAgent, CommunityEngagementAgent
from apps.integrations.moltbook.client import MoltbookClient
from apps.models.audit_event import AuditEventModel
from apps.models.base import Base
from apps.models.content_item import ContentItemModel
from apps.models.engagement_proposal import EngagementProposalModel


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


@pytest.mark.asyncio
async def test_discover_discussions_uses_read_only_semantic_search_and_normalizes_posts():
    observed_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        observed_request["method"] = request.method
        observed_request["path"] = request.url.path
        observed_request["authorization"] = request.headers.get("Authorization")
        observed_request["params"] = dict(request.url.params)
        return httpx.Response(
            200,
            json={
                "success": True,
                "results": [
                    {
                        "id": "post-123",
                        "type": "post",
                        "title": "x402 payment flow question",
                        "content": "How can an AI agent safely use x402 payments?",
                        "similarity": 0.92,
                        "author": {"name": "PaymentMolty"},
                        "submolt": {"name": "aifintech"},
                    },
                    {
                        "id": "comment-456",
                        "type": "comment",
                        "content": "This comment must not become a proposal.",
                    },
                    {
                        "id": "post-789",
                        "type": "post",
                        "content": "",
                        "submolt": {"name": "aifintech"},
                    },
                ],
            },
        )

    client = MoltbookClient(
        base_url="https://www.moltbook.com",
        agent_key="unit-test-agent-key",
        app_key="unit-test-app-key",
    )
    await client.close()
    client.http = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    try:
        discussions = await client.discover_discussions(
            query="safe x402 payment flows for AI agents",
            limit=20,
        )
    finally:
        await client.close()

    assert observed_request == {
        "method": "GET",
        "path": "/api/v1/search",
        "authorization": "Bearer unit-test-agent-key",
        "params": {
            "q": "safe x402 payment flows for AI agents",
            "type": "posts",
            "limit": "20",
        },
    }
    assert discussions == [
        {
            "url": "https://www.moltbook.com/posts/post-123",
            "post_id": "post-123",
            "submolt": "aifintech",
            "content": "x402 payment flow question\n\nHow can an AI agent safely use x402 payments?",
            "author": "PaymentMolty",
            "similarity": 0.92,
        }
    ]


@pytest.mark.asyncio
async def test_discover_discussions_rejects_invalid_search_parameters_without_network_calls():
    client = MoltbookClient(
        base_url="https://www.moltbook.com",
        agent_key="unit-test-agent-key",
        app_key="unit-test-app-key",
    )
    try:
        with pytest.raises(ValueError, match="at most 500 characters"):
            await client.discover_discussions(query="x" * 501)
        with pytest.raises(ValueError, match="integer from 1 to 50"):
            await client.discover_discussions(query="x402", limit=51)
    finally:
        await client.close()


@patch("apps.agents.specialized.get_sync_session")
@pytest.mark.asyncio
async def test_analytics_agent_counts_real_published_content_and_successful_mcp_events(
    mock_get_session,
):
    session = TestingSessionLocal()
    mock_get_session.return_value.__enter__.return_value = session

    session.add_all(
        [
            ContentItemModel(
                id="published-content",
                title="Published",
                channel="Moltbook",
                status="published",
            ),
            ContentItemModel(
                id="draft-content",
                title="Draft",
                channel="Moltbook",
                status="draft",
            ),
            AuditEventModel(
                id="mcp-success",
                agent_name="Payments",
                event_type="mcp_call_succeeded",
                message="MCP call completed",
            ),
            AuditEventModel(
                id="mcp-failed",
                agent_name="Payments",
                event_type="mcp_call_failed",
                message="MCP call failed",
            ),
        ]
    )
    session.commit()

    result = await AnalyticsAgent().execute({})

    assert result["agent"] == "Analytics Agent"
    assert result["outcome"] == "metrics_generated"
    assert result["report"]["publications"] == 1
    assert result["report"]["mcp_calls"] == 1
    assert session.query(AuditEventModel).filter(
        AuditEventModel.event_type == "metrics_reported"
    ).count() == 1


@patch("apps.agents.specialized.MoltbookClient")
@patch("apps.agents.specialized.get_sync_session")
@patch("apps.agents.specialized.complete_json")
@pytest.mark.asyncio
async def test_community_engagement_discovers_posts_before_creating_approval_gated_proposals(
    mock_complete_json,
    mock_get_session,
    mock_moltbook_client,
):
    session = TestingSessionLocal()
    mock_get_session.return_value.__enter__.return_value = session
    mock_complete_json.return_value = {
        "discussion_summary": "An agent needs guidance on x402 payments.",
        "proposed_reply": "AiFinPay can help with an approval-gated x402 payment flow.",
    }

    discovered_discussions = [
        {
            "url": "https://www.moltbook.com/posts/post-123",
            "post_id": "post-123",
            "submolt": "aifintech",
            "content": "How can an AI agent safely use x402 payments?",
            "author": "PaymentMolty",
            "similarity": 0.92,
        }
    ]
    mock_client = MagicMock()
    mock_client.discover_discussions = AsyncMock(return_value=discovered_discussions)
    mock_moltbook_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_moltbook_client.return_value.__aexit__ = AsyncMock(return_value=None)

    result = await CommunityEngagementAgent().execute(
        {"query": "safe x402 payment flows for AI agents", "limit": 20}
    )

    mock_client.discover_discussions.assert_awaited_once_with(
        query="safe x402 payment flows for AI agents",
        limit=20,
        cursor=None,
    )
    assert result["outcome"] == "proposals_created"
    assert len(result["proposal_ids"]) == 1

    proposal = session.query(EngagementProposalModel).one()
    assert proposal.status == "proposed"
    assert proposal.source_url == "https://www.moltbook.com/posts/post-123"
    assert proposal.submolt == "aifintech"
    assert "approval-gated" in proposal.proposed_reply
    assert mock_complete_json.await_count == 1
