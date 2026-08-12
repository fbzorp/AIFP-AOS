import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis import Redis
from apps.api.config import settings as config_settings
from apps.models.base import get_db
from apps.api.routers import system, approvals, payments
from apps.api.routers import settings as settings_router
from apps.api.routers.marketing import router as marketing_router
from apps.api.auth import create_access_token, create_test_token
from apps.core.observability import setup_logging, RequestIDMiddleware, init_tracing

# Configure structured logging
setup_logging(config_settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AiFinPay AOS API...")
    yield
    logger.info("Shutting down AiFinPay AOS API...")

app = FastAPI(
    title="AiFinPay Autonomous Growth OS",
    description="AiFinPay Autonomous OS API - Payment processing, content approvals, MCP/x402 integration, and system health monitoring with JWT-based authentication and role-based access control",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "System",
            "description": "System health checks and API information"
        },
        {
            "name": "Approvals",
            "description": "Content approval workflow, engagement proposals, and calendar management"
        },
        {
            "name": "Payments",
            "description": "Payment processing, approval workflows, and transaction execution"
        },
        {
            "name": "Settings",
            "description": "System settings and credential management (admin only)"
        },
        {
            "name": "Marketing",
            "description": "Marketing activity and evidence registry"
        }
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenTelemetry tracing with safe fallbacks
init_tracing(app)

# Add request ID middleware for tracing
app.add_middleware(RequestIDMiddleware)

app.include_router(system.router, prefix="/api/v1", tags=["System"])
app.include_router(approvals.router, prefix="/api/v1", tags=["Approvals"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(settings_router.router, prefix="/api/v1", tags=["Settings"])
app.include_router(marketing_router, prefix="/api/v1", tags=["Marketing"])

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    health = {
        "status": "ok",
        "version": "1.0.0",
        "dependencies": {
            "postgres": "unknown",
            "redis": "unknown"
        }
    }
    
    # Check Postgres
    try:
        await db.execute(select(1))
        health["dependencies"]["postgres"] = "healthy"
    except Exception as e:
        logger.error(f"Postgres health check failed: {e}")
        health["dependencies"]["postgres"] = "unhealthy"
        health["status"] = "degraded"

    # Check Redis
    try:
        redis_client = Redis.from_url(config_settings.REDIS_URL)
        if redis_client.ping():
            health["dependencies"]["redis"] = "healthy"
        else:
            health["dependencies"]["redis"] = "unhealthy"
            health["status"] = "degraded"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health["dependencies"]["redis"] = "unhealthy"
        health["status"] = "degraded"

    return health

@app.get("/")
async def root():
    return {
        "message": "AiFinPay Autonomous Growth OS API",
        "docs": "/docs",
        "health": "/health"
    }
