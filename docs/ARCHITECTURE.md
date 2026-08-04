# AIFP-AOS Architecture

## System Architecture

```mermaid
graph TB
    subgraph Client Layer
        Dashboard[Dashboard React App]
        API[FastAPI REST API]
    end

    subgraph Application Layer
        APIAuth[JWT Auth & RBAC]
        Payments[Payment Router]
        Approvals[Approval Router]
        System[System Router]
    end

    subgraph Agent Layer
        MarketingManager[Marketing Manager (ADK Root Agent)]
        MarketIntelligence[Market Intelligence Agent]
        ContentStrategy[Content Strategy Agent]
        TechnicalWriter[Technical Writer Agent]
        FounderContent[Founder Content Agent]
        SocialPublishing[Social Publishing Agent]
        CommunityEngagement[Community Engagement Agent]
        Analytics[Analytics Agent]
        ComplianceBrand[Compliance & Brand Agent]
        GrowthOrchestrator[Growth Orchestrator]
    end

    subgraph Integration Layer
        DeepSeek[DeepSeek LLM]
        Moltbook[Moltbook API]
        AiFinPay[AiFinPay Payment]
        X402[X402 Protocol]
        Wallet[Wallet Client]
        MCP[MCP Client]
    end

    subgraph Data Layer
        PostgreSQL[(PostgreSQL)]
        Redis[(Redis)]
    end

    subgraph Infrastructure
        Nginx[Nginx Reverse Proxy]
        Docker[Docker Compose]
    end

    Dashboard -->|HTTP| Nginx
    API -->|HTTP| Nginx
    Nginx --> API
    API --> APIAuth
    API --> Payments
    API --> Approvals
    API --> System

    MarketingManager --> DeepSeek
    MarketingManager --> MarketIntelligence
    MarketingManager --> ContentStrategy
    MarketingManager --> TechnicalWriter
    MarketingManager --> FounderContent
    MarketingManager --> SocialPublishing
    MarketingManager --> CommunityEngagement
    MarketingManager --> Analytics
    MarketingManager --> ComplianceBrand
    
    MarketIntelligence --> DeepSeek
    ContentStrategy --> DeepSeek
    TechnicalWriter --> DeepSeek
    FounderContent --> DeepSeek
    SocialPublishing --> Moltbook
    CommunityEngagement --> Moltbook
    Analytics --> Moltbook
    ComplianceBrand --> DeepSeek
    
    GrowthOrchestrator --> MarketingManager

    Payments --> AiFinPay
    Payments --> X402
    Payments --> Wallet
    Payments --> MCP

    API --> PostgreSQL
    API --> Redis
    Worker --> PostgreSQL
    Worker --> Redis

    DeepSeek --> API
    Moltbook --> API
    AiFinPay --> API
    X402 --> API
    Wallet --> API
    MCP --> API
```

## Component Overview

### Client Layer
- **Dashboard**: React-based admin interface for content management and approval workflows
- **API**: FastAPI REST API with JWT authentication and RBAC

### Application Layer
- **APIAuth**: JWT token generation and verification, role-based access control with 4-role system (founder_admin, smm_manager, viewer, service_agent)
- **Payments**: Payment creation, approval, and execution with safety controls
- **Approvals**: Content approval queue and workflow management
- **System**: Health checks, configuration, and system status endpoints

### Agent Layer
- **Marketing Manager (ADK Root Agent)**: Google ADK-based routing coordinator that intelligently delegates to specialists using DeepSeek reasoning model
- **Market Intelligence Agent**: Researches market trends, discussions, and opportunities
- **Content Strategy Agent**: Generates content strategy and content calendar
- **Technical Writer Agent**: Creates technical documentation and blog posts
- **Founder Content Agent**: Creates founder-led content and thought leadership pieces
- **Social Publishing Agent**: Manages social media publishing (Moltbook access with approval gating)
- **Community Engagement Agent**: Handles community interactions and engagement proposals (Moltbook access with approval gating)
- **Analytics Agent**: Tracks content performance and provides insights
- **Compliance & Brand Agent**: Ensures content meets brand guidelines and compliance requirements
- **Growth Orchestrator**: Coordinates agents and manages content growth campaigns using ADK routing with static fallback

### Integration Layer
- **DeepSeek LLM**: AI-powered content generation
- **Moltbook API**: Content publishing and analytics platform
- **AiFinPay Payment**: Payment processing and safety controls
- **X402 Protocol**: Cross-chain payment protocol
- **Wallet Client**: Blockchain wallet management
- **MCP Client**: Model Context Protocol integration

### Data Layer
- **PostgreSQL**: Primary database for persistent data
- **Redis**: Caching and task queue

### Infrastructure
- **Nginx**: Reverse proxy with SSL termination and rate limiting
- **Docker Compose**: Container orchestration for multi-environment deployment

## ADK Orchestration

### Marketing Manager Root Agent

The system uses Google ADK (Agent Development Kit) for intelligent agent orchestration:

- **Root Agent**: Marketing Manager (ADK `LlmAgent` with DeepSeek reasoning model)
- **Specialists**: 8 specialized agents wrapped as ADK `FunctionTool` instances
- **Model Gateway**: LiteLlm wrapper (`google.adk.models.lite_llm`) for DeepSeek integration
- **Fallback**: Static steps when `DEEPSEEK_API_KEY` is unavailable (CI/tests)

