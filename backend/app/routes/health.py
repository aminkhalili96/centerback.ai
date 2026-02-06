"""Health check endpoint."""

from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.db import db_session
from app.services.ingest_pipeline import ingestion_pipeline
from ml.inference import inference

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    db_ok = True
    try:
        with db_session() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "success": True,
        "data": {
            "status": "healthy" if db_ok else "degraded",
            "service": "centerback-api",
            "database": "ok" if db_ok else "error",
            "model_loaded": inference.is_loaded(),
            "model_version": inference.get_model_version() if inference.is_loaded() else None,
            "auth_required": settings.auth_enforced,
            "auth_mode": settings.auth_mode,
            "ingest_pipeline_enabled": settings.ingest_pipeline_enabled,
            "ingest_pipeline_running": ingestion_pipeline.is_running if settings.ingest_pipeline_enabled else False,
        },
        "message": "Service is running",
    }
