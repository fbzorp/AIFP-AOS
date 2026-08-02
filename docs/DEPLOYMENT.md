# Deployment Guide

This guide covers deploying the AiFinPay Autonomous OS to staging and production environments.

## Prerequisites

- Docker and Docker Compose installed
- A domain name (for production)
- SSL certificates (for production)
- Environment variables configured
- Python 3.12+ (for migrations and SSL generation)
- Basic Linux administration skills

### Server / VPS Requirements

**Minimum Viable Specs:**
- **RAM**: 4 GB (required for dashboard Vite build, uv dependency installation, and running all services)
- **CPU**: 2 vCPU (for concurrent container operations)
- **Storage**: 20-30 GB (for Docker images, PostgreSQL data, Redis, and logs)
- **OS**: Ubuntu 22.04 LTS or similar Linux distribution

**Recommended Specs:**
- **RAM**: 4-8 GB (for comfortable operation under load, backups, and concurrent database operations)
- **CPU**: 2-4 vCPU (for better performance during peak usage)
- **Storage**: 40+ GB (for data growth, backups, and logs)
- **OS**: Ubuntu 22.04 LTS or similar Linux distribution

**⚠️ Important Notes:**
- **1 GB / 1 vCPU servers are NOT sufficient** - image builds (dashboard `npm run build`, `uv sync`) and concurrent containers will exhaust memory
- PostgreSQL and Redis require consistent memory allocation for reliable operation
- Docker image caching and layered builds require additional disk space
- Persistent volumes for PostgreSQL and Redis will grow over time

**Resource Breakdown by Service:**
- **API**: ~500MB RAM (Python + FastAPI + dependencies)
- **Worker**: ~500MB RAM (Python + Dramatiq + tasks)
- **Dashboard**: ~1GB RAM during build, ~200MB runtime (nginx static serving)
- **PostgreSQL**: ~1GB RAM (database + queries + connections)
- **Redis**: ~200MB RAM (caching + task queue)
- **Nginx**: ~100MB RAM (reverse proxy + SSL)
- **Build overhead**: ~1GB RAM (docker build operations)

## Pre-Deployment Checklist

### 1. Domain Configuration

**Required for Production:**
- Purchase a domain name (e.g., from Namecheap, GoDaddy, Cloudflare)
- Configure DNS to point to your VPS IP address
- DNS Record Types:
  - **A Record**: `@` → `YOUR_VPS_IP`
  - **A Record**: `www` → `YOUR_VPS_IP`

**DNS Propagation:**
- DNS changes typically take 15-60 minutes to propagate
- Verify with: `nslookup your-domain.com`
- Or use online tools like `digwebinterface.com`

**Staging (Optional):**
- Can use subdomain like `staging.your-domain.com`
- Configure similarly with A records

### 2. SSL Certificates

**Option A: Let's Encrypt (Recommended for Production)**
```bash
# Install certbot on your VPS
sudo apt-get update
sudo apt-get install certbot

# Generate certificates (requires domain pointing to VPS)
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Certificate location:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

**Option B: Self-Signed (For Testing/Staging)**
```bash
# Use the provided SSL generation script
cd /path/to/AIFP-AOS
python scripts/generate_ssl_cert.py --cert-dir nginx/ssl
```

**Option C: Commercial SSL**
- Purchase from certificate authority
- Follow their installation instructions
- Place certificates in `nginx/ssl/` directory

**Automatic Renewal (Let's Encrypt):**
```bash
# Test renewal
sudo certbot renew --dry-run

# Set up auto-renewal (cron)
sudo crontab -e
# Add: 0 0,12 * * * certbot renew --quiet
```

### 3. Environment Variables Configuration

**Database Configuration:**
```bash
# Generate strong passwords
POSTGRES_USER=$(openssl rand -base64 16)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_DB=aifp_prod  # or staging database name
```

**API Keys Required:**
- **DeepSeek API**: Get from https://platform.deepseek.com/
  - `DEEPSEEK_API_KEY`: Your API key
  - `DEEPSEEK_PRIMARY_MODEL`: deepseek/deepseek-v4-flash
  - `DEEPSEEK_REASONING_MODEL`: deepseek/deepseek-v4-pro

- **Moltbook API**: Get from Moltbook developer portal
  - `MOLTBOOK_AGENT_API_KEY`: Your agent API key
  - `MOLTBOOK_APP_KEY`: Your app key

- **X (Twitter) API**: Get from X developer portal
  - `X_API_KEY`: Consumer key
  - `X_API_SECRET`: Consumer secret
  - `X_ACCESS_TOKEN`: Access token
  - `X_ACCESS_TOKEN_SECRET`: Access token secret

- **Telegram Bot**: Get from @BotFather
  - `TELEGRAM_BOT_TOKEN`: Your bot token

**Blockchain Configuration:**
```bash
# Solana Configuration
SOLANA_RPC_URL=https://api.devnet.solana.com  # or mainnet RPC
SOLANA_PRIVATE_KEY=your_base58_private_key    # Never commit this!