### Routing Mechanism

**With ADK (DEEPSEEK_API_KEY present)**:
1. Marketing Manager receives campaign objective
2. DeepSeek reasoning model determines optimal specialist sequence
3. ADK Runner executes routing decision
4. Steps fed into existing infrastructure (persistence, audit, dramatiq)
5. Audit event: `adk_routed`

**Without ADK (DEEPSEEK_API_KEY absent)**:
1. System automatically uses static fallback
2. Fixed sequence: Market Intelligence → Content Strategy → Community Engagement
3. Steps fed into existing infrastructure
4. Audit event: `static_fallback`

### Specialist Tool Delegation

Each specialist is exposed as an ADK tool that calls the existing `BaseAgent.execute` interface:

- **Moltbook Access**: Only Social Publishing and Community Engagement have Moltbook publish access
- **Permission Gating**: Existing approval gates (`MOLTBOOK_AUTOPUBLISH`, policy engine) remain enforced
- **Persistence**: CampaignModel/TaskModel persistence unchanged
- **Audit Logging**: All specialist execution logged

### Model Gateway

The system uses the existing LiteLlm factory from `apps/core/models/factory.py`:

```python
from apps.core.models.factory import deepseek_reasoning

# Returns LiteLlm instance when DEEPSEEK_API_KEY is present
# Returns None when DEEPSEEK_API_KEY is absent (graceful degradation)
model = deepseek_reasoning()
```

**Models Used**:
- **Root Agent**: `deepseek/deepseek-v4-pro` (reasoning model)
- **Specialists**: Existing models (can use `deepseek_fast()` or other models)

### Documentation

See [ADK_ORCHESTRATION.md](ADK_ORCHESTRATION.md) for complete documentation on:
- Implementation details
- Testing strategy
- Configuration
- Monitoring and debugging
- Security considerations
- Troubleshooting

## Data Flow

### Content Creation Flow
1. Growth Orchestrator identifies growth opportunities
2. Content Strategy Agent generates content strategy
3. Technical Writer Agent creates content based on strategy
4. Compliance & Brand Agent reviews and approves content
5. Content submitted to approval queue
6. Human operator reviews and approves content
7. Content published to Moltbook via API

### Payment Processing Flow
1. Payment request created via API
2. Safety checks applied (kill switch, allowlist, limits)
3. Payment routed to appropriate processor (AiFinPay/X402)
4. Blockchain transaction executed
5. Payment status updated in database
6. Audit event recorded

### Security Flow
1. Client authenticates with credentials
2. JWT token generated with user role
3. Token validated on each request
4. RBAC checks applied based on user role and permissions
5. Request processed if authorized

## Role-Based Access Control (RBAC)

### 4-Role System

The system implements a 4-role RBAC model with granular permission sets:

#### 1. Founder/Admin (`founder_admin`)
- **Permissions**: `read`, `write`, `approve`, `execute`, `publish`, `admin`
- **Description**: Full system access including administrative operations, payment execution, and content publishing
- **Use Case**: System administrators and founders requiring complete control

#### 2. SMM Manager (`smm_manager`)
- **Permissions**: `read`, `write`, `approve`, `publish`
- **Description**: Content and campaign management with approval and publishing rights, but no execution or admin privileges
- **Use Case**: Social media managers who can create, approve, and publish content but cannot execute payments or perform admin operations

#### 3. Viewer (`viewer`)
- **Permissions**: `read`
- **Description**: Read-only access for viewing content, campaigns, and system status
- **Use Case**: Stakeholders who need visibility without modification rights

#### 4. Service/Agent (`service_agent`)
- **Permissions**: `read`, `execute`
- **Description**: Machine-to-machine service account with read and execute permissions only
- **Use Case**: Automated agents and services that can read data and execute tasks but cannot approve, publish, or perform administrative operations

### Permission Enforcement

- **Approve Operations**: Restricted to `founder_admin` and `smm_manager` roles
- **Publish Operations**: Restricted to `founder_admin` and `smm_manager` roles
- **Execute Operations**: Restricted to `founder_admin` and `service_agent` roles
- **Write Operations**: Restricted to `founder_admin` and `smm_manager` roles
- **Admin Operations**: Restricted to `founder_admin` role only
- **Read Operations**: Available to all roles

### API Endpoint Protection

Key endpoints are protected by permission-based dependencies:
- `/api/v1/approvals/content/{id}/approve` → `require_approver`
- `/api/v1/approvals/content/{id}/publish` → `require_publisher`
- `/api/v1/payments/{id}/execute` → `require_admin`
- `/api/v1/campaigns` (POST) → `require_writer`
- `/api/v1/tasks` (POST) → `require_writer`

## Deployment Architecture

### Development Environment
- Source code bind-mounts for hot reload
- In-memory SQLite for tests
- PostgreSQL for development data
- No SSL (HTTP only)
- Debug logging enabled

### Staging Environment
- Built Docker images (no bind-mounts)
- PostgreSQL persistent volumes
- Redis persistent volumes
- Self-signed SSL certificates
- Production-like configuration
- Nginx reverse proxy

### Production Environment
- Built Docker images (no bind-mounts)
- PostgreSQL persistent volumes
- Redis persistent volumes
- Let's Encrypt SSL certificates
- Production configuration
- Nginx reverse proxy
- Monitoring and alerting
