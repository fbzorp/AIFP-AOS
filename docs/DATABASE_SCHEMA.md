# Database Schema

## Overview

AIFP-AOS uses PostgreSQL as the primary database with the following schema:

## Core Tables

### Agents
- **Table**: `agents`
- **Purpose**: Store agent configurations and display names
- **Key Fields**: 
  - `id` (UUID, primary key)
  - `display_name` (text)
  - `config` (JSONB)
  - `is_active` (boolean)
- **Migration**: `20260721_initial_foundation.py`, `20260722_enriched_agents.py`

### Content Items
- **Table**: `content_items`
- **Purpose**: Store content drafts and published content
- **Key Fields**:
  - `id` (UUID, primary key)
  - `title` (text)
  - `content` (text)
  - `status` (enum: draft, submitted, approved, published, rejected)
  - `variant` (text, for A/B testing)
  - `compliance_approved` (boolean)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)
- **Migration**: `20260721_initial_foundation.py`, `20260725_add_compliance_and_variants.py`, `e97c7449d888_add_sources_and_enrich_content_items.py`

### Approval Queue
- **Table**: `approvals`
- **Purpose**: Content approval workflow management
- **Key Fields**:
  - `id` (UUID, primary key)
  - `content_id` (UUID, foreign key to content_items)
  - `status` (enum: pending, approved, rejected)
  - `submitted_at` (timestamp)
  - `reviewed_at` (timestamp)
  - `reviewer_id` (UUID)
  - `scheduled_at` (timestamp)
- **Migration**: `20260721_initial_foundation.py`, `20260724_enrich_approvals.py`

### Tasks
- **Table**: `tasks`
- **Purpose**: Background task management
- **Key Fields**:
  - `id` (UUID, primary key)
  - `task_type` (text)
  - `status` (enum: pending, running, completed, failed)
  - `payload` (JSONB)
  - `result` (JSONB)
  - `error_message` (text)
  - `created_at` (timestamp)
  - `completed_at` (timestamp)
- **Migration**: `20260723_create_tasks_table.py`

### Sources
- **Table**: `sources`
- **Purpose**: Store content sources and reference materials
- **Key Fields**:
  - `id` (UUID, primary key)
  - `url` (text)
  - `title` (text)
  - `source_type` (text)
  - `metadata` (JSONB)
- **Migration**: `e97c7449d888_add_sources_and_enrich_content_items.py`

### Engagement Proposals
- **Table**: `engagement_proposals`
- **Purpose**: Community engagement proposals
- **Key Fields**:
  - `id` (UUID, primary key)
  - `content_id` (UUID, foreign key to content_items)
  - `target_submolt` (text)
  - `status` (enum: pending, approved, rejected)
  - `created_at` (timestamp)
- **Migration**: `20260726_days_10_11_updates.py`

### Payments
- **Table**: `payments`
- **Purpose**: Payment processing and tracking
- **Key Fields**:
  - `id` (UUID, primary key)
  - `amount_usd` (decimal)
  - `recipient_address` (text)
  - `status` (enum: pending, approved, executing, completed, failed, rejected)
  - `network` (text: devnet, mainnet)
  - `tx_hash` (text)
  - `explorer_url` (text)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)
  - `mcp_call_id` (text)
  - `mcp_cost_usd` (decimal)
- **Migration**: `20260729_add_payments_table.py`

### Audit Events
- **Table**: `audit_events`
- **Purpose**: Audit trail for all system events
- **Key Fields**:
  - `id` (UUID, primary key)
  - `agent_name` (text)
  - `event_type` (text)
  - `event_data` (JSONB)
  - `timestamp` (timestamp)
- **Migration**: `7ff8e3bbcdfd_add_metadata_to_audit_and_schema_updates.py`

## Migration History

1. **20260721_initial_foundation.py**: Base schema with agents, content_items, approvals, audit_events
2. **20260722_enriched_agents.py**: Enhanced agent configuration
3. **20260723_create_tasks_table.py**: Added background task management
4. **20260724_enrich_approvals.py**: Enhanced approval workflow with scheduling
5. **20260725_add_compliance_and_variants.py**: Added compliance approval and content variants
6. **7ff8e3bbcdfd_add_metadata_to_audit_and_schema_updates.py**: Enhanced audit events with metadata
7. **e97c7449d888_add_sources_and_enrich_content_items.py**: Added sources table and content item enrichment
8. **20260726_days_10_11_updates.py**: Added engagement proposals for community features
9. **20260729_add_payments_table.py**: Added payment processing functionality

## Relationships

- `content_items` → `approvals` (one-to-many)
- `content_items` → `engagement_proposals` (one-to-many)
- `content_items` → `sources` (many-to-many via junction table)
- `approvals` → `content_items` (many-to-one)
- `payments` → audit events (via event data)

## Indexes

Primary indexes on all UUID primary keys.
Additional indexes on frequently queried fields:
- `content_items.status`
- `content_items.created_at`
- `approvals.status`
- `approvals.submitted_at`
- `payments.status`
- `payments.created_at`
- `audit_events.timestamp`
- `audit_events.event_type`
