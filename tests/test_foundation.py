from apps.agents.registry import AgentRegistry
from apps.models.agent import AgentModel
from apps.models.campaign import CampaignModel
from apps.models.content_item import ContentItemModel
from apps.models.audit_event import AuditEventModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.models.base import Base
import uuid


def test_agent_registry_registers_specialized_agents():
    registry = AgentRegistry()
    registry.register_default_agents()

    agents = registry.list_agents()
    names = [agent.name for agent in agents]

    assert "Growth Orchestrator" in names
    assert "Market Intelligence" in names
    assert "Content Strategy" in names


def test_models_have_expected_columns():
    agent = AgentModel(name="Growth Orchestrator",
                       role="orchestrator", status="active")
    campaign = CampaignModel(name="Weekly Launch", objective="Launch content")
    content_item = ContentItemModel(
        title="Launch post", channel="x", status="draft")
    audit_event = AuditEventModel(
        agent_name="Growth Orchestrator", event_type="created")

    assert agent.name == "Growth Orchestrator"
    assert campaign.objective == "Launch content"
    assert content_item.channel == "x"
    assert audit_event.event_type == "created"


def test_sqlite_models_and_uuid_uniqueness():
    # In-memory SQLite
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Insert two agents with JSON
    agent1 = AgentModel(
        name="Test1", role="test", tools=[{"tool": "read"}], inputs={}, outputs={}, policies={}, kpis={}, execution_history=[]
    )
    agent2 = AgentModel(
        name="Test2", role="test", tools=[{"tool": "write"}], inputs={}, outputs={}, policies={}, kpis={}, execution_history=[]
    )
    session.add(agent1)
    session.add(agent2)
    session.commit()

    # Re-query and assert distinct IDs
    agents = session.query(AgentModel).all()
    assert len(agents) == 2
    assert agents[0].id != agents[1].id
    assert "agent-" in agents[0].id
    session.close()