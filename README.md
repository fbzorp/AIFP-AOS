# AiFinPay Autonomous Growth OS (AOS)

AI-powered marketing and growth automation system with 9 specialized agents, integrating Google ADK, DeepSeek, Moltbook, and AiFinPay MCP/x402 payments.

## Tech Stack

### Backend
- **Python 3.11+** with Google ADK
- **FastAPI** for REST API
- **LiteLLM** for DeepSeek integration via Google ADK
- **PostgreSQL** (Docker) for persistent data
- **Redis** (Docker) for caching
- **Dramatiq** for async task queue
- **Alembic** for database migrations

### Frontend
- **React 18+** with TypeScript
- **Vite** for fast development
- **TailwindCSS** for styling
- **React Router** for navigation
- **TanStack Query** for API state management

### Infrastructure
- **Docker Compose** for local services
- **GitHub Actions** for CI/CD

## Project Structure

```
AIFP-AOS/
├── apps/
│   ├── api/          # FastAPI backend
│   ├── agents/       # AI agent implementations
│   ├── dashboard/    # React frontend
│   └── workers/      # Dramatiq background tasks
├── tests/            # Test suite
├── deploy/           # Deployment configurations
├── .github/          # GitHub Actions workflows
├── pyproject.toml    # Python dependencies
├── docker-compose.dev.yml
└── .env.example      # Environment variables template
```

## Quick Start

### Prerequisites

- **Docker & Docker Compose** installed
- **Python 3.11+** installed
- **Node.js 20+** installed

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/fbzorp/AIFP-AOS.git
   cd AIFP-AOS
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start the development stack**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

4. **Install Python dependencies** (if not using Docker)
   ```bash
   pip install -e ".[dev]"
   ```

5. **Install frontend dependencies** (if not using Docker)
   ```bash
   cd apps/dashboard
   npm install
   ```

### Access the Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:3000

## Development Commands

### Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Restart specific service
docker-compose -f docker-compose.dev.yml restart api
```

### Backend (without Docker)

```bash
# Install dependencies
pip install -e ".[dev]"

# Run API server
uvicorn apps.api.main:app --reload --port 8000

# Run worker
dramatiq apps.workers.tasks --watch apps

# Run tests
pytest tests/ -v

# Run migrations
alembic upgrade head
```

### Frontend (without Docker)

```bash
cd apps/dashboard

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint
```

## Environment Variables

See `.env.example` for all available variables. Key variables include:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `DEEPSEEK_API_KEY`: DeepSeek API key for AI agents
- `AIFP_API_KEY`: AiFinPay SDK API key
- `X_API_KEY`, `TELEGRAM_BOT_TOKEN`: Social media API keys
- `SOLANA_PRIVATE_KEY`, `EVM_PRIVATE_KEY`: Blockchain private keys

## Daily Workflow

1. Pull latest changes: `git pull origin main`
2. Start stack: `docker-compose -f docker-compose.dev.yml up -d`
3. Develop and test
4. Run tests: `docker-compose -f docker-compose.dev.yml exec api pytest tests/ -v`
5. Commit changes: `git add . && git commit -m "feat: description"`
6. Push to GitHub: `git push origin main`

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/agents/test_growth_orchestrator.py -v

# Run with coverage
pytest tests/ --cov=apps --cov-report=html
```

## Security Notes

- **NEVER commit `.env` file to Git**
- Store private keys securely (use hardware wallets for production)
- All publications require manual approval by default
- Spending limits and kill switches are implemented
- Seed phrases and private keys never stored in plaintext

## License

Proprietary - AiFinPay

## Support

For issues and questions, refer to the project documentation or contact the development team.
