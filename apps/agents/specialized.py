from __future__ import annotations
import logging
import asyncio
from typing import Any, Dict
from .base import BaseAgent
from apps.core.models.factory import deepseek_fast, deepseek_reasoning
from apps.models.base import get_sync_session
from apps.core.orchestrator.engine import Orchestrator

logger = logging.getLogger(__name__)

class GrowthOrchestratorAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Growth Orchestrator", 
            role="Orchestrator",
            description="Receives marketing objectives and dispatches specialized tasks.",
            model=deepseek_reasoning()
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        objective = input_data.get('objective', 'default_campaign')
        
        # Define the campaign plan
        steps = [
            {"agent": "Market Intelligence", "input": {"topic": objective}},
            {"agent": "Content Strategy", "input": {"objective": objective}},
            {"agent": "Social Publishing", "input": {"action": "distribute"}}
        ]
        
        with get_sync_session() as session:
            orch = Orchestrator(session)
            result = await orch.create_campaign(objective, steps)
            return {
                "agent": self.name,
                "outcome": "campaign_dispatched",
                "campaign_id": result["campaign_id"],
                "tasks": result["tasks"],
                "status": "executing"
            }

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "purpose": "Receives marketing objective, creates execution plan, distributes tasks, handles retries, daily reports",
            "tools": ["task_distribution", "retry_handler"],
            "inputs": ["objective", "constraints"],
            "outputs": ["execution_plan", "daily_report"],
            "policies": ["approval_required_for_publish"],
            "kpis": ["tasks_completed", "success_rate"]
        }

class MarketIntelligenceAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Market Intelligence", 
            role="Researcher",
            description="Tracks AI agents, MCP, and market trends.",
            model=deepseek_fast()
        )
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        topic = input_data.get('topic', 'ai_agents')
        return {"agent": self.name, "outcome": "intelligence_gathered", "topic": topic}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Tracks AI agents, MCP, x402...", "tools": ["web_search"], "inputs": ["topics"], "outputs": ["structured_intel"], "policies": ["primary_sources_only"], "kpis": ["sources_tracked"]}

class ContentStrategyAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Content Strategy", 
            role="Strategist",
            description="Creates weekly content plans across multiple channels.",
            model=deepseek_fast()
        )
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "weekly_plan_created"}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Creates weekly content plan by channel.", "tools": ["planning"], "inputs": ["audience"], "outputs": ["content_calendar"], "policies": [], "kpis": ["plan_coverage"]}

class TechnicalContentAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Technical Content", 
            role="Technical Writer",
            description="Generates technical tutorials and SDK documentation.",
            model=deepseek_fast()
        )
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "tutorial_generated"}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Creates technical posts, tutorials, SDK examples...", "tools": ["code_verification"], "inputs": ["topic"], "outputs": ["draft"], "policies": ["no_invented_endpoints"], "kpis": ["technical_accuracy"]}

class FounderContentAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Founder Content", 
            role="Ghostwriter",
            description="Crafts high-impact content for leadership accounts.",
            model=deepseek_fast()
        )
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "founder_draft_ready"}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Creates materials for founder's account...", "tools": ["drafting"], "inputs": ["update"], "outputs": ["variants"], "policies": ["manual_approval"], "kpis": ["approval_rate"]}

class SocialPublishingAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Social Publishing", 
            role="Publisher",
            description="Handles distribution of approved content to social channels.",
            model=deepseek_fast()
        )
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "publish_queued"}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Publishes only approved materials...", "tools": ["publish"], "inputs": ["approved_draft"], "outputs": ["post_url"], "policies": ["approval_only"], "kpis": ["publish_success"]}

class CommunityEngagementAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Community Engagement", 
            role="Community Manager",
            description="Monitors and responds to relevant community discussions.",
            model=deepseek_fast()
        )
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "reply_prepared"}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Finds relevant discussions and prepares meaningful replies...", "tools": ["engagement_scan"], "inputs": ["discussion"], "outputs": ["proposed_reply"], "policies": ["no_mass_comments"], "kpis": ["engagement_quality"]}

class AnalyticsAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Analytics", 
            role="Data Analyst",
            description="Measures and reports on campaign performance metrics.",
            model=deepseek_fast()
        )
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "report_generated"}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Collects only real metrics...", "tools": ["metric_collection"], "inputs": ["publication_url"], "outputs": ["report"], "policies": ["verifiable_sources"], "kpis": ["conversion_rate"]}

class ComplianceBrandAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Compliance & Brand", 
            role="Brand Guardian",
            description="Ensures all content adheres to brand and regulatory standards.",
            model=deepseek_fast()
        )
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "reviewed", "status": "approved"}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Reviews every piece of content before publication.", "tools": ["review"], "inputs": ["draft"], "outputs": ["status"], "policies": ["brand_tone"], "kpis": ["compliance_rate"]}