# EVM Configuration  
EVM_RPC_URL=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY  # or mainnet
EVM_PRIVATE_KEY=your_hex_private_key                        # Never commit this!
```

**AiFinPay Integration:**
```bash
# Generate Ed25519 keypair
AIFINPAY_AGENT_SECRET=your_base58_secret_key
AIFINPAY_AGENT_PUBKEY=your_base58_public_key
AIFINPAY_MAX_USD=0.10  # Per MCP call limit
AIFINPAY_MCP_ENABLED=true
```

**Payment Security Limits:**
```bash
DAILY_SPENDING_LIMIT=100.00         # Daily total limit in USD
PER_TRANSACTION_LIMIT=50.00         # Max per transaction in USD
HUMAN_APPROVAL_THRESHOLD=25.00     # Require approval above this amount
PAYMENTS_KILL_SWITCH=false          # Emergency stop switch
RECIPIENT_ALLOWLIST=address1,address2,address3  # Comma-separated
```

**Network Configuration:**
```bash
PAYMENTS_NETWORK=devnet  # Options: devnet, mainnet
APP_ENV=production       # Options: development, staging, production
DOMAIN=your-domain.com   # Your production domain
```

**Complete .env.production Example:**
```bash
# Application
APP_ENV=production
DOMAIN=your-domain.com
LOG_LEVEL=INFO

# Database
POSTGRES_USER=your_secure_username
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=aifp_prod
DATABASE_URL=postgresql+asyncpg://your_secure_username:your_secure_password@postgres:5432/aifp_prod

# Redis
REDIS_URL=redis://redis:6379/0

# DeepSeek AI
DEEPSEEK_API_KEY=sk-your-api-key
DEEPSEEK_PRIMARY_MODEL=deepseek/deepseek-v4-flash
DEEPSEEK_REASONING_MODEL=deepseek/deepseek-v4-pro
DEEPSEEK_API_BASE=https://api.deepseek.com
DAILY_LLM_BUDGET_USD=25.00

# Moltbook
MOLTBOOK_BASE_URL=https://www.moltbook.com
MOLTBOOK_AGENT_API_KEY=your-agent-api-key
MOLTBOOK_APP_KEY=your-app-key
MOLTBOOK_AUTOPUBLISH=false
MOLTBOOK_ALLOWED_SUBMOLTS=general,agents,introductions,aifintech

# X (Twitter)
X_API_KEY=your-consumer-key
X_API_SECRET=your-consumer-secret
X_ACCESS_TOKEN=your-access-token
X_ACCESS_TOKEN_SECRET=your-access-token-secret
X_AUTOPUBLISH=false

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token

# Blockchain
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_PRIVATE_KEY=your_base58_private_key
EVM_RPC_URL=https://base-sepolia.g.alchemy.com/v2/your-key
EVM_PRIVATE_KEY=your_hex_private_key

# X402
X402_ENABLED=true
X402_FACILITATOR_URL=https://api.aifinpay.io
PAYMENTS_NETWORK=devnet

# Payment Security
DAILY_SPENDING_LIMIT=100.00
PER_TRANSACTION_LIMIT=50.00
HUMAN_APPROVAL_THRESHOLD=25.00
RECIPIENT_ALLOWLIST=address1,address2,address3
PAYMENTS_KILL_SWITCH=false

# AiFinPay Integration
AIFP_BASE_URL=https://api.aifinpay.io
AIFINPAY_AGENT_SECRET=your_base58_secret
AIFINPAY_AGENT_PUBKEY=your_base58_public_key
AIFINPAY_MAX_USD=0.10
AIFINPAY_MCP_ENABLED=true
```

### 4. VPS Preparation

**System Requirements:**
- **Minimum**: 2GB RAM, 20GB storage, 1 CPU
- **Recommended**: 4GB RAM, 40GB storage, 2 CPUs
- **OS**: Ubuntu 22.04 LTS or similar

**Install Docker:**
```bash
# Update system
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**Firewall Configuration:**
```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

**System Optimization:**
```bash
# Increase file descriptors (for high traffic)
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Configure swap (if low RAM)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Clean Server Deployment

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/fbzorp/AIFP-AOS.git
cd AIFP-AOS
```

### Step 2: Environment Setup

```bash
# Copy environment example
cp .env.example .env.production

