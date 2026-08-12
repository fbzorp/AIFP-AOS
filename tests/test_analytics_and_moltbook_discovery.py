import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock, call, patch

from apps.agents.registry import get_agent, list_agents
from apps.agents.specialized import (
    AnalyticsAgent,
    CommunityEngagementAgent,
    GrowthOrchestratorAgent,
)
from apps.api.config import settings
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
async def test_list_discussions_uses_read_only_posts_feed_and_normalizes_posts():
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
                "posts": [
                    {
                        "id": "post-123",
                        "submolt": {"name": "aifintech"},
                        "content": "How can an AI agent safely use x402 payments?",
                    },
                    {
                        "id": "post-456",
                        "submolt_name": "aifintech",
                        "content": "",
                    },
                    {
                        "id": "post-789",
                        "submolt_name": "aifintech",
                        "content": "This post includes a supplied canonical URL.",
                        "url": "https://www.moltbook.com/posts/post-789",
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
        discussions = await client.list_discussions(submolt="aifintech", limit=10)
    finally:
        await client.close()

    assert observed_request == {
        "method": "GET",
        "path": "/api/v1/posts",
        "authorization": "Bearer unit-test-agent-key",
        "params": {
            "submolt": "aifintech",
            "sort": "new",
            "limit": "10",
        },
    }
    assert discussions == [
        {
            "url": "https://www.moltbook.com/posts/post-123",
            "submolt": "aifintech",
            "content": "How can an AI agent safely use x402 payments?",
        },
        {
            "url": "https://www.moltbook.com/posts/post-789",
            "submolt": "aifintech",
            "content": "This post includes a supplied canonical URL.",
        },
    ]


@pytest.mark.asyncio
async def test_list_discussions_rejects_invalid_parameters_without_network_calls():
    client = MoltbookClient(
        base_url="https://www.moltbook.com",
        agent_key="unit-test-agent-key",
        app_key="unit-test-app-key",
    )
    try:
        with pytest.raises(ValueError, match="non-empty string"):
            await client.list_discussions(submolt="")
    finally:
        await client.close()


def test_registry_has_one_real_analytics_agent_and_get_agent_resolves_it():
    analytics_agents = [agent for agent in list_agents() if agent.name == "Analytics Agent"]

    assert len(analytics_agents) == 1
    assert type(analytics_agents[0]) is AnalyticsAgent

    resolved_agent = get_agent("Analytics Agent")
    assert type(resolved_agent) is AnalyticsAgent


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
                post_id="real-post-123",  # Add real post_id to count as real publication
                post_url="https://moltbook.com/posts/real-post-123"
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
                metadata_json={"function": "agent_quote"}
            ),
            AuditEventModel(
                id="mcp-failed",
                agent_name="Payments",
                event_type="mcp_call_failed",
                message="MCP call failed",
                metadata_json={"function": "agent_quote"}
            ),
        ]
    )
    session.flush()  # Flush to ensure hash computation
    session.commit()

    # Patch mcp_client to disable it
    with patch("apps.agents.specialized.mcp_client") as mock_mcp:
        mock_mcp.enabled = False
        mock_mcp.get_successful_calls.return_value = []
        
        result = await AnalyticsAgent().execute({})

    assert result["agent"] == "Analytics Agent"
    assert result["outcome"] == "metrics_generated"
    assert result["report"]["metrics"]["publications"] == 1
    assert result["report"]["metrics"]["mcp_calls"] == 1
    assert session.query(AuditEventModel).filter(
        AuditEventModel.event_type == "metrics_reported"
    ).count() == 1


