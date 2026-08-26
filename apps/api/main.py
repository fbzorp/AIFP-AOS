import logging
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from redis import Redis
import prometheus_client as prom
from apps.api.config import settings as config_settings
from apps.models.base import get_db
from apps.api.routers import system, approvals
from apps.api.routers import settings as settings_router
from apps.api.routers.marketing import router as marketing_router
from apps.api.auth import create_access_token, create_test_token
from apps.core.observability import setup_logging, RequestIDMiddleware, init_tracing
from apps.core.audit.service import record_event_async

# Configure structured logging
setup_logging(config_settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AiFinPay AOS API...")

    # Production configuration validation
    if config_settings.APP_ENV == "production":
        errors = config_settings.validate_production_startup()
        if errors:
            error_message = f"Production configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.critical(error_message)
            # Try to record audit event before failing
            try:
                engine = create_async_engine(config_settings.DATABASE_URL)
                async_session = async_sessionmaker(engine, expire_on_commit=False)
                async with async_session() as session:
                    await record_event_async(
                        session,
                        agent_name="system",
                        event_type="config_validation_failed",
                        message=f"Production startup failed: {error_message}",
                        metadata={"errors": errors, "env": "production"}
                    )
                    await session.commit()
            except Exception as audit_error:
                logger.error(f"Failed to record audit event for config validation failure: {audit_error}")
            # Fail closed - do not start with invalid production config
            raise ValueError(error_message)

    yield
    logger.info("Shutting down AiFinPay AOS API...")

app = FastAPI(
    title="AiFinPay Autonomous Growth OS",
    description="AiFinPay Autonomous OS API - Content approvals, MCP integration, and system health monitoring with JWT-based authentication and role-based access control",
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
            "name": "Settings",
            "description": "System settings and credential management (admin only)"
        },
        {
            "name": "Marketing",
            "description": "Marketing activity and evidence registry"
        },
        {
            "name": "Alerts",
            "description": "Alertmanager webhook integration"
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

# Prometheus metrics
http_requests = prom.Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
api_up = prom.Gauge('api_up', 'API status')

@app.middleware("http")
async def track_requests(request, call_next):
    http_requests.labels(method=request.method, endpoint=request.url.path).inc()
    return await call_next(request)

app.include_router(system.router, prefix="/api/v1", tags=["System"])
app.include_router(approvals.router, prefix="/api/v1", tags=["Approvals"])
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

@app.get("/api/v1/dashboard/token")
async def get_dashboard_token():
    """Generate a JWT token for dashboard authentication."""
    return {
        "token": create_test_token("founder_admin")
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