# Edit .env.production with your production values
nano .env.production
```

Required environment variables for production:
- `POSTGRES_USER`: PostgreSQL username (no default)
- `POSTGRES_PASSWORD`: PostgreSQL password (no default)
- `POSTGRES_DB`: PostgreSQL database name (default: aifp_prod)
- `DOMAIN`: Your production domain name
- `SOLANA_RPC_URL`: Solana RPC endpoint
- `EVM_RPC_URL`: EVM RPC endpoint
- `AIFINPAY_AGENT_SECRET`: Ed25519 secret key
- `AIFINPAY_AGENT_PUBKEY`: Ed25519 public key
- `PAYMENTS_NETWORK`: Network (devnet or mainnet)
- `DAILY_SPENDING_LIMIT`: Daily spending limit in USD
- `PER_TRANSACTION_LIMIT`: Per-transaction limit in USD
- `HUMAN_APPROVAL_THRESHOLD`: Approval threshold in USD
- `RECIPIENT_ALLOWLIST`: Comma-separated allowed addresses

### Step 3: Build and Start Services

```bash
# Build production images
docker compose -f docker-compose.prod.yml --env-file .env.production build

# Start all services
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
```

The `cert-init` service will automatically generate self-signed SSL certificates on first run. For production, replace these with Let's Encrypt certificates.

### Step 4: Run Database Migrations

```bash
# Run migrations
docker compose -f docker-compose.prod.yml --env-file .env.production exec api alembic upgrade head
```

### Step 5: Health Check

```bash
# Check service status
docker compose -f docker-compose.prod.yml --env-file .env.production ps

# Check API health
curl https://your-domain.com/health

# Check nginx status
docker compose -f docker-compose.prod.yml --env-file .env.production logs nginx
```

### Step 6: Configure Production SSL (Optional)

For production, replace self-signed certificates with Let's Encrypt:

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com

# Stop nginx container
docker compose -f docker-compose.prod.yml --env-file .env.production stop nginx

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

# Set permissions
sudo chmod 644 nginx/ssl/fullchain.pem
sudo chmod 600 nginx/ssl/privkey.pem

# Restart nginx
docker compose -f docker-compose.prod.yml --env-file .env.production start nginx
```

## Environment Configuration

## Environment Configuration

### Staging Environment

The staging environment uses Docker Compose with environment-driven configuration.

#### Environment Variables

Create a `.env.staging` file:

```bash
# Database Configuration
POSTGRES_USER=aifp
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=aifp_staging

# Domain Configuration
DOMAIN=staging.your-domain.com

# API Configuration
VITE_API_URL=https://staging.your-domain.com/api

# Payment Configuration
SOLANA_RPC_URL=https://api.devnet.solana.com
EVM_RPC_URL=https://base-sepolia.g.alchemy.com/v2/YOUR_ALCHEMY_KEY

# Secrets (generate secure ones)
AIFINPAY_AGENT_SECRET=your_generated_secret
AIFINPAY_AGENT_PUBKEY=your_generated_pubkey

# Payment Limits
DAILY_SPENDING_LIMIT=100.00
PER_TRANSACTION_LIMIT=50.00
HUMAN_APPROVAL_THRESHOLD=25.00
RECIPIENT_ALLOWLIST=
```

### SSL Certificate Setup

#### Option 1: Self-Signed Certificates (Development/Testing)

For local development or testing, generate self-signed certificates using Python:

**Linux/Mac:**
```bash
DOMAIN=staging.your-domain.com ./scripts/generate_ssl_cert.sh
```

**Windows:**
```batch
generate_ssl_cert.bat staging.your-domain.com
```

**Or directly with Python:**
```bash
python scripts/generate_ssl_cert.py staging.your-domain.com
```

This creates:
- `nginx/ssl/fullchain.pem` (certificate)
- `nginx/ssl/privkey.pem` (private key)

⚠️ **Warning**: Self-signed certificates are for development only. Never use them in production.

**Note**: The scripts use Python's cryptography library, so OpenSSL doesn't need to be installed on the host system.

#### Option 2: Let's Encrypt (Production)

