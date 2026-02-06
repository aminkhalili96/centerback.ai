"""Integration management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.entities import User, UserRole
from app.services.audit_service import audit_service
from app.services.notification_service import notification_service

router = APIRouter()


class NotificationTestPayload(BaseModel):
    type: str = Field(default="DDoS", min_length=2, max_length=120)
    severity: str = Field(default="high", pattern="^(low|medium|high|critical)$")
    source_ip: str = "10.0.0.1"
    destination_ip: str = "10.0.0.2"
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)


@router.get(
    "/integrations/status",
    response_model=dict,
    dependencies=[Depends(require_roles(UserRole.admin.value, UserRole.analyst.value))],
)
async def get_integration_status():
    return {
        "success": True,
        "data": notification_service.status(),
        "message": "Integration status retrieved",
    }


@router.post("/integrations/notify/test", response_model=dict, dependencies=[Depends(require_roles(UserRole.admin.value))])
async def test_notification(
    payload: NotificationTestPayload,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    notification_service.notify_alert(
        {
            "id": "test-alert",
            "event_id": "test-event",
            "type": payload.type,
            "severity": payload.severity,
            "source_ip": payload.source_ip,
            "destination_ip": payload.destination_ip,
            "confidence": payload.confidence,
            "status": "new",
            "source": "api.integrations.notify.test",
        }
    )
    audit_service.log(
        db=db,
        action="integrations.notify_test",
        target_type="integration",
        target_id=None,
        actor=current_user,
        details={"type": payload.type, "severity": payload.severity},
    )
    db.commit()
    return {
        "success": True,
        "data": {"delivered_async": True, "channels": notification_service.status()},
        "message": "Notification test enqueued",
    }
