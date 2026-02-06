"""Persistent alerts service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import Alert, AlertStatus


class AlertsService:
    """DB-backed alert retrieval and lifecycle updates."""
    _allowed_transitions = {
        AlertStatus.new.value: {
            AlertStatus.triaged.value,
            AlertStatus.investigating.value,
            AlertStatus.resolved.value,
            AlertStatus.false_positive.value,
        },
        AlertStatus.triaged.value: {
            AlertStatus.investigating.value,
            AlertStatus.resolved.value,
            AlertStatus.false_positive.value,
        },
        AlertStatus.investigating.value: {
            AlertStatus.resolved.value,
            AlertStatus.false_positive.value,
        },
        AlertStatus.resolved.value: {
            AlertStatus.triaged.value,
        },
        AlertStatus.false_positive.value: {
            AlertStatus.triaged.value,
        },
    }

    def get_recent_alerts(self, db: Session, limit: int = 10, severity: str | None = None) -> list[dict[str, Any]]:
        query = select(Alert)
        if severity:
            query = query.where(Alert.severity == severity)
        rows = db.execute(query.order_by(desc(Alert.created_at)).limit(limit)).scalars().all()
        return [self._serialize(a) for a in rows]

    def get_alert_by_id(self, db: Session, alert_id: str) -> dict[str, Any] | None:
        alert = db.get(Alert, alert_id)
        return self._serialize(alert) if alert else None

    def update_status(self, db: Session, alert_id: str, status: str) -> dict[str, Any] | None:
        if status not in {s.value for s in AlertStatus}:
            raise ValueError("Invalid alert status")
        alert = db.get(Alert, alert_id)
        if alert is None:
            return None
        if status == alert.status:
            return self._serialize(alert)

        allowed = self._allowed_transitions.get(alert.status, set())
        if status not in allowed:
            raise ValueError(f"Invalid transition from '{alert.status}' to '{status}'")
        alert.status = status
        alert.updated_at = datetime.utcnow()
        db.flush()
        return self._serialize(alert)

    @staticmethod
    def _serialize(alert: Alert) -> dict[str, Any]:
        return {
            "id": alert.id,
            "type": alert.type,
            "severity": alert.severity,
            "source_ip": alert.source_ip,
            "destination_ip": alert.destination_ip,
            "confidence": alert.confidence,
            "timestamp": alert.created_at.isoformat() if alert.created_at else None,
            "status": alert.status,
            "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
        }


alerts_service = AlertsService()
