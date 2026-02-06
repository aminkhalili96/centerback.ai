"""Alerts endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.entities import AlertStatus, User, UserRole
from app.services.alerts_service import alerts_service
from app.services.audit_service import audit_service

router = APIRouter()


class AlertStatusUpdate(BaseModel):
    status: str = Field(pattern="^(new|triaged|investigating|resolved|false_positive)$")


@router.get("/alerts", dependencies=[Depends(require_roles(UserRole.viewer.value, UserRole.analyst.value, UserRole.admin.value))])
async def get_alerts(
    limit: int = Query(default=10, ge=1, le=100),
    severity: str | None = Query(default=None, pattern="^(low|medium|high|critical)$"),
    db: Session = Depends(get_db),
):
    """
    Get recent threat alerts.
    
    Args:
        limit: Number of alerts to return (1-100)
        severity: Filter by severity level
    """
    alerts = alerts_service.get_recent_alerts(db=db, limit=limit, severity=severity)
    
    return {
        "success": True,
        "data": {
            "alerts": alerts,
            "total": len(alerts),
        },
        "message": "Alerts retrieved",
    }


@router.get("/alerts/{alert_id}", dependencies=[Depends(require_roles(UserRole.viewer.value, UserRole.analyst.value, UserRole.admin.value))])
async def get_alert_detail(alert_id: str, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific alert.
    """
    alert = alerts_service.get_alert_by_id(db=db, alert_id=alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "success": True,
        "data": alert,
        "message": "Alert detail retrieved",
    }


@router.patch(
    "/alerts/{alert_id}/status",
    response_model=dict,
    dependencies=[Depends(require_roles(UserRole.analyst.value, UserRole.admin.value))],
)
async def update_alert_status(
    alert_id: str,
    payload: AlertStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    if payload.status not in {s.value for s in AlertStatus}:
        raise HTTPException(status_code=400, detail="Invalid alert status")

    try:
        alert = alerts_service.update_status(db=db, alert_id=alert_id, status=payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    audit_service.log(
        db=db,
        action="alerts.update_status",
        target_type="alert",
        target_id=alert_id,
        actor=current_user,
        details={"status": payload.status},
    )
    db.commit()

    return {
        "success": True,
        "data": alert,
        "message": "Alert status updated",
    }
