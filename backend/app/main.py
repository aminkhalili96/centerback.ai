"""
CenterBack.AI - FastAPI Backend
AI-Powered Network Intrusion Detection System
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routes import health, classify, stats, alerts, model, dataset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting CenterBack.AI Backend...")
    logger.info("Loading ML model...")
    # Model loading will be done in services
    yield
    # Shutdown
    logger.info("Shutting down CenterBack.AI Backend...")


# Create FastAPI app
app = FastAPI(
    title="CenterBack.AI",
    description="AI-Powered Network Intrusion Detection System API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(classify.router, prefix="/api", tags=["Classification"])
app.include_router(stats.router, prefix="/api", tags=["Statistics"])
app.include_router(alerts.router, prefix="/api", tags=["Alerts"])
app.include_router(model.router, prefix="/api", tags=["Model"])
app.include_router(dataset.router, prefix="/api", tags=["Dataset"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "CenterBack.AI",
        "description": "AI-Powered Network Intrusion Detection System",
        "version": "0.1.0",
        "docs": "/docs",
    }
