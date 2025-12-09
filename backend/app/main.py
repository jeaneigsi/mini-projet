"""
Main FastAPI Application for Maintenance 4.0 Platform.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from .config import settings
from .database import engine, SessionLocal
from .api.routes import router
from .schemas.schemas import HealthResponse
from .services.rule_engine import rule_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Background scheduler
scheduler = BackgroundScheduler()


def run_rule_engine():
    """Background task to run the rule engine."""
    try:
        rule_engine.evaluate_all_policies()
    except Exception as e:
        logger.error(f"Rule engine error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Maintenance 4.0 Backend...")
    
    # Start scheduler
    scheduler.add_job(
        run_rule_engine,
        'interval',
        seconds=settings.rule_engine_interval,
        id='rule_engine',
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Rule engine scheduled every {settings.rule_engine_interval} seconds")
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    logger.info("Maintenance 4.0 Backend stopped")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API pour la plateforme de Maintenance 4.0 multi-sites",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    # Check database
    db_status = "healthy"
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {e}"
    
    # Check Elasticsearch
    from .elasticsearch_client import es_client
    es_status = "healthy" if es_client.client and es_client.client.ping() else "unhealthy"
    
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        database=db_status,
        elasticsearch=es_status
    )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }
