from __future__ import annotations
import logging
import asyncio
import hashlib
from typing import Any, Dict, List
from sqlalchemy import select, desc
from .base import BaseAgent
from apps.core.models.factory import deepseek_fast, deepseek_reasoning
from apps.models.base import get_sync_session
from apps.models.source import SourceModel
from apps.models.content_item import ContentItemModel
from apps.core.orchestrator.engine import Orchestrator
from apps.core.models.llm import complete_json
from apps.core.sanitizer import sanitize_external
from apps.core.audit.service import record_event

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
        
        # Offload synchronous DB work to a thread to avoid blocking the event loop
        result = await asyncio.to_thread(self._dispatch_campaign, objective, steps)
        
        return {
            "agent": self.name,
            "outcome": "campaign_dispatched",
            "campaign_id": result["campaign_id"],
            "tasks": result["tasks"],
            "status": "executing"
        }

    def _dispatch_campaign(self, objective: str, steps: list) -> Dict[str, Any]:
        """Synchronous helper for campaign dispatch."""
        with get_sync_session() as session:
            orch = Orchestrator(session)
            return orch.create_campaign(objective, steps)

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
        topic = input_data.get('topic', 'AI agents, agentic commerce, MCP, stablecoin payments')
        raw_sources = input_data.get('sources', [
            {"url": "https://aifinpay.com/blog/agentic-commerce", "title": "The Future of Agentic Commerce", "content": "AiFinPay is leading the way in AI-driven payments..."},
            {"url": "https://techcrunch.com/2026/ai-fintech", "title": "AI Infrastructure in Fintech", "content": "New trends in AI infrastructure are shaping the fintech landscape..."}
        ])
        
        stored_count = 0
        skipped_count = 0
        top_sources = []

        for item in raw_sources:
            url = item.get("url")
            if not url: continue
            
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            
            # Sanitization
            clean_content = sanitize_external(item.get("content", ""))
            
            # Sync DB check and storage
            def _check_and_store():
                with get_sync_session() as session:
                    existing = session.query(SourceModel).filter(SourceModel.url_hash == url_hash).first()
                    if existing:
                        return False, existing.id
                    
                    return True, None
            
            is_new, existing_id = await asyncio.to_thread(_check_and_store)
            
            if not is_new:
                skipped_count += 1
                continue

            # LLM Scoring
            scoring_prompt = "Analyze this source for market intelligence relevance to AiFinPay's growth."
            schema_hint = "{summary: string, relevance_score: float, content_angle: string}"
            
            analysis = await complete_json(
                model=self.model,
                system_prompt=scoring_prompt,
                user_content=clean_content,
                schema_hint=schema_hint
            )
            
            def _persist_source():
                with get_sync_session() as session:
                    new_source = SourceModel(
                        url=url,
                        url_hash=url_hash,
                        title=item.get("title"),
                        summary=analysis.get("summary"),
                        relevance_score=analysis.get("relevance_score", 0.0),
                        content_angle=analysis.get("content_angle"),
                        topic=topic,
                        raw_content=item.get("content")
                    )
                    session.add(new_source)
                    session.flush()
                    record_event(session, self.name, "source_stored", f"Stored source: {url}", {"source_id": new_source.id})
                    session.commit()
                    return new_source.id

            source_id = await asyncio.to_thread(_persist_source)
            stored_count += 1
            top_sources.append({"id": source_id, "url": url, "score": analysis.get("relevance_score")})

        return {
            "agent": self.name,
            "outcome": "intelligence_gathered",
            "sources_stored": stored_count,
            "duplicates_skipped": skipped_count,
            "top_sources": top_sources
        }

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "purpose": "Tracks AI agents, MCP, x402, and fintech trends.",
            "tools": ["web_search", "deduplication", "llm_scoring"],
            "inputs": ["topic", "sources"],
            "outputs": ["intelligence_gathered", "sources_stored", "relevance_score"],
            "policies": ["primary_sources_only", "sanitize_untrusted"],
            "kpis": ["sources_tracked", "unique_source_rate"]
        }

class ContentStrategyAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Content Strategy", 
            role="Strategist",
            description="Creates weekly content plans across multiple channels.",
            model=deepseek_fast()
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        objective = input_data.get('objective', 'AiFinPay brand awareness')
        
        def _get_top_sources():
            with get_sync_session() as session:
                return session.query(SourceModel).order_by(desc(SourceModel.relevance_score)).limit(5).all()
        
        sources = await asyncio.to_thread(_get_top_sources)
        source_context = "\n".join([f"- {s.title}: {s.summary} (ID: {s.id})" for s in sources])
        
        planning_prompt = f"Create a weekly content plan for objective: {objective}. Rule: Every item must link to an AiFinPay connection and a provided source ID."
        schema_hint = "{items: [{channel: string, target_audience: string, objective: string, format: string, cta: string, kpi: string, source_id: string, title: string}]}"
        
        plan = await complete_json(
            model=self.model,
            system_prompt=planning_prompt,
            user_content=f"Available Sources:\n{source_context}",
            schema_hint=schema_hint
        )
        
        item_ids = []
        def _persist_plan():
            with get_sync_session() as session:
                for item in plan.get("items", []):
                    new_item = ContentItemModel(
                        title=item.get("title", "Planned Content"),
                        channel=item.get("channel", "X"),
                        status="draft",
                        objective=item.get("objective"),
                        target_audience=item.get("target_audience"),
                        format=item.get("format"),
                        cta=item.get("cta"),
                        kpi=item.get("kpi"),
                        source_id=item.get("source_id"),
                        author_agent=self.name
                    )
                    session.add(new_item)
                    session.flush()
                    item_ids.append(new_item.id)
                    record_event(session, self.name, "content_planned", f"Planned item for {item.get('channel')}", {"item_id": new_item.id})
                session.commit()
        
        await asyncio.to_thread(_persist_plan)
        
        return {
            "agent": self.name,
            "outcome": "weekly_plan_created",
            "items": item_ids
        }

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "purpose": "Creates weekly content plan by channel based on intelligence.",
            "tools": ["planning", "source_mapping"],
            "inputs": ["objective", "intelligence"],
            "outputs": ["content_calendar", "source_id_links"],
            "policies": ["no_generic_ai_content", "must_link_aifinpay"],
            "kpis": ["plan_coverage", "source_utilization"]
        }

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
