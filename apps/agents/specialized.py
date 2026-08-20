# Force Docker cache invalidate - v2
from __future__ import annotations
import logging
import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy import select, desc
from .base import BaseAgent
from apps.core.models.factory import deepseek_fast, deepseek_reasoning
from apps.models.base import get_sync_session
from apps.models.source import SourceModel
from apps.models.content_item import ContentItemModel
from apps.models.audit_event import AuditEventModel
from apps.core.orchestrator.engine import Orchestrator
from apps.core.models.llm import complete_json
from apps.core.sanitizer import sanitize_external
from apps.core.audit.service import record_event
from apps.core.policy.engine import PolicyEngine
from apps.api.config import settings
from apps.workers.tasks import _perform_publish_logic
from apps.integrations.moltbook.client import MoltbookClient
from apps.integrations.x.client import XClient
from apps.core.embeddings import embed_text
from .adk_orchestrator import get_adk_orchestrator
from apps.integrations.analytics.gsc_client import GoogleSearchConsoleClient

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
        discussions = await self._discover_allowed_discussions(limit=10)

        # Try to use ADK Marketing Manager for intelligent routing
        adk_orchestrator = get_adk_orchestrator()
        orchestration_result = await adk_orchestrator.orchestrate_campaign(objective)
        
        # Use ADK-routed steps if available, otherwise use static fallback
        if orchestration_result["routing_method"] == "adk_routed":
            steps = orchestration_result["steps"]
            # Add discussions to the Community Engagement step if available
            for step in steps:
                if step.get("agent") == "Community Engagement" and discussions:
                    step["input"]["discussions"] = discussions
        else:
            # Static fallback (original behavior)
            steps = [
                {"agent": "Market Intelligence", "input": {"topic": objective}},
                {"agent": "Content Strategy", "input": {"objective": objective}},
                {
                    "agent": "Community Engagement",
                    "input": {"discussions": discussions},
                },
            ]

        # Offload synchronous DB work to a thread to avoid blocking the event loop
        result = await asyncio.to_thread(self._dispatch_campaign, objective, steps)

        return {
            "agent": self.name,
            "outcome": "campaign_dispatched",
            "campaign_id": result["campaign_id"],
            "tasks": result["tasks"],
            "status": "executing",
            "discussions_discovered": len(discussions),
            "routing_method": orchestration_result["routing_method"],
        }

    async def _discover_allowed_discussions(self, limit: int = 10) -> List[Dict[str, str]]:
        """Read recent discussions from allowlisted platforms without blocking a campaign.

        Discovery is read-only and produces no synthetic fallback records. The
        Community Engagement Agent remains responsible for sanitization and
        approval-gated proposal creation.
        
        Platforms supported:
        - Moltbook: Uses allowlisted submolts
        - X/Twitter: Uses configured search queries
        """
        discussions: List[Dict[str, str]] = []
        
        # Discover from Moltbook (existing implementation)
        moltbook_discussions = await self._discover_moltbook_discussions(limit)
        discussions.extend(moltbook_discussions)
        
        # Discover from X/Twitter (new implementation)
        x_discussions = await self._discover_x_discussions(limit)
        discussions.extend(x_discussions)
        
        # Record combined discovery audit event (once)
        try:
            await asyncio.to_thread(
                self._record_discovery_audit,
                "discussion_discovery_attempted",
                f"Completed read-only discussion discovery from multiple platforms",
                {
                    "moltbook_discovered": len(moltbook_discussions),
                    "x_discovered": len(x_discussions),
                    "total_discovered": len(discussions),
                    "limit_per_platform": limit,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record combined discovery audit event: {e}", exc_info=True)

        return discussions
    
    async def _discover_moltbook_discussions(self, limit: int = 10) -> List[Dict[str, str]]:
        """Discover discussions from Moltbook allowlisted submolts."""
        allowed_submolts = [
            submolt.strip().lower()
            for submolt in settings.MOLTBOOK_ALLOWED_SUBMOLTS.split(",")
            if submolt.strip()
        ]
        allowed_submolts = list(dict.fromkeys(allowed_submolts))
        discussions: List[Dict[str, str]] = []
        failed_submolts: List[str] = []

        if not allowed_submolts:
            logger.warning("Skipping Moltbook discussion discovery: no allowed submolts configured")
        else:
            try:
                async with MoltbookClient() as client:
                    for submolt in allowed_submolts:
                        try:
                            candidates = await client.list_discussions(
                                submolt=submolt,
                                limit=limit,
                            )
                        except Exception:
                            failed_submolts.append(submolt)
                            logger.warning(
                                "Moltbook discussion discovery failed for allowlisted submolt %s",
                                submolt,
                                exc_info=True,
                            )
                            continue

                        for candidate in candidates:
                            candidate_submolt = candidate.get("submolt")
                            if (
                                isinstance(candidate_submolt, str)
                                and candidate_submolt.strip().lower() in allowed_submolts
                            ):
                                # Add platform identifier only if not already present
                                if "platform" not in candidate:
                                    candidate["platform"] = "moltbook"
                                if candidate not in discussions:  # Avoid duplicates
                                    discussions.append(candidate)
                            else:
                                logger.warning(
                                    "Ignoring Moltbook discussion outside the configured allowlist"
                                )
            except Exception:
                failed_submolts = allowed_submolts
                logger.warning(
                    "Moltbook discussion discovery is unavailable; continuing with other platforms",
                    exc_info=True,
                )

        # Record individual Moltbook discovery audit event (before returning to avoid duplicates)
        try:
            await asyncio.to_thread(
                self._record_discovery_audit,
                "moltbook_discovery_attempted",
                f"Moltbook discussion discovery completed",
                {
                    "allowed_submolts": allowed_submolts,
                    "attempted_submolts": allowed_submolts,
                    "failed_submolts": failed_submolts,
                    "discovered_count": len(discussions),
                    "limit_per_submolt": limit,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record Moltbook discovery audit event: {e}", exc_info=True)
        
        logger.info(f"Moltbook discovery: {len(discussions)} discussions, failed: {failed_submolts}")
        
        return discussions
    
    async def _discover_x_discussions(self, limit: int = 10) -> List[Dict[str, str]]:
        """Discover discussions from X/Twitter using search API."""
        discussions: List[Dict[str, str]] = []
        
        # Check if X search is enabled via env var
        x_search_enabled = getattr(settings, "X_SEARCH_ENABLED", False)
        if isinstance(x_search_enabled, str):
            x_search_enabled = x_search_enabled.lower() == "true"
        if not x_search_enabled:
            logger.info("X/Twitter search discovery disabled (X_SEARCH_ENABLED=false)")
            return discussions
        
        # Get search queries from env (comma-separated)
        search_queries = getattr(settings, "X_SEARCH_QUERIES", "")
        if not search_queries:
            logger.info("No X search queries configured (X_SEARCH_QUERIES not set)")
            return discussions
        
        queries = [q.strip() for q in search_queries.split(",") if q.strip()]
        
        try:
            async with XClient() as x_client:
                for query in queries:
                    try:
                        logger.info(f"X search discovery for query: {query}")
                        
                        # Use the new search method from XClient
                        search_result = await x_client.search(query, max_results=limit)
                        
                        if search_result.get("success") and search_result.get("data"):
                            tweets = search_result["data"]
                            for tweet in tweets:
                                discussions.append({
                                    "id": tweet.get("id"),
                                    "text": tweet.get("text"),
                                    "author_id": tweet.get("author_id"),
                                    "created_at": tweet.get("created_at"),
                                    "public_metrics": tweet.get("public_metrics", {}),
                                    "lang": tweet.get("lang"),
                                    "source": "x"
                                })
                            
                            logger.info(f"Found {len(tweets)} tweets for query: {query}")
                            
                        # Stop if we've reached the limit
                        if len(discussions) >= limit:
                            break
                        
                    except Exception as e:
                        logger.warning(f"X search failed for query '{query}': {e}", exc_info=True)
                        continue
            
        except Exception as e:
            logger.warning(f"X/Twitter search discovery unavailable: {e}", exc_info=True)
        
        # Limit results
        discussions = discussions[:limit]
        
        logger.info(f"X discovery: {len(discussions)} discussions")
        
        # Record individual X discovery audit event
        try:
            await asyncio.to_thread(
                self._record_discovery_audit,
                "x_discovery_attempted",
                f"X/Twitter search discovery completed",
                {
                    "search_queries": queries,
                    "results_per_query": len(discussions) // len(queries) if queries else 0,
                    "total_discovered": len(discussions),
                    "limit": limit,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record X discovery audit event: {e}", exc_info=True)
        
        return discussions

    def _record_discovery_audit(
        self,
        event_type: str,
        message: str,
        metadata: Dict[str, Any],
    ) -> None:
        with get_sync_session() as session:
            record_event(session, self.name, event_type, message, metadata)
            session.commit()

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
        topic = input_data.get('topic', 'AI agents, agentic commerce, MCP, fintech')
        
        # Priority: use externally-supplied sources, then fetch real sources
        raw_sources = input_data.get('sources')
        
        if not raw_sources:
            # Fetch real sources from available APIs
            from apps.core.news_fetcher import news_fetcher
            
            logger.info(f"No sources provided, fetching real sources for topic: {topic}")
            raw_sources = await news_fetcher.fetch_real_sources(topic)
            
            if not raw_sources:
                logger.warning(f"No real sources could be retrieved for topic: {topic}")
                return {
                    "agent": self.name,
                    "outcome": "no_verified_sources_available",
                    "sources_stored": 0,
                    "duplicates_skipped": 0,
                    "top_sources": [],
                    "message": "No verified sources available. Please configure NEWS_API_KEY or SERPER_API_KEY in .env, or provide sources manually."
                }
        
        stored_count = 0
        skipped_count = 0
        top_sources = []
        from datetime import datetime

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
                    # Compute embedding for semantic search
                    summary = analysis.get("summary", "")
                    raw_content = item.get("content", "")
                    combined_text = f"{summary} {raw_content}"
                    
                    try:
                        embedding = embed_text(combined_text)
                    except Exception as e:
                        logger.warning(f"Failed to compute embedding for source {url}: {e}")
                        embedding = None
                    
                    # Parse published_date if it's a string
                    published_date = item.get("published_date")
                    if isinstance(published_date, str):
                        try:
                            published_date = datetime.fromisoformat(published_date.replace('Z', '+00:00')).replace(tzinfo=None)
                        except (ValueError, AttributeError):
                            published_date = None
                    
                    new_source = SourceModel(
                        url=url,
                        url_hash=url_hash,
                        title=item.get("title"),
                        author=item.get("author"),
                        publisher=item.get("source"),  # Publisher from news API
                        published_date=published_date,
                        retrieval_date=datetime.now(timezone.utc).replace(tzinfo=None),
                        summary=analysis.get("summary"),
                        relevance_score=analysis.get("relevance_score", 0.0),
                        content_angle=analysis.get("content_angle"),
                        topic=topic,
                        raw_content=item.get("content")
                    )
                    session.add(new_source)
                    session.flush()
                    
                    # Set embedding via raw SQL since it's not in the model definition
                    # Only attempt this for Postgres (not SQLite tests)
                    if embedding is not None:
                        try:
                            from sqlalchemy import text
                            # Handle both numpy arrays and lists
                            if hasattr(embedding, 'tolist'):
                                embedding_str = str(embedding.tolist())
                            else:
                                embedding_str = str(embedding)
                            session.execute(
                                text("UPDATE sources SET embedding = :embedding WHERE id = :source_id"),
                                {"embedding": embedding_str, "source_id": new_source.id}
                            )
                        except Exception as e:
                            # SQLite tests don't have embedding column, ignore error
                            logger.debug(f"Could not set embedding (column may not exist in SQLite): {e}")
                    
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
                # Try semantic retrieval first
                try:
                    # Import pgvector only if available
                    from pgvector.sqlalchemy import Vector
                    from sqlalchemy import text
                    
                    # Embed the objective for semantic search
                    query_embedding = embed_text(objective)
                    
                    # Handle both numpy arrays and lists
                    if hasattr(query_embedding, 'tolist'):
                        embedding_str = str(query_embedding.tolist())
                    else:
                        embedding_str = str(query_embedding)
                    
                    # Use raw SQL with pgvector cosine distance for semantic retrieval
                    # since embedding column is not defined in the model
                    source_ids = session.execute(
                        text("""
                            SELECT id FROM sources 
                            WHERE embedding IS NOT NULL 
                            ORDER BY embedding <=> cast(:query_embedding as vector)
                            LIMIT 5
                        """),
                        {"query_embedding": embedding_str}
                    ).scalars().all()
                    
                    # Convert IDs to SourceModel objects
                    if source_ids:
                        sources = session.query(SourceModel).filter(SourceModel.id.in_(source_ids)).all()
                        return sources
                except ImportError:
                    logger.warning("pgvector not available, falling back to relevance_score")
                except Exception as e:
                    logger.warning(f"Semantic retrieval failed (embedding column may not exist in SQLite): {e}")
                    session.rollback()  # Rollback failed transaction before fallback
                
                # Fallback to relevance_score ordering (original behavior)
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
                    # Normalize channel to supported values
                    channel = item.get("channel", "X")
                    # Normalize google/seo/blog to supported publishers
                    if channel.lower() in ["google", "seo", "blog"]:
                        channel = "google"
                    elif channel.lower() == "twitter":
                        channel = "x"
                    elif channel.lower() not in ["x", "twitter", "moltbook", "general", "aifintech", "aiagents", "telegram"]:
                        channel = "x"  # Default to X for unknown channels

                    new_item = ContentItemModel(
                        title=item.get("title", "Planned Content"),
                        channel=channel,
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
                    record_event(session, self.name, "content_planned", f"Planned item for {channel}", {"item_id": new_item.id})
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
        self._load_technical_spec()

    def _load_technical_spec(self) -> None:
        """Load the AiFinPay technical specification for verification."""
        import json
        import os
        spec_path = os.path.join(os.path.dirname(__file__), "technical_spec.json")
        try:
            with open(spec_path, 'r') as f:
                self.technical_spec = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load technical spec: {e}")
            self.technical_spec = {}

    def _verify_technical_claims(self, content: str) -> Dict[str, Any]:
        """Verify technical claims against the AiFinPay specification."""
        import re
        
        verified_claims = []
        failed_claims = []
        
        # Extract potential technical claims (API endpoints, networks, features, etc.)
        content_lower = content.lower()
        
        # Check API endpoints
        if self.technical_spec.get("api_endpoints"):
            for endpoint in self.technical_spec["api_endpoints"]:
                if endpoint.lower() in content_lower:
                    verified_claims.append(f"API endpoint: {endpoint}")
        
        # Check for invented endpoints (common patterns)
        invented_patterns = [
            r'/api/v\d+/[a-z_]+',
            r'/[a-z]+/[a-z_]+/create',
            r'/[a-z]+/[a-z_]+/delete'
        ]
        for pattern in invented_patterns:
            matches = re.findall(pattern, content_lower)
            for match in matches:
                if match not in [e.lower() for e in self.technical_spec.get("api_endpoints", [])]:
                    failed_claims.append(f"Potential invented endpoint: {match}")
        
        # Check supported networks
        if self.technical_spec.get("supported_networks"):
            for network in self.technical_spec["supported_networks"]:
                if network.lower() in content_lower:
                    verified_claims.append(f"Supported network: {network}")
        
        # Check for unsupported blockchain networks (common inventions)
        unsupported_networks = ["ethereum", "bitcoin", "solana", "polygon", "bsc", "avalanche"]
        for network in unsupported_networks:
            if network in content_lower and network not in [n.lower() for n in self.technical_spec.get("supported_networks", [])]:
                failed_claims.append(f"Unsupported network mentioned: {network}")
        
        # Check supported features
        if self.technical_spec.get("supported_features"):
            for feature in self.technical_spec["supported_features"]:
                if feature.lower() in content_lower:
                    verified_claims.append(f"Supported feature: {feature}")
        
        # Check authentication methods
        if self.technical_spec.get("authentication_methods"):
            for auth_method in self.technical_spec["authentication_methods"]:
                if auth_method.lower() in content_lower:
                    verified_claims.append(f"Authentication method: {auth_method}")
        
        # Determine overall status
        if failed_claims:
            status = "failed"
            details = f"Found {len(failed_claims)} unverifiable claims: {', '.join(failed_claims[:3])}"
        elif verified_claims:
            status = "verified"
            details = f"Verified {len(verified_claims)} technical claims"
        else:
            status = "pending"
            details = "No technical claims found for verification"
        
        return {
            "status": status,
            "verified_claims": verified_claims,
            "failed_claims": failed_claims,
            "details": details
        }

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

        # Add randomness for unique content
        import random
        from datetime import datetime

        source_text = source.raw_content if source else "No source provided."

        technical_topics = [
            "SDK integration basics",
            "API authentication methods",
            "Error handling best practices",
            "Rate limiting strategies",
            "Security implementation",
            "Testing methodologies",
            "Performance optimization",
            "Documentation standards"
        ]

        tech_angles = [
            "step-by-step tutorial",
            "quick start guide",
            "advanced techniques",
            "troubleshooting common issues",
            "best practices and patterns",
            "architecture overview"
        ]

        random_topic = random.choice(technical_topics)
        random_angle = random.choice(tech_angles)
        timestamp = datetime.now().strftime("%Y-%m-%d")

        system_prompt = (
            f"You are the Technical Content Agent for AiFinPay. "
            f"Today is {timestamp}. Generate UNIQUE content about {random_topic} using a {random_angle} approach. "
            f"NEVER repeat the same content. Each tutorial must be distinct and original. "
            "RULE: Must not invent endpoints, functions, supported networks, transactions, or integrations. "
            "Stick strictly to verifiable technical facts about AiFinPay and its ecosystem."
        )
        schema_hint = "{body: string}"

        try:
            generation = await complete_json(
                model=self.model,
                system_prompt=system_prompt,
                user_content=f"Title: {item.title}\nObjective: {item.objective}\nSource: {source_text}",
                schema_hint=schema_hint
            )
        except Exception as e:
            logger.warning(f"LLM generation failed: {e}, using fallback random generation")
            generation = {
                "body": f"# {random_topic.title()}: {random_angle.title()} Guide\n\nWelcome to this {random_angle} guide for {random_topic}. In this tutorial, we'll cover the essential aspects of implementing {random_topic} in your AiFinPay applications.\n\n## Getting Started\n\nBefore diving into {random_topic}, ensure you have:\n- A valid API key\n- Basic understanding of REST APIs\n- Development environment set up\n\n## Step-by-Step Process\n\n1. Initialize the client with your credentials\n2. Configure the necessary parameters\n3. Make your first API call\n4. Handle responses appropriately\n5. Implement error handling\n\n## Common Issues and Solutions\n\n- Authentication failures: Check your API key\n- Rate limits: Implement proper retry logic\n- Network errors: Add timeout handling\n\n## Best Practices\n\n- Always validate inputs\n- Log important events\n- Monitor API usage\n- Keep credentials secure\n\nThis {random_angle} approach to {random_topic} will help you build robust applications with AiFinPay."
            }

        # Real technical verification against AiFinPay spec
        verification_result = self._verify_technical_claims(generation.get("body", ""))
        
        def _update_item():
            with get_sync_session() as session:
                db_item = session.query(ContentItemModel).filter(ContentItemModel.id == content_item_id).first()
                db_item.body = generation.get("body")
                db_item.author_agent = self.name
                
                # Set verification status based on results
                if verification_result["status"] == "failed":
                    db_item.technical_verification_status = "flagged"
                    db_item.status = "draft"  # Keep as draft for human review
                    record_event(session, self.name, "technical_verification_failed", 
                                f"Technical content flagged for unverifiable claims: {content_item_id}", 
                                {"item_id": content_item_id, "failed_claims": verification_result["failed_claims"]})
                elif verification_result["status"] == "verified":
                    db_item.technical_verification_status = "verified"
                    db_item.status = "draft"
                    record_event(session, self.name, "technical_verification_passed", 
                                f"Technical content verified: {content_item_id}", 
                                {"item_id": content_item_id, "verified_claims": verification_result["verified_claims"]})
                else:  # pending
                    db_item.technical_verification_status = "pending"
                    db_item.status = "draft"
                    record_event(session, self.name, "technical_verification_pending", 
                                f"No technical claims found for verification: {content_item_id}", 
                                {"item_id": content_item_id})
                
                db_item.technical_verification_details = verification_result["details"]
                session.commit()

        await asyncio.to_thread(_update_item)
        
        return {
            "agent": self.name, 
            "outcome": "tutorial_generated", 
            "item_id": content_item_id,
            "verification_status": verification_result["status"],
            "verification_details": verification_result["details"]
        }

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

        # Add randomness for unique content
        import random
        from datetime import datetime

        source_text = source.raw_content if source else "No source provided."

        founder_themes = [
            "Building the future of AI-first finance",
            "Democratizing access to sophisticated financial tools",
            "Our vision for autonomous financial services",
            "Revolutionizing traditional banking with AI",
            "Empowering users through intelligent automation",
            "Creating transparent and efficient financial systems"
        ]

        call_to_actions = [
            "Join us in this journey",
            "Let's build the future together",
            "Your feedback matters",
            "Be part of the revolution",
            "Together we can transform finance"
        ]

        random_theme = random.choice(founder_themes)
        random_cta = random.choice(call_to_actions)
        timestamp = datetime.now().strftime("%Y-%m-%d")

        system_prompt = (
            f"You are the Founder Content Agent for AiFinPay. "
            f"Today is {timestamp}. Generate UNIQUE content about {random_theme}. "
            f"NEVER repeat the same content. Each post must be distinct and original. "
            f"Include a call to action: {random_cta}. "
            "Generate several text variants of a high-impact leadership post. "
            "Each variant must explain its target audience (e.g., Investors, Developers, Enterprise Partners)."
        )
        schema_hint = "{variants: [{audience: string, text: string}]}"

        try:
            generation = await complete_json(
                model=self.model,
                system_prompt=system_prompt,
                user_content=f"Topic: {item.title}\nObjective: {item.objective}\nSource: {source_text}",
                schema_hint=schema_hint
            )
        except Exception as e:
            logger.warning(f"LLM generation failed: {e}, using fallback random generation")
            generation = {
                "variants": [
                    {
                        "audience": "Investors",
                        "text": f"{random_theme} #AI #FinTech #DeFi {random_cta}"
                    },
                    {
                        "audience": "Developers",
                        "text": f"Building tools for developers to transform finance with AI. Check out our new SDK! #DevTools #API {random_cta}"
                    },
                    {
                        "audience": "Enterprise Partners",
                        "text": f"Enterprise solutions for autonomous financial services. Let's discuss how we can work together. #B2B #Partnership {random_cta}"
                    }
                ]
            }

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

class SEOContentAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="SEO Content",
            role="SEO Writer",
            description="Generates Google-search-optimized long-form content with SEO metadata.",
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

        # Add randomness to content generation
        import random
        from datetime import datetime

        source_text = source.raw_content if source else "No source provided."

        # Random elements for diverse content
        topics = [
            "DeFi Integration Strategies",
            "AI-First Financial Services",
            "Automated Trading Systems",
            "Blockchain Security Best Practices",
            "Smart Contract Optimization",
            "Cross-Chain Liquidity Solutions",
            "Tokenomics Design Principles",
            "Yield Farming Automation",
            "Regulatory Compliance in DeFi",
            "Scalable Crypto Infrastructure"
        ]

        angles = [
            "comprehensive guide for beginners",
            "advanced strategies for experienced users",
            "technical deep dive for developers",
            "business use cases for enterprises",
            "security considerations for all users",
            "optimization techniques for maximum efficiency"
        ]

        random_topic = random.choice(topics)
        random_angle = random.choice(angles)
        timestamp = datetime.now().strftime("%Y-%m-%d")

        system_prompt = (
            f"You are the SEO Content Agent for AiFinPay. "
            f"Today is {timestamp}. Generate UNIQUE, fresh content about {random_topic} from a {random_angle} perspective. "
            "NEVER repeat the same content twice. Each generation must be distinct and original. "
            "Include: SEO title tag (50-60 chars), meta description (150-160 chars), H1, H2 subheadings, "
            "target keyword list (3-5 keywords), and the article body. "
            "Focus on SEO best practices: keyword density, readability, and search intent matching."
        )
        schema_hint = "{seo_title_tag: string, meta_description: string, keywords: [string], h1: string, h2_subheadings: [string], body: string}"

        try:
            generation = await complete_json(
                model=self.model,
                system_prompt=system_prompt,
                user_content=f"Title: {item.title}\nObjective: {item.objective}\nSource: {source_text}",
                schema_hint=schema_hint
            )
        except Exception as e:
            # Fallback to random content generation if LLM fails
            logger.warning(f"LLM generation failed: {e}, using fallback random generation")
            generation = {
                "seo_title_tag": f"{random_topic} - {random_angle} Guide",
                "meta_description": f"Learn about {random_topic} from a {random_angle} perspective in this comprehensive guide.",
                "keywords": [random_topic.lower(), "defi", "ai", "blockchain", "cryptocurrency"],
                "h1": f"{random_topic}: {random_angle.title()} Guide",
                "h2_subheadings": [
                    f"Understanding {random_topic}",
                    f"Key Benefits of {random_angle}",
                    f"Implementation Strategies",
                    f"Best Practices and Tips"
                ],
                "body": f"# {random_topic}: {random_angle.title()} Guide\n\nIn this comprehensive guide, we explore {random_topic} from a {random_angle} perspective. This approach is designed to help you understand the fundamentals and apply them effectively.\n\n## Understanding {random_topic}\n\n{random_topic} represents a significant advancement in the financial technology landscape. By focusing on {random_angle}, we can unlock new possibilities for automation and efficiency.\n\n## Key Benefits of {random_angle}\n\nThe {random_angle} approach offers several advantages:\n- Improved efficiency in operations\n- Enhanced security through automation\n- Better user experience with streamlined processes\n- Cost savings through optimization\n\n## Implementation Strategies\n\nTo implement {random_topic} effectively:\n1. Start with a clear understanding of requirements\n2. Choose the right tools and platforms\n3. Test thoroughly before deployment\n4. Monitor performance and iterate\n\n## Best Practices and Tips\n\n- Always prioritize security in financial applications\n- Keep user experience central to design decisions\n- Stay updated with regulatory requirements\n- Maintain clear documentation\n\nThis guide provides a foundation for implementing {random_topic} with a {random_angle} approach."
            }

        def _update_item():
            with get_sync_session() as session:
                db_item = session.query(ContentItemModel).filter(ContentItemModel.id == content_item_id).first()
                db_item.body = generation.get("body")
                # Set channel to google for proper publisher resolution and submolt routing
                if not db_item.channel or db_item.channel == "X":
                    db_item.channel = "google"  # This will route to MultiChannelPublisher
                # Store SEO metadata in variants to preserve it
                seo_metadata = {
                    "seo_title_tag": generation.get("seo_title_tag"),
                    "meta_description": generation.get("meta_description"),
                    "keywords": generation.get("keywords"),
                    "h1": generation.get("h1"),
                    "h2_subheadings": generation.get("h2_subheadings")
                }
                db_item.variants = seo_metadata
                db_item.author_agent = self.name
                db_item.status = "draft"
                record_event(session, self.name, "content_generated", f"Generated SEO content for {content_item_id}", {"item_id": content_item_id, "seo_metadata": seo_metadata})
                session.commit()

        await asyncio.to_thread(_update_item)
        return {"agent": self.name, "outcome": "seo_content_generated", "item_id": content_item_id}

    def get_capabilities(self) -> Dict[str, Any]:
        return {"purpose": "Creates Google-optimized content with SEO metadata...", "tools": ["seo_optimization"], "inputs": ["topic"], "outputs": ["draft"], "policies": ["seo_best_practices"], "kpis": ["search_ranking"]}

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
        
        # Initialize analytics clients
        self.gsc_client = GoogleSearchConsoleClient()
        
        # Define metric data sources and their availability
        # Check if Google Search Console is configured for real analytics
        gsc_available = self.gsc_client.is_configured
        
        self.metric_data_sources = {
            "publications": {"source": "content_items", "available": True, "integration": "database"},
            "impressions": {"source": "google_search_console", "available": gsc_available, "integration": "google_search_console"},
            "clicks": {"source": "google_search_console", "available": gsc_available, "integration": "google_search_console"},
            "engagement": {"source": "google_search_console", "available": gsc_available, "integration": "google_search_console"},
            "website_visits": {"source": "google_search_console", "available": gsc_available, "integration": "google_search_console"},
            "registrations": {"source": "user_platform", "available": False, "integration": "auth_service"},
            "sdk_installs": {"source": "package_registry", "available": False, "integration": "pypi/npm"},
            "mcp_activations": {"source": "mcp_sidecar", "available": True, "integration": "mcp_audit_events"},
            "github_activity": {"source": "github_api", "available": False, "integration": "github"},
            "conversions": {"source": "user_platform", "available": False, "integration": "analytics"},
            "mcp_calls": {"source": "audit_events", "available": True, "integration": "database"}
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        timeframe = input_data.get('timeframe', 'daily')  # daily or weekly
        
        # Collect metrics from available data sources
        metrics_report = {}
        
        for metric_name, metric_config in self.metric_data_sources.items():
            if metric_config["available"]:
                # Collect real data for available metrics
                if metric_name == "publications":
                    metrics_report[metric_name] = await self._get_publications_count()
                elif metric_name == "mcp_calls":
                    metrics_report[metric_name] = await self._get_mcp_calls_count()
                elif metric_name == "mcp_activations":
                    metrics_report[metric_name] = await self._get_mcp_activations_count()
                elif metric_name in ["impressions", "clicks", "engagement", "website_visits"]:
                    # Fetch real data from Google Search Console if configured
                    gsc_data = await self._get_gsc_metrics(metric_name)
                    metrics_report[metric_name] = gsc_data
                else:
                    # For other available metrics, implement specific data collection
                    metrics_report[metric_name] = f"Data from {metric_config['source']}"
                
                # Add data source info
                metrics_report[f"{metric_name}_data_source"] = metric_config["integration"]
            else:
                # Return unavailable status for unconfigured metrics
                metrics_report[metric_name] = "unavailable/not configured"
                metrics_report[f"{metric_name}_data_source"] = metric_config["integration"]
        
        # Generate recommendations based on available data
        recommendations = self._generate_recommendations(metrics_report, timeframe)
        
        # Update content_items with real analytics data if available
        await self._update_content_items_analytics(metrics_report)
        
        report = {
            "timeframe": timeframe,
            "metrics": metrics_report,
            "recommendations": recommendations,
            "data_source_summary": {
                "available_metrics": [m for m, c in self.metric_data_sources.items() if c["available"]],
                "unavailable_metrics": [m for m, c in self.metric_data_sources.items() if not c["available"]]
            }
        }

        with get_sync_session() as session:
            record_event(session, self.name, "metrics_reported", f"Generated {timeframe} metrics report", report)
            session.commit()

        return {"agent": self.name, "outcome": "metrics_generated", "report": report}
    
    async def _get_publications_count(self) -> int:
        """Count real published content items (excludes dry-run and fake post IDs)."""
        def _count():
            with get_sync_session() as session:
                return session.query(ContentItemModel).filter(
                    ContentItemModel.status == "published",
                    ContentItemModel.post_id != "dry-run-id",
                    ~ContentItemModel.post_id.like("dry-run%")
                ).count()
        
        return await asyncio.to_thread(_count)
    
    async def _get_mcp_calls_count(self) -> int:
        """Count successful MCP calls from audit events."""
        def _count():
            with get_sync_session() as session:
                return session.query(AuditEventModel).filter(
                    AuditEventModel.event_type == "mcp_call_succeeded"
                ).count()
        
        return await asyncio.to_thread(_count)
    
    async def _get_mcp_activations_count(self) -> int:
        """Count MCP activations (distinct agents that made successful calls)."""
        def _count():
            with get_sync_session() as session:
                from sqlalchemy import func
                return session.query(AuditEventModel.agent_name).filter(
                    AuditEventModel.event_type == "mcp_call_succeeded"
                ).distinct().count()
        
        return await asyncio.to_thread(_count)
    
    async def _get_gsc_metrics(self, metric_name: str) -> Dict[str, Any]:
        """Fetch real metrics from Google Search Console if configured."""
        try:
            # Get base URL from settings for GSC query
            base_url = getattr(settings, "SEO_PAGES_BASE_URL", "https://aifinpay.io")
            
            # Map metric names to GSC data fields
            metric_mapping = {
                "impressions": "impressions",
                "clicks": "clicks", 
                "engagement": "engagement",
                "website_visits": "impressions"  # Use impressions as proxy for visits
            }
            
            gsc_field = metric_mapping.get(metric_name, metric_name)
            
            # Fetch data from GSC client
            gsc_data = await self.gsc_client.get_site_metrics(base_url)
            
            if gsc_data.get("available"):
                # Return the specific metric value if available
                return {
                    "value": gsc_data.get(gsc_field, 0),
                    "data_source": "Google Search Console",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                # Return unavailable status with explanation
                return {
                    "value": "unavailable/not configured",
                    "data_source": "Google Search Console",
                    "error": gsc_data.get("error", "Unknown error"),
                    "message": gsc_data.get("message", "unavailable/not configured")
                }
                
        except Exception as e:
            logger.error(f"Error fetching GSC metrics for {metric_name}: {e}")
            return {
                "value": "error fetching data",
                "data_source": "Google Search Console",
                "error": str(e)
            }
    
    async def _update_content_items_analytics(self, metrics_report: Dict[str, Any]) -> None:
        """Update content_items table with real analytics data from Google Search Console."""
        try:
            # Extract GSC metrics if available
            impressions = metrics_report.get("impressions", {})
            clicks = metrics_report.get("clicks", {})
            
            # Only update if we have real numeric data (not error messages)
            if isinstance(impressions, dict) and isinstance(impressions.get("value"), (int, float)):
                def _update():
                    with get_sync_session() as session:
                        # Update all published content items with aggregate metrics
                        # In a real implementation, you might want to map URLs to specific content items
                        from datetime import datetime, timezone
                        session.query(ContentItemModel).filter(
                            ContentItemModel.status == "published"
                        ).update({
                            "impressions": impressions.get("value"),
                            "clicks": clicks.get("value") if isinstance(clicks, dict) and isinstance(clicks.get("value"), (int, float)) else None,
                            "last_analytics_update": datetime.now(timezone.utc)
                        })
                        session.commit()
                
                await asyncio.to_thread(_update)
                logger.info("Updated content_items with real analytics data from Google Search Console")
                
        except Exception as e:
            logger.error(f"Error updating content_items analytics: {e}")
    
    def _generate_recommendations(self, metrics: dict, timeframe: str) -> str:
        """Generate recommendations based on available metrics."""
        recommendations = []
        
        if metrics.get("publications") != "unavailable/not configured":
            pubs = metrics["publications"]
            if isinstance(pubs, int) and pubs < 5:
                recommendations.append("Increase content publication frequency to improve market presence.")
            elif isinstance(pubs, int) and pubs > 20:
                recommendations.append("Content publication rate is strong. Focus on quality and engagement optimization.")
        
        if metrics.get("mcp_calls") != "unavailable/not configured":
            mcp_calls = metrics["mcp_calls"]
            if isinstance(mcp_calls, int) and mcp_calls < 10:
                recommendations.append("Increase MCP integration testing to ensure protocol reliability.")
        
        # Add recommendations for unavailable metrics
        unavailable = [m for m, v in metrics.items() if v == "unavailable/not configured" and not m.endswith("_data_source")]
        if unavailable:
            recommendations.append(f"Configure integrations for unavailable metrics to enable comprehensive analytics: {', '.join(unavailable[:3])}")
        
        if not recommendations:
            recommendations.append("Current metrics indicate stable performance. Continue monitoring for optimization opportunities.")
        
        return " ".join(recommendations)

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "purpose": "Collects real metrics: publications, impressions, clicks, engagement rate, website visits, registrations, SDK installs, MCP activations, GitHub stars, and conversions. Links every metric to its actual data source. Produces daily and weekly reports with concrete recommendations for the next cycle.",
            "tools": ["data_collection", "report_generation", "recommendation_engine"],
            "inputs": ["timeframe", "metrics_to_track"],
            "outputs": ["daily_report", "weekly_report", "recommendations"],
            "policies": ["real_metrics_only", "data_source_linking", "no_fabrication"],
            "kpis": ["report_accuracy", "recommendation_effectiveness"],
            "data_sources": self.metric_data_sources
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
        discussions = input_data.get("discussions")
        if discussions is None:
            logger.warning(
                "Community Engagement received no discovered discussions; creating zero proposals"
            )
            discussions = []

        if not isinstance(discussions, list):
            raise ValueError("Community engagement discussions must be a list")

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