@patch("apps.agents.specialized.get_sync_session")
@pytest.mark.asyncio
async def test_growth_orchestrator_uses_list_discussions_and_filters_allowed_submolts(
    mock_get_session,
):
    session = TestingSessionLocal()
    mock_get_session.return_value.__enter__.return_value = session
    mock_client = MagicMock()
    mock_client.list_discussions = AsyncMock(
        side_effect=[
            [
                {
                    "url": "https://www.moltbook.com/posts/allowed-1",
                    "submolt": "aifintech",
                    "content": "Relevant x402 discussion",
                },
                {
                    "url": "https://www.moltbook.com/posts/blocked-1",
                    "submolt": "blocked-community",
                    "content": "This must not enter the task payload",
                },
            ],
            [
                {
                    "url": "https://www.moltbook.com/posts/allowed-2",
                    "submolt": "aiagents",
                    "content": "Relevant agentic-commerce discussion",
                }
            ],
        ]
    )
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_client)
    mock_context.__aexit__ = AsyncMock(return_value=None)

    agent = GrowthOrchestratorAgent()
    with (
        patch("apps.agents.specialized.MoltbookClient", return_value=mock_context),
        patch.object(
            settings,
            "MOLTBOOK_ALLOWED_SUBMOLTS",
            "aifintech, aiagents",
        ),
        patch.object(
            agent,
            "_dispatch_campaign",
            return_value={"campaign_id": "campaign-1", "tasks": []},
        ) as mock_dispatch_campaign,
    ):
        result = await agent.execute({"objective": "Grow verified x402 adoption"})

    assert mock_client.list_discussions.await_args_list == [
        call(submolt="aifintech", limit=10),
        call(submolt="aiagents", limit=10),
    ]
    dispatched_steps = mock_dispatch_campaign.call_args.args[1]
    engagement_step = next(
        step for step in dispatched_steps if step["agent"] == "Community Engagement"
    )
    assert engagement_step["input"] == {
        "discussions": [
            {
                "url": "https://www.moltbook.com/posts/allowed-1",
                "submolt": "aifintech",
                "content": "Relevant x402 discussion",
            },
            {
                "url": "https://www.moltbook.com/posts/allowed-2",
                "submolt": "aiagents",
                "content": "Relevant agentic-commerce discussion",
            },
        ]
    }
    assert result["discussions_discovered"] == 2

    discovery_audit = session.query(AuditEventModel).filter(
        AuditEventModel.event_type == "discussion_discovery_attempted"
    ).one()
    assert discovery_audit.metadata_json == {
        "allowed_submolts": ["aifintech", "aiagents"],
        "attempted_submolts": ["aifintech", "aiagents"],
        "failed_submolts": [],
        "discovered_count": 2,
        "limit_per_submolt": 10,
    }


@patch("apps.agents.specialized.get_sync_session")
@pytest.mark.asyncio
async def test_growth_orchestrator_handles_discovery_failure_without_fake_discussions(
    mock_get_session,
):
    session = TestingSessionLocal()
    mock_get_session.return_value.__enter__.return_value = session
    mock_client = MagicMock()
    mock_client.list_discussions = AsyncMock(
        side_effect=httpx.ConnectError("Moltbook is unavailable")
    )
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_client)
    mock_context.__aexit__ = AsyncMock(return_value=None)

    agent = GrowthOrchestratorAgent()
    with (
        patch("apps.agents.specialized.MoltbookClient", return_value=mock_context),
        patch.object(settings, "MOLTBOOK_ALLOWED_SUBMOLTS", "aifintech"),
        patch.object(
            agent,
            "_dispatch_campaign",
            return_value={"campaign_id": "campaign-2", "tasks": []},
        ) as mock_dispatch_campaign,
    ):
        result = await agent.execute({"objective": "Remain resilient offline"})

    engagement_step = next(
        step
        for step in mock_dispatch_campaign.call_args.args[1]
        if step["agent"] == "Community Engagement"
    )
    assert engagement_step["input"] == {"discussions": []}
    assert result["discussions_discovered"] == 0

    discovery_audit = session.query(AuditEventModel).filter(
        AuditEventModel.event_type == "discussion_discovery_attempted"
    ).one()
    assert discovery_audit.metadata_json["failed_submolts"] == ["aifintech"]
    assert discovery_audit.metadata_json["discovered_count"] == 0


@patch("apps.agents.specialized.get_sync_session")
@patch("apps.agents.specialized.complete_json")
@pytest.mark.asyncio
async def test_community_engagement_persists_approval_gated_proposals(
    mock_complete_json,
    mock_get_session,
):
    session = TestingSessionLocal()
    mock_get_session.return_value.__enter__.return_value = session
    mock_complete_json.return_value = {
        "discussion_summary": "An agent needs guidance on x402 payments.",
        "proposed_reply": "AiFinPay can help with an approval-gated x402 payment flow.",
    }

    result = await CommunityEngagementAgent().execute(
        {
            "discussions": [
                {
                    "url": "https://www.moltbook.com/posts/post-123",
                    "submolt": "aifintech",
                    "content": "How can an AI agent safely use x402 payments?",
                }
            ]
        }
    )

    assert result["outcome"] == "proposals_created"
    assert len(result["proposal_ids"]) == 1

    proposal = session.query(EngagementProposalModel).one()
    assert proposal.status == "proposed"
    assert proposal.source_url == "https://www.moltbook.com/posts/post-123"
    assert proposal.submolt == "aifintech"
    assert "approval-gated" in proposal.proposed_reply
