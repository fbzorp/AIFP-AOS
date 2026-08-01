# Deployment Guide

This guide covers deploying the AiFinPay Autonomous OS to staging and production environments.

## Prerequisites

- Docker and Docker Compose installed
- A domain name (for production)
- SSL certificates (for production)
- Environment variables configured

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
