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
from apps.core.policy.engine import PolicyEngine
from apps.api.config import settings
from apps.workers.tasks import _perform_publish_logic

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
        
        # Define the campaign plan (Day 8: News-to-Content Flow)
        # Content Strategy -> Technical/Founder Content -> Compliance review -> Content Queue
        # Note: Since the orchestrator is simple, we chain these via sequential tasks
        # In a real system, some might be triggered by events.
        # Gap B: Add Community Engagement step to campaign flow
        # Use injected sample discussions list gated for offline consistency
        sample_discussions = [
            {
                "url": "https://www.moltbook.com/posts/aifp-aos-discussion-1",
                "submolt": "aifintech",
                "content": "Does anyone know if AiFinPay AOS supports automated SDK integration for AI agents?"
            },
            {
                "url": "https://www.moltbook.com/posts/aifp-aos-discussion-2",
                "submolt": "aiagents",
                "content": "Looking for a secure way to handle agent-to-agent payments. Any recommendations?"
            }
        ]

        steps = [
            {"agent": "Market Intelligence", "input": {"topic": objective}},
            {"agent": "Content Strategy", "input": {"objective": objective}},
            {"agent": "Community Engagement", "input": {"discussions": sample_discussions}}
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
        content_item_id = input_data.get('content_item_id')
        
        def _get_context():
            with get_sync_session() as session:
                item = session.query(ContentItemModel).filter(ContentItemModel.id == content_item_id).first()
                source = None
                if item and item.source_id:
                    source = session.query(SourceModel).filter(SourceModel.id == item.source_id).first()
                return item, source

        item, source = await asyncio.to_thread(_get_context)
        if not item:
            return {"error": "Content item not found"}

        source_text = source.raw_content if source else "No source provided."
        system_prompt = (
            "You are the Technical Content Agent for AiFinPay. "
            "Generate a technical tutorial or SDK documentation based on the provided context. "
            "RULE: Must not invent endpoints, functions, supported networks, transactions, or integrations. "
            "Stick strictly to verifiable technical facts about AiFinPay and its ecosystem."
        )
        schema_hint = "{body: string}"
        
        generation = await complete_json(
            model=self.model,
            system_prompt=system_prompt,
            user_content=f"Title: {item.title}\nObjective: {item.objective}\nSource: {source_text}",
            schema_hint=schema_hint
        )

        def _update_item():
            with get_sync_session() as session:
                db_item = session.query(ContentItemModel).filter(ContentItemModel.id == content_item_id).first()
                db_item.body = generation.get("body")
                db_item.author_agent = self.name
                db_item.status = "draft"
                record_event(session, self.name, "content_generated", f"Generated technical content for {content_item_id}", {"item_id": content_item_id})
                session.commit()

        await asyncio.to_thread(_update_item)
        return {"agent": self.name, "outcome": "tutorial_generated", "item_id": content_item_id}

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
        content_item_id = input_data.get('content_item_id')
        
        def _get_context():
            with get_sync_session() as session:
                item = session.query(ContentItemModel).filter(ContentItemModel.id == content_item_id).first()
                source = None
                if item and item.source_id:
                    source = session.query(SourceModel).filter(SourceModel.id == item.source_id).first()
                return item, source

        item, source = await asyncio.to_thread(_get_context)
        if not item:
            return {"error": "Content item not found"}

        source_text = source.raw_content if source else "No source provided."
        system_prompt = (
            "You are the Founder Content Agent for AiFinPay. "
            "Generate several text variants of a high-impact leadership post. "
            "Each variant must explain its target audience (e.g., Investors, Developers, Enterprise Partners)."
        )
        schema_hint = "{variants: [{audience: string, text: string}]}"
        
        generation = await complete_json(
            model=self.model,
            system_prompt=system_prompt,
            user_content=f"Topic: {item.title}\nObjective: {item.objective}\nSource: {source_text}",
            schema_hint=schema_hint
        )

        def _update_item():
            with get_sync_session() as session:
                db_item = session.query(ContentItemModel).filter(ContentItemModel.id == content_item_id).first()
                db_item.variants = generation.get("variants")
                db_item.author_agent = self.name
                db_item.status = "draft"
                record_event(session, self.name, "content_generated", f"Generated founder variants for {content_item_id}", {"item_id": content_item_id})
                session.commit()

        await asyncio.to_thread(_update_item)
        return {"agent": self.name, "outcome": "founder_draft_ready", "item_id": content_item_id}

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
        content_item_id = input_data.get("content_item_id")
        approval_id = input_data.get("approval_id")
        draft_hash = input_data.get("draft_hash")

        if not all([content_item_id, approval_id, draft_hash]):
            with get_sync_session() as session:
                record_event(session, self.name, "publish_denied", "Missing required input for publishing", {"input_data": input_data})
                session.commit()
            return {"agent": self.name, "outcome": "publish_denied", "reason": "Missing content_item_id, approval_id, or draft_hash"}

        def _sync_wrapper():
            with get_sync_session() as session:
                try:
                    return asyncio.run(_perform_publish_logic(session, content_item_id, approval_id, draft_hash))
                except ValueError as e:
                    session.rollback()
                    # _perform_publish_logic already records audit events for denials/failures
                    return {"agent": self.name, "outcome": "publish_denied", "reason": str(e)}
                except Exception as e:
                    session.rollback()
                    # _perform_publish_logic already records audit events for denials/failures
                    raise # Re-raise for outer exception handling

        try:
            result = await asyncio.to_thread(_sync_wrapper)
            return result
        except Exception as e:
            return {"agent": self.name, "outcome": "publish_failed", "reason": str(e)}
    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Publishes only approved materials...", "tools": ["publish"], "inputs": ["approved_draft"], "outputs": ["post_url"], "policies": ["approval_only"], "kpis": ["publish_success"]}

class AnalyticsAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Analytics Agent",
            role="Analyst",
            description="Collects and reports real metrics, providing recommendations.",
            model=deepseek_fast()
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # For now, simulate metric collection and reporting
        # In a real scenario, this would query various data sources (DB, external APIs)
        
        # Example: Count published content items
        def _get_published_count():
            with get_sync_session() as session:
                published_count = session.query(ContentItemModel).filter(ContentItemModel.status == "published").count()
                return published_count
        
        published_count = await asyncio.to_thread(_get_published_count)

        # Example: Count successful MCP calls (from audit events)
        def _get_mcp_calls_count():
            with get_sync_session() as session:
                mcp_calls_count = session.query(AuditEventModel).filter(AuditEventModel.event_type == "mcp_call_succeeded").count()
                return mcp_calls_count
        
        mcp_calls_count = await asyncio.to_thread(_get_mcp_calls_count)

        report = {
            "publications": published_count,
            "mcp_calls": mcp_calls_count,
            "recommendations": "Based on current data, focus on increasing content publication frequency and diversifying channels."
        }

        with get_sync_session() as session:
            record_event(session, self.name, "metrics_reported", "Generated daily metrics report", report)
            session.commit()

        return {"agent": self.name, "outcome": "metrics_generated", "report": report}

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "purpose": "Collects real metrics: publications, impressions, clicks, engagement rate, website visits, registrations, SDK installs, MCP activations, GitHub stars, and conversions. Links every metric to its actual data source. Produces daily and weekly reports with concrete recommendations for the next cycle.",
            "tools": ["data_collection", "report_generation", "recommendation_engine"],
            "inputs": ["timeframe", "metrics_to_track"],
            "outputs": ["daily_report", "weekly_report", "recommendations"],
            "policies": ["real_metrics_only", "data_source_linking"],
            "kpis": ["report_accuracy", "recommendation_effectiveness"]
        }

class CommunityEngagementAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Community Engagement", 
            role="Community Manager",
            description="Monitors and responds to relevant community discussions.",
            model=deepseek_fast()
        )
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        discussions = input_data.get('discussions', [])
        from apps.models.engagement_proposal import EngagementProposalModel
        
        proposal_ids = []
        for disc in discussions:
            source_url = disc.get("url")
            submolt = disc.get("submolt", "general")
            content = sanitize_external(disc.get("content", ""))
            
            system_prompt = (
                "You are the Community Engagement Agent for AiFinPay. "
                "Analyze the discussion and draft a meaningful, helpful reply. "
                "RULE: No repetitive comments, mass engagement, or impersonating a human."
            )
            schema_hint = "{discussion_summary: string, proposed_reply: string}"
            
            draft = await complete_json(
                model=self.model,
                system_prompt=system_prompt,
                user_content=content,
                schema_hint=schema_hint
            )
            
            def _persist_proposal():
                with get_sync_session() as session:
                    proposal = EngagementProposalModel(
                        source_url=source_url,
                        submolt=submolt,
                        discussion_summary=draft.get("discussion_summary"),
                        proposed_reply=draft.get("proposed_reply"),
                        status="proposed"
                    )
                    session.add(proposal)
                    session.flush()
                    proposal_ids.append(proposal.id)
                    record_event(session, self.name, "engagement_proposed", f"Proposed reply for {submolt}", {"proposal_id": proposal.id})
                    session.commit()
            
            await asyncio.to_thread(_persist_proposal)
            
        return {"agent": self.name, "outcome": "proposals_created", "proposal_ids": proposal_ids}

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
        content_item_id = input_data.get('content_item_id')
        
        def _get_item():
            with get_sync_session() as session:
                return session.query(ContentItemModel).filter(ContentItemModel.id == content_item_id).first()

        item = await asyncio.to_thread(_get_item)
        if not item:
            return {"error": "Content item not found"}

        content_to_review = item.body or str(item.variants)
        system_prompt = (
            "You are the Compliance & Brand Agent for AiFinPay. "
            "Review the provided content for compliance and brand violations. "
            "BLOCK: False claims, invented partnerships, promises of returns, spam, secret exposure, and brand-tone violations. "
            "Return one of: approved, rejected, needs_revision with a specific reason."
        )
        schema_hint = "{status: string, reason: string}"
        
        review = await complete_json(
            model=self.model,
            system_prompt=system_prompt,
            user_content=content_to_review,
            schema_hint=schema_hint
        )

        status = review.get("status", "needs_revision")
        reason = review.get("reason", "Incomplete review")

        def _update_compliance():
            with get_sync_session() as session:
                db_item = session.query(ContentItemModel).filter(ContentItemModel.id == content_item_id).first()
                db_item.compliance_status = status
                db_item.compliance_reason = reason
                # Map compliance status to content status if rejected
                if status == "rejected":
                    db_item.status = "rejected"
                elif status == "approved":
                    db_item.status = "pending_review" # Ready for human queue
                
                record_event(session, self.name, "compliance_reviewed", f"Compliance result: {status}", {"item_id": content_item_id, "reason": reason})
                session.commit()

        await asyncio.to_thread(_update_compliance)
        return {"agent": self.name, "outcome": "reviewed", "status": status, "reason": reason}

    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Reviews every piece of content before publication.", "tools": ["review"], "inputs": ["draft"], "outputs": ["status"], "policies": ["brand_tone"], "kpis": ["compliance_rate"]}