For production, use Let's Encrypt to obtain real SSL certificates:

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to project directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
```

The `nginx/ssl/*.pem` files are gitignored for security, so they won't be committed to the repository.

## Nginx Configuration

The staging environment uses nginx with environment-based templating:

- **Template File**: `nginx/templates/default.conf.template`
- **Main Config**: `nginx/nginx.conf`
- **Environment Variable**: `DOMAIN` controls the server name

The nginx container automatically substitutes `${DOMAIN}` in the template file on startup.

### How It Works

1. `nginx/nginx.conf` contains the base configuration with upstreams and rate limiting
2. `nginx/templates/default.conf.template` contains server blocks with `${DOMAIN}` placeholders
3. The nginx:alpine image automatically runs `envsubst` on template files in `/etc/nginx/templates/`
4. Resulting configuration is written to `/etc/nginx/conf.d/` and included by the main config

### Starting Staging

```bash
# Build and start all services
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Start only nginx (for testing)
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d nginx
```

### Accessing Services

- **Dashboard**: `https://your-domain.com`
- **API**: `https://your-domain.com/api`
- **API Documentation**: `https://your-domain.com/docs`
- **Health Check**: `https://your-domain.com/health`

## Deployment Verification

### 1. Check Docker Compose Configuration

```bash
docker compose -f docker-compose.staging.yml config
```

This validates the compose file syntax and shows the final configuration.

### 2. Verify Nginx Configuration

```bash
# Check nginx is running
docker compose -f docker-compose.staging.yml ps nginx

# Check nginx logs
docker compose -f docker-compose.staging.yml logs nginx

# Test nginx configuration
docker compose -f docker-compose.staging.yml exec nginx nginx -t
```

### 3. Test SSL/TLS

```bash
# Test SSL certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Test HTTP to HTTPS redirect
curl -I http://your-domain.com
```

### 4. Verify API Endpoints

```bash
# Health check
curl https://your-domain.com/health

# API root
curl https://your-domain.com/api/

# API documentation
curl https://your-domain.com/docs
```

## Production Deployment Notes

### Dockerfile Usage
- **API/Worker Services**: Use `Dockerfile.prod` with `--workers` flag for production performance (no reload, non-root user)
- **Dashboard Service**: Uses `Dockerfile` with multi-stage build (Node build + nginx static serving)
- **cert-init Service**: Uses `Dockerfile.prod` for simplicity (one-shot service, worker optimization not needed)
- **Development**: Uses `Dockerfile.dev` with `--reload` for hot reload during development

### Database URL Configuration
- **Docker Compose**: DATABASE_URL uses docker network hostname (e.g., `postgres:5432`)
- **Local Testing**: DATABASE_URL should use localhost (e.g., `localhost:5432`) when running tests directly on host
- **Switching**: Modify .env DATABASE_URL between docker hostname and localhost based on execution context

## Production Deployment Checklist

- [ ] Set secure database passwords
- [ ] Configure production domain in `DOMAIN` environment variable
- [ ] Obtain SSL certificates from Let's Encrypt
- [ ] Set up firewall rules (only allow ports 80, 443)
- [ ] Configure backup automation
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Review and adjust payment limits
- [ ] Enable payment kill switch if needed
- [ ] Configure proper logging
- [ ] Set up error tracking (Sentry, etc.)

## OpenAPI Documentation

The API documentation is automatically generated and must be kept in sync with code changes:

### Update OpenAPI Spec

```bash
# Export the latest OpenAPI specification
python scripts/export_openapi.py

# Commit the changes
git add docs/openapi.json
git commit -m "Update OpenAPI specification"
```

### Check OpenAPI Freshness

```bash
# Check if the spec is up to date (used in CI)
python scripts/export_openapi.py --check
```

The CI pipeline automatically checks if `docs/openapi.json` is up to date. If you add or modify API routes, you must regenerate the spec before the PR can be merged.

## Security Considerations

### SSL Certificates

- ✅ SSL certificate files (`nginx/ssl/*.pem`, `*.key`, `*.crt`) are gitignored
- ✅ Only `.gitkeep` is committed to preserve the directory structure
- ✅ Use Let's Encrypt for production certificates
- ❌ Never commit real SSL certificates to the repository

### Environment Variables

- ✅ `.env` files are gitignored
- ✅ Use environment-specific files (`.env.staging`, `.env.production`)
- ✅ Never commit secrets or API keys
- ✅ Use secret management services in production (AWS Secrets Manager, etc.)

### Payment Security

- ✅ Payment kill switch is disabled by default (`PAYMENTS_KILL_SWITCH=false`)
- ✅ Per-transaction and daily spending limits are enforced
- ✅ Human approval threshold is configurable
- ✅ Recipient allowlist is available for additional security
- ✅ All payment endpoints require authentication and proper RBAC

## Troubleshooting

### Nginx Won't Start

1. Check if SSL certificates exist:
   ```bash
   ls -la nginx/ssl/
   ```

2. Check nginx logs:
   ```bash
   docker compose -f docker-compose.staging.yml logs nginx
   ```

3. Test nginx configuration:
   ```bash
   docker compose -f docker-compose.staging.yml exec nginx nginx -t
   ```

### SSL Certificate Errors

1. Verify certificate files exist and are readable
2. Check certificate validity:
   ```bash
   openssl x509 -in nginx/ssl/fullchain.pem -text -noout
   ```
3. Ensure the DOMAIN variable matches the certificate's Common Name

### OpenAPI Check Fails in CI

If the OpenAPI check fails:
1. Regenerate the spec: `python scripts/export_openapi.py`
2. Commit the updated `docs/openapi.json`
3. Push the changes

## Backup and Restore

### Database Backups

Automated backups are configured via the backup automation system. Manual backups:

```bash
# Create backup
docker compose -f docker-compose.staging.yml exec postgres pg_dump -U aifp aifp_staging > backup.sql

# Restore backup
docker compose -f docker-compose.staging.yml exec -T postgres psql -U aifp aifp_staging < backup.sql
```

### Configuration Backups

Important configuration files to back up:
- `.env.staging` (environment variables)
- `nginx/ssl/*.pem` (SSL certificates)
- `alembic/versions/` (database migrations)

## Monitoring

### Health Checks

- API health: `https://your-domain.com/health`
- Container status: `docker compose -f docker-compose.staging.yml ps`
- Service logs: `docker compose -f docker-compose.staging.yml logs -f`

### Logs

- API logs: `docker compose -f docker-compose.staging.yml logs api`
- Nginx logs: `docker compose -f docker-compose.staging.yml logs nginx`
- Worker logs: `docker compose -f docker-compose.staging.yml logs worker`

### Monitoring Integration

For production monitoring, integrate with Prometheus and Grafana:

```bash
# Add Prometheus to docker-compose.prod.yml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

# Add Grafana to docker-compose.prod.yml
grafana:
  image: grafana/grafana:latest
  ports:
    - "3001:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=your_secure_password
```

Monitor metrics:
- API response times
- Payment transaction success rates
- Worker task queue depth
- Database connection pool usage
- Nginx request rates

## VPS Restart Resume Behavior

### Automatic Restart Configuration

All long-running services in `docker-compose.prod.yml` and `docker-compose.staging.yml` are configured with `restart: unless-stopped` to ensure they automatically resume after a VPS reboot:

- `postgres`: `restart: unless-stopped`
- `redis`: `restart: unless-stopped`
- `api`: `restart: unless-stopped`
- `worker`: `restart: unless-stopped`
- `dashboard`: `restart: unless-stopped`
- `nginx`: `restart: unless-stopped`

The `cert-init` service has `restart: "no"` as it is a one-shot initialization service that should only run once to generate SSL certificates.

### How It Works

When the VPS reboots:
1. Docker daemon starts automatically (via systemd)
2. Docker Compose automatically restarts all services with `restart: unless-stopped`
3. Services start in dependency order (postgres → redis → api/worker → dashboard → nginx)
4. Nginx waits for API to be healthy before starting
5. Worker resumes processing any pending tasks from Redis queue

### Verification

To verify reboot-resume behavior:

```bash
# Check current service status
docker compose -f docker-compose.prod.yml ps

# Simulate reboot (or wait for actual reboot)
sudo reboot

# After reboot, check services are back up
docker compose -f docker-compose.prod.yml ps

# Verify API health
curl https://your-domain.com/health

# Check worker is processing tasks
docker compose -f docker-compose.prod.yml logs worker | tail -20
```

Expected output after reboot:
```
NAME              STATUS              PORTS
postgres          running (healthy)   5432/tcp
redis             running (healthy)   6379/tcp
api               running (healthy)   8000/tcp
worker            running             -
dashboard         running             80/tcp
nginx             running             80/tcp, 443/tcp
```

### Manual Restart

If services don't automatically restart:

```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# Start specific service
docker compose -f docker-compose.prod.yml up -d api

# Check service logs
docker compose -f docker-compose.prod.yml logs -f api
```

## Performance Optimization

### Nginx Caching

Static files are cached for 1 hour by default. Adjust in `nginx/templates/default.conf.template` if needed.

### Rate Limiting

Default rate limits:
- API: 10 requests/second with burst of 20
- Dashboard: 20 requests/second with burst of 30

Adjust in `nginx/nginx.conf` if needed.

## Support

For deployment issues:
1. Check the logs: `docker compose -f docker-compose.staging.yml logs`
2. Verify configuration: `docker compose -f docker-compose.staging.yml config`
3. Review this documentation
4. Check the main project documentation in `docs/`
