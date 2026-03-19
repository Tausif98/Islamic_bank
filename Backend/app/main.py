"""
FastAPI Application Entry Point

Lifespan context manager handles startup/shutdown:
- startup: connect to MongoDB, Redis, Kafka (fail fast if any fails)
- shutdown: gracefully close all connections

This replaces the deprecated @app.on_event("startup") pattern.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.core.redis import connect_redis, disconnect_redis
from app.core.kafka import start_kafka_producer, stop_kafka_producer
from app.api.v1 import api_router

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Everything before 'yield' runs at startup.
    Everything after 'yield' runs at shutdown.
    Order matters: MongoDB must be ready before Beanie init.
    """
    logger.info(f"Starting {settings.app_name}...")

    await connect_to_mongo()
    await connect_redis()
    await start_kafka_producer()

    logger.info("All services connected. Application ready.")
    yield

    # Graceful shutdown
    await stop_kafka_producer()
    await disconnect_redis()
    await close_mongo_connection()
    logger.info("All connections closed. Shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Islamic Banking API — Mudarabah, Murabaha, Musharakah products",
    docs_url="/docs",           # Swagger UI
    redoc_url="/redoc",         # ReDoc UI
    lifespan=lifespan,
)

# CORS: allow frontend (React, etc.) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Load balancer / k8s liveness probe endpoint."""
    return {"status": "healthy", "app": settings.app_name}