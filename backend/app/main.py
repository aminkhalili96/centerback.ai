"""
CenterBack.AI - FastAPI Backend
Enterprise transition runtime.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.config import settings
from app.db import init_db
from app.middleware.rate_limit import enforce_rate_limit
from app.observability import metrics_middleware, metrics_response
from app.routes import alerts, auth, classify, dataset, health, ingest, integrations, model, scim, stats
from app.services.canary_service import canary_service
from app.services.ingest_pipeline import ingestion_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    logger.info("Starting CenterBack.AI backend")
    init_db()
    canary_service.configure_from_settings()
    if settings.ingest_pipeline_enabled:
        ingestion_pipeline.start()
    yield
    logger.info("Stopping CenterBack.AI backend")
    if settings.ingest_pipeline_enabled:
        await ingestion_pipeline.stop()


app = FastAPI(
    title="CenterBack.AI",
    description="AI-Powered Network Intrusion Detection System API",
    version="0.2.0",
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": exc.errors(),
            "error": "Validation error",
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": "Internal server error",
        },
    )


cors_allow_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
    if origin.strip()
]
if not cors_allow_origins:
    cors_allow_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_origin_regex=os.getenv("CORS_ALLOW_ORIGIN_REGEX", r"https://.*\.vercel\.app"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(metrics_middleware)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    enforce_rate_limit(request)
    return await call_next(request)


@app.middleware("http")
async def request_size_middleware(request: Request, call_next):
    exempt_paths = {"/health", "/metrics", "/api/classify/batch"}
    if request.url.path not in exempt_paths:
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit():
            if int(content_length) > settings.max_request_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "success": False,
                        "data": None,
                        "error": f"Request too large (max {settings.max_request_bytes} bytes)",
                    },
                )
    return await call_next(request)


app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(classify.router, prefix="/api", tags=["Classification"])
app.include_router(stats.router, prefix="/api", tags=["Statistics"])
app.include_router(alerts.router, prefix="/api", tags=["Alerts"])
app.include_router(model.router, prefix="/api", tags=["Model"])
app.include_router(dataset.router, prefix="/api", tags=["Dataset"])
app.include_router(ingest.router, prefix="/api", tags=["Ingestion"])
app.include_router(integrations.router, prefix="/api", tags=["Integrations"])
app.include_router(scim.router, prefix="/api", tags=["SCIM"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "success": True,
        "data": {
            "name": "CenterBack.AI",
            "description": "AI-Powered Network Intrusion Detection System",
            "version": "0.2.0",
            "docs": "/docs",
            "metrics": "/metrics",
        },
        "message": "Service info retrieved",
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return metrics_response()
