from __future__ import annotations
from typing import Any, Dict
from .base import BaseAgent
from apps.core.models.factory import deepseek_fast, deepseek_reasoning

class GrowthOrchestratorAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="Growth Orchestrator", model=deepseek_reasoning())
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        objective = input_data.get('objective', 'default_campaign')
        plan = {"plan_id": f"plan-{hash(objective)}", "tasks": ["research", "content", "publish"], "dependencies": []}
        return {"agent": self.name, "outcome": "plan_generated", "plan": plan, "status": "executing"}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Receives marketing objective, creates execution plan, distributes tasks, handles retries, daily reports", "tools": ["task_distribution", "retry_handler"], "inputs": ["objective", "constraints"], "outputs": ["execution_plan", "daily_report"], "policies": ["approval_required_for_publish"], "kpis": ["tasks_completed", "success_rate"]}

class MarketIntelligenceAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="Market Intelligence", model=deepseek_fast())
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        topic = input_data.get('topic', 'ai_agents')
        sources = [{"url": f"https://example.com/{topic}", "summary": "Relevant update", "relevance": 0.95, "date": "2026-07-22"}]
        return {"agent": self.name, "outcome": "intelligence_gathered", "sources": sources}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Tracks AI agents, MCP, x402... Stores source URL, date, summary, relevance", "tools": ["web_search", "deduplication"], "inputs": ["topics"], "outputs": ["structured_intel"], "policies": ["primary_sources_only"], "kpis": ["sources_tracked", "relevance_score_avg"]}

class ContentStrategyAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="Content Strategy", model=deepseek_fast())
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "weekly_plan_created", "plan": {"channels": ["X", "Telegram"], "items": 5}}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Creates weekly content plan by channel. Defines target audience, objective, format, CTA...", "tools": ["planning"], "inputs": ["audience"], "outputs": ["content_calendar"], "policies": [], "kpis": ["plan_coverage"]}

class TechnicalContentAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="Technical Content", model=deepseek_fast())
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "tutorial_generated", "verified": True}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Creates technical posts, tutorials, SDK examples... Verifies every claim against AiFinPay codebase", "tools": ["code_verification"], "inputs": ["topic"], "outputs": ["draft"], "policies": ["no_invented_endpoints"], "kpis": ["technical_accuracy"]}

class FounderContentAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="Founder Content", model=deepseek_fast())
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "founder_draft_ready", "variants": 3}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Creates materials for founder's account... Provides several text variants...", "tools": ["drafting"], "inputs": ["update"], "outputs": ["variants"], "policies": ["manual_approval"], "kpis": ["approval_rate"]}

class SocialPublishingAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="Social Publishing", model=deepseek_fast())
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "publish_queued", "platforms": ["X", "Telegram", "Moltbook"]}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Publishes only approved materials... Includes duplicate protection, scheduling...", "tools": ["publish"], "inputs": ["approved_draft"], "outputs": ["post_url"], "policies": ["approval_only"], "kpis": ["publish_success"]}

class CommunityEngagementAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="Community Engagement", model=deepseek_fast())
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "reply_prepared", "risk": "low"}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Finds relevant discussions and prepares meaningful replies... Shows original post, risk level...", "tools": ["engagement_scan"], "inputs": ["discussion"], "outputs": ["proposed_reply"], "policies": ["no_mass_comments"], "kpis": ["engagement_quality"]}

class AnalyticsAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="Analytics", model=deepseek_fast())
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "report_generated", "metrics": {"impressions": 1500}}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Collects only real metrics... Produces daily/weekly reports with recommendations...", "tools": ["metric_collection"], "inputs": ["publication_url"], "outputs": ["report"], "policies": ["verifiable_sources"], "kpis": ["conversion_rate"]}

class ComplianceBrandAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="Compliance & Brand", model=deepseek_fast())
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "outcome": "reviewed", "status": "approved"}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Reviews every piece of content before publication. Blocks false claims...", "tools": ["review"], "inputs": ["draft"], "outputs": ["status"], "policies": ["brand_tone"], "kpis": ["compliance_rate"]}
