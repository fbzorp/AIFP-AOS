# AiFinPay Autonomous Growth OS (AIFP-AOS)

A production-ready autonomous growth system with multi-agent orchestration, content strategy, AI content generation, approval workflows, and secure payment processing capabilities.

## Overview

AIFP-AOS is a comprehensive content growth platform that combines:
- **Multi-Agent System**: Specialized agents for content strategy, technical writing, brand compliance, and analytics
- **AI Content Generation**: DeepSeek-powered content creation with verification and approval workflows
- **Payment Integration**: Secure blockchain payment processing with kill switches and safety controls
- **Content Management**: Approval queues, content editing, and publishing workflows
- **Analytics**: Moltbook integration for content performance tracking
- **Security**: JWT authentication, RBAC, and comprehensive security controls

## Environment Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.12+ (for local development)
- PostgreSQL 17 (for local development)
- Redis 8 (for local development)
- **Server Requirements**: Minimum 4GB RAM, 2 vCPU, 20-30GB storage for production deployment (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#server--vps-requirements) for detailed sizing)

### Local Development

```bash
# Start development environment
docker compose -f docker-compose.dev.yml up -d

# Run tests
docker compose -f docker-compose.dev.yml exec -T api uv run pytest tests/ -v

# View logs
docker compose -f docker-compose.dev.yml logs -f api
```

The development environment includes:
- Hot reload for Python code
- Source code bind-mounts
- In-memory SQLite for tests
- PostgreSQL for development data
- Development dashboard (http://localhost:3000)
- API server (http://localhost:8000)

### Staging Environment

```bash
# Copy and configure environment file
cp .env.example .env.staging
# Edit .env.staging with your staging configuration

# Build and start staging
docker compose -f docker-compose.staging.yml --env-file .env.staging build
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Run database migrations (required on first run)
docker compose -f docker-compose.staging.yml --env-file .env.staging exec api uv run alembic upgrade head

# Generate SSL certificates (automatic on first run)
# SSL certs are generated automatically by cert-init service
# Domain: staging.aifp-aos.local (configurable via DOMAIN env var)
```

Staging environment features:
- Production-like configuration
- No source code bind-mounts
- Persistent PostgreSQL and Redis volumes
- Nginx reverse proxy with SSL (ports 80/443)
- Dashboard served as static build (not Vite dev server)
- Rate limiting and security headers
- Separate from development environment

**Access URLs:**
- Dashboard: `http://localhost/` (or `https://staging.aifp-aos.local`)
- API: `http://localhost/api/v1` (proxied through nginx)
- Health Check: `http://localhost/health`
- **Note**: Dashboard is NOT on port 3000 in staging (that's dev-only)

### Production Environment

```bash
# Build and start production
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

Production environment requires:
- Production SSL certificates (Let's Encrypt recommended)
- Production database credentials
- Production RPC endpoints
- Proper backup configuration
- Monitoring and alerting setup

**Access URLs:**
- Dashboard: `https://your-domain.com` (served by nginx)
- API: `https://your-domain.com/api` (proxied through nginx)
- **Note**: Dashboard is built as static files and served by nginx on port 80/443, not port 3000. API is behind nginx, not directly accessible on port 8000.

## Environment Variables

### Core Configuration
- `APP_ENV`: Environment (development, staging, production)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `VITE_API_URL`: Dashboard API base URL (build-time arg for production/staging - default: empty string for same-origin API calls)

### DeepSeek Integration
- `DEEPSEEK_API_KEY`: DeepSeek API key
- `DEEPSEEK_PRIMARY_MODEL`: Primary model (deepseek/deepseek-v4-flash)
- `DEEPSEEK_REASONING_MODEL`: Reasoning model (deepseek/deepseek-v4-pro)
- `DEEPSEEK_API_BASE`: API base URL (https://api.deepseek.com)
- `DAILY_LLM_BUDGET_USD`: Daily LLM spending limit

### Moltbook Integration
- `MOLTBOOK_BASE_URL`: Moltbook API URL
- `MOLTBOOK_AGENT_API_KEY`: Agent API key
- `MOLTBOOK_APP_KEY`: Application key
- `MOLTBOOK_AUTOPUBLISH`: Enable auto-publishing (true/false)
- `MOLTBOOK_ALLOWED_SUBMOLTS`: Allowed submolts (comma-separated)

### Payment Safety Settings
- `HUMAN_APPROVAL_THRESHOLD`: Approval threshold in USD
- `PER_TRANSACTION_LIMIT`: Per-transaction limit in USD
- `DAILY_SPENDING_LIMIT`: Daily spending limit in USD
- `PAYMENTS_NETWORK`: Network (devnet, mainnet)
- `PAYMENTS_KILL_SWITCH`: Global kill switch (true/false)
- `RECIPIENT_ALLOWLIST`: Comma-separated allowed recipient addresses

### Blockchain Configuration
- `SOLANA_PRIVATE_KEY`: Solana private key (base58)
- `EVM_PRIVATE_KEY`: EVM private key
- `SOLANA_RPC_URL`: Solana RPC endpoint
- `EVM_RPC_URL`: EVM RPC endpoint

### AiFinPay Integration
- `AIFINPAY_AGENT_SECRET`: Ed25519 secret key
- `AIFINPAY_AGENT_PUBKEY`: Ed25519 public key
- `AIFINPAY_MAX_USD`: Maximum USD per transaction
- `AIFINPAY_MCP_ENABLED`: Enable MCP integration (true/false)

## Database Migrations

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback to previous version
alembic downgrade -1

# View migration history
alembic history
```

## SSL Certificate Setup

### Development/Staging (Self-Signed)

SSL certificates are automatically generated on first `docker compose up` by the `cert-init` service:
- Uses `scripts/generate_ssl_cert.py` with Python cryptography library
- Certificates generated in `nginx/ssl/` directory
- Domain configured via `DOMAIN` environment variable (default: staging.aifp-aos.local)
- Idempotent - skips regeneration if certificates already exist

### Production (Let's Encrypt)

For production, use Let's Encrypt certificates:
```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
```

## Backup and Restore

```bash
# Backup database
make backup
# or
docker compose -f docker-compose.staging.yml exec postgres pg_dump -U aifp aifp_staging > backup.sql

# Restore database
make restore
# or
docker compose -f docker-compose.staging.yml exec -T postgres psql -U aifp aifp_staging < backup.sql
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **OpenAPI Spec**: docs/openapi.json
- **API Guide**: docs/API.md
- **Deployment Guide**: docs/DEPLOYMENT.md

## Testing

```bash
# Run all tests
docker compose -f docker-compose.dev.yml exec -T api uv run pytest tests/ -v

# Run with coverage
docker compose -f docker-compose.dev.yml exec -T api uv run pytest tests/ --cov=apps --cov-report=html

# Run specific test file
docker compose -f docker-compose.dev.yml exec -T api uv run pytest tests/test_auth.py -v
```

## Load Testing

```bash
# Run load tests
make load-test
# or
locust -f load/locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 30s
```

## Security

- **JWT Authentication**: Token-based authentication with role-based access control
- **RBAC**: Admin, Operator, and Viewer roles with appropriate permissions
- **Security Scanning**: pip-audit, bandit, and gitleaks integrated in CI
- **Payment Safety**: Kill switches, allowlists, and spending limits
- **Secrets Management**: Environment variables only, no hardcoded secrets

## Architecture

See `docs/ARCHITECTURE.md` for detailed architecture documentation.

## Known Limitations

See `docs/KNOWN_LIMITATIONS.md` for current technical debt and limitations.

## Support

For deployment issues, see `docs/DEPLOYMENT.md`.
For API documentation, see `docs/API.md`.
For known limitations, see `docs/KNOWN_LIMITATIONS.md`.
