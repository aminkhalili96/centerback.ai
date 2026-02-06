"""Real-time ingestion routes."""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.entities import IngestionMessage, QueueStatus, User, UserRole
from app.services.audit_service import audit_service

router = APIRouter()


class FlowPayload(BaseModel):
    flow_id: str | None = None
    source_ip: str = "unknown"
    destination_ip: str = "unknown"
    features: list[float] = Field(min_length=78, max_length=78)
    metadata: dict | None = None


class IngestRequest(BaseModel):
    source: str = Field(min_length=2, max_length=120)
    flows: list[FlowPayload] = Field(min_length=1, max_length=1000)


def _flow_idempotency_key(source: str, flow: FlowPayload) -> str:
    if flow.flow_id:
        return f"{source}:{flow.flow_id}"
    payload = {
        "source_ip": flow.source_ip,
        "destination_ip": flow.destination_ip,
        "features": flow.features,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{source}:{digest}"


@router.post("/ingest/flows", response_model=dict, dependencies=[Depends(require_roles(UserRole.analyst.value, UserRole.admin.value))])
async def ingest_flows(
    payload: IngestRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    queue_depth = db.scalar(
        select(func.count(IngestionMessage.id)).where(
            IngestionMessage.status.in_(
                [QueueStatus.queued.value, QueueStatus.processing.value, QueueStatus.failed.value]
            )
        )
    ) or 0
    if queue_depth >= settings.ingest_max_queue_depth:
        raise HTTPException(status_code=429, detail="Ingestion backpressure active: queue depth exceeded")
    if queue_depth + len(payload.flows) > settings.ingest_max_queue_depth:
        raise HTTPException(status_code=429, detail="Ingestion request exceeds available queue capacity")

    cutoff = datetime.utcnow() - timedelta(minutes=settings.ingest_idempotency_window_minutes)
    existing_keys = set(
        db.execute(
            select(IngestionMessage.idempotency_key)
            .where(IngestionMessage.source == payload.source)
            .where(IngestionMessage.created_at >= cutoff)
            .where(IngestionMessage.idempotency_key.is_not(None))
        ).scalars().all()
    )

    queued = 0
    duplicates_skipped = 0
    for flow in payload.flows:
        idempotency_key = _flow_idempotency_key(payload.source, flow)
        if idempotency_key in existing_keys:
            duplicates_skipped += 1
            continue

        db.add(
            IngestionMessage(
                source=payload.source,
                idempotency_key=idempotency_key,
                payload={
                    "flow_id": flow.flow_id,
                    "source": payload.source,
                    "source_ip": flow.source_ip,
                    "destination_ip": flow.destination_ip,
                    "features": flow.features,
                    "metadata": flow.metadata or {},
                },
                status=QueueStatus.queued.value,
                attempts=0,
            )
        )
        existing_keys.add(idempotency_key)
        queued += 1

    audit_service.log(
        db=db,
        action="ingest.enqueue",
        target_type="ingestion_batch",
        target_id=None,
        actor=current_user,
        details={
            "source": payload.source,
            "queued": queued,
            "duplicates_skipped": duplicates_skipped,
            "queue_depth_before": queue_depth,
        },
    )
    db.commit()

    return {
        "success": True,
        "data": {
            "queued": queued,
            "duplicates_skipped": duplicates_skipped,
            "source": payload.source,
            "queue_depth": queue_depth + queued,
        },
        "message": f"Queued {queued} flows for processing",
    }


@router.get("/ingest/queue", response_model=dict, dependencies=[Depends(require_roles(UserRole.analyst.value, UserRole.admin.value))])
async def ingest_queue_summary(db: Session = Depends(get_db)):
    rows = db.execute(
        select(IngestionMessage.status, func.count(IngestionMessage.id)).group_by(IngestionMessage.status)
    ).all()
    summary = {status: count for status, count in rows}
    return {
        "success": True,
        "data": summary,
        "message": "Queue summary retrieved",
    }


@router.get("/ingest/dlq", response_model=dict, dependencies=[Depends(require_roles(UserRole.admin.value))])
async def list_dead_letters(db: Session = Depends(get_db), limit: int = Query(default=50, ge=1, le=500)):
    messages = db.execute(
        select(IngestionMessage)
        .where(IngestionMessage.status == QueueStatus.dead_letter.value)
        .order_by(IngestionMessage.updated_at.desc())
        .limit(limit)
    ).scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": m.id,
                "source": m.source,
                "attempts": m.attempts,
                "last_error": m.last_error,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            }
            for m in messages
        ],
        "message": "Dead-letter queue retrieved",
    }


@router.post("/ingest/retry/{message_id}", response_model=dict, dependencies=[Depends(require_roles(UserRole.admin.value))])
async def retry_dead_letter(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    message = db.get(IngestionMessage, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Ingestion message not found")

    message.status = QueueStatus.queued.value
    message.last_error = None
    message.attempts = 0
    audit_service.log(
        db=db,
        action="ingest.retry",
        target_type="ingestion_message",
        target_id=message_id,
        actor=current_user,
        details={"source": message.source},
    )
    db.commit()

    return {
        "success": True,
        "data": {"id": message.id, "status": message.status},
        "message": "Message re-queued",
    }
