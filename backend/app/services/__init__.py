"""Services package."""

from app.services.alerts_service import alerts_service
from app.services.audit_service import audit_service
from app.services.canary_service import canary_service
from app.services.classifier import ClassifierService
from app.services.detection_service import detection_service
from app.services.drift_service import drift_service
from app.services.ingest_pipeline import ingestion_pipeline
from app.services.model_registry_service import model_registry_service
from app.services.notification_service import notification_service
from app.services.stats_service import stats_service

__all__ = [
    "alerts_service",
    "audit_service",
    "canary_service",
    "ClassifierService",
    "detection_service",
    "drift_service",
    "ingestion_pipeline",
    "model_registry_service",
    "notification_service",
    "stats_service",
]
