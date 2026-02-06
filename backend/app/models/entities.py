"""Persistent entities for enterprise-grade operations."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class UserRole(str, Enum):
    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"


class AlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AlertStatus(str, Enum):
    new = "new"
    triaged = "triaged"
    investigating = "investigating"
    resolved = "resolved"
    false_positive = "false_positive"


class QueueStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"
    dead_letter = "dead_letter"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    external_subject: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    auth_provider: Mapped[str] = mapped_column(String(40), default="local", index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.viewer.value, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    version: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    path: Mapped[str] = mapped_column(String(512))
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClassificationEvent(Base):
    __tablename__ = "classification_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(80), default="api")
    source_ip: Mapped[str] = mapped_column(String(120), default="unknown", index=True)
    destination_ip: Mapped[str] = mapped_column(String(120), default="unknown", index=True)
    model_version: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    prediction: Mapped[str] = mapped_column(String(200), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    is_threat: Mapped[bool] = mapped_column(Boolean, index=True)
    features: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("classification_events.id"), nullable=True)
    dedup_key: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(200), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    source_ip: Mapped[str] = mapped_column(String(120), default="unknown", index=True)
    destination_ip: Mapped[str] = mapped_column(String(120), default="unknown", index=True)
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default=AlertStatus.new.value, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(150), index=True)
    target_type: Mapped[str] = mapped_column(String(120), index=True)
    target_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class IngestionMessage(Base):
    __tablename__ = "ingestion_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(120), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default=QueueStatus.queued.value, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelEvaluationEvent(Base):
    __tablename__ = "model_evaluation_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(80), default="api", index=True)
    production_model_version: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    canary_model_version: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    production_prediction: Mapped[str] = mapped_column(String(200), index=True)
    canary_prediction: Mapped[str] = mapped_column(String(200), index=True)
    production_confidence: Mapped[float] = mapped_column(Float)
    canary_confidence: Mapped[float] = mapped_column(Float)
    diverged: Mapped[bool] = mapped_column(Boolean, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
