import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis import Redis
from apps.api.config import settings
from apps.models.base import get_db
from apps.api.routers import system

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AiFinPay AOS API...")
    yield
    logger.info("Shutting down AiFinPay AOS API...")

app = FastAPI(
    title="AiFinPay Autonomous Growth OS",
    description="Days 3-4: Growth Orchestrator & Task Engine",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router, prefix="/api/v1")

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    health = {
        "status": "ok",
        "version": "0.1.0",
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
        redis_client = Redis.from_url(settings.REDIS_URL)
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
