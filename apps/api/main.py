from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AiFinPay AOS API...")
    yield
    logger.info("Shutting down AiFinPay AOS API...")


app = FastAPI(
    title="AiFinPay Autonomous Growth OS",
    description="AI-powered marketing and growth automation system",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root():
    return {
        "message": "AiFinPay Autonomous Growth OS API",
        "docs": "/docs",
        "version": "0.1.0"
    }
