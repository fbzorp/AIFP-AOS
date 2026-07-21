from apps.agents.registry import AgentRegistry
from apps.models.agent import AgentModel
from apps.models.campaign import CampaignModel
from apps.models.content_item import ContentItemModel
from apps.models.audit_event import AuditEventModel


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
