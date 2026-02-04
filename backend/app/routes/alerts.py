"""Alerts endpoints."""

from fastapi import APIRouter, Query
from typing import Optional
from app.services.alerts_service import AlertsService

router = APIRouter()
alerts_service = AlertsService()


@router.get("/alerts")
async def get_alerts(
    limit: int = Query(default=10, ge=1, le=100),
    severity: Optional[str] = Query(default=None, pattern="^(low|medium|high|critical)$"),
):
    """
    Get recent threat alerts.
    
    Args:
        limit: Number of alerts to return (1-100)
        severity: Filter by severity level
    """
    alerts = alerts_service.get_recent_alerts(limit=limit, severity=severity)
    
    return {
        "success": True,
        "data": {
            "alerts": alerts,
            "total": len(alerts),
        },
        "message": "Alerts retrieved",
    }


@router.get("/alerts/{alert_id}")
async def get_alert_detail(alert_id: str):
    """
    Get detailed information about a specific alert.
    """
    alert = alerts_service.get_alert_by_id(alert_id)
    
    return {
        "success": True,
        "data": alert,
        "message": "Alert detail retrieved",
    }
