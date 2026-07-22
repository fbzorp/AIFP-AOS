# AiFinPay AOS New Architecture (Day 1 Deliverable)

## 9 Specialized Agents (per Assignment)
1. **Growth Orchestrator**: Plan creation, task distribution, retries, daily reports.
2. **Market Intelligence Agent**: Track topics, store sources, deduplicate.
3. **Content Strategy Agent**: Weekly plans, formats, KPIs.
4. **Technical Content Agent**: Technical posts, verified against SDK/MCP.
5. **Founder Content Agent**: Founder materials with approval.
6. **Social Publishing Agent**: Publish to X, Telegram, Moltbook (approved only).
7. **Community Engagement Agent**: Prepare replies, risk assessment.
8. **Analytics Agent**: Real metrics tracking.
9. **Compliance & Brand Agent**: Content review, block violations.

## Tech Stack (Strict Follow)
- Backend: Python + Google ADK + FastAPI + LiteLLM (DeepSeek) + Dramatiq
- DB: PostgreSQL + Alembic
- Cache: Redis
- Frontend: React + TS
- Integrations: AiFinPay MCP/x402, Moltbook

## Data Models (Extend apps/models/)
- Agent, Campaign, ContentItem, AuditEvent, etc.

**All parameters explicit. No placeholders.**

Next: Implement in code.