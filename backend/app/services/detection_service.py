"""Detection persistence and alerting policy."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.entities import Alert, AlertSeverity, AlertStatus, ClassificationEvent, ModelEvaluationEvent
from app.services.canary_service import canary_service
from app.services.notification_service import notification_service


class DetectionService:
    """Persists classification events and derives alerts."""

    @staticmethod
    def _severity(confidence: float) -> str:
        if confidence >= 0.95:
            return AlertSeverity.critical.value
        if confidence >= 0.90:
            return AlertSeverity.high.value
        if confidence >= 0.80:
            return AlertSeverity.medium.value
        return AlertSeverity.low.value

    def record_classification(
        self,
        db: Session,
        prediction: str,
        confidence: float,
        is_threat: bool,
        source: str,
        source_ip: str = "unknown",
        destination_ip: str = "unknown",
        features: list[float] | None = None,
        model_version: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> tuple[ClassificationEvent, Alert | None]:
        event = ClassificationEvent(
            source=source,
            source_ip=source_ip,
            destination_ip=destination_ip,
            prediction=prediction,
            confidence=confidence,
            is_threat=is_threat,
            features=features,
            model_version=model_version,
            extra_metadata=extra_metadata,
        )
        db.add(event)
        db.flush()

        if features is not None and canary_service.should_sample():
            canary_result = canary_service.evaluate(features)
            if canary_result is not None:
                db.add(
                    ModelEvaluationEvent(
                        source=source,
                        production_model_version=model_version,
                        canary_model_version=canary_result.get("model_version"),
                        production_prediction=prediction,
                        canary_prediction=str(canary_result["prediction"]),
                        production_confidence=confidence,
                        canary_confidence=float(canary_result["confidence"]),
                        diverged=str(canary_result["prediction"]) != prediction,
                    )
                )

        if not is_threat:
            return event, None

        dedup_key = f"{prediction}:{source_ip}:{destination_ip}"
        cutoff = datetime.utcnow() - timedelta(minutes=settings.alert_dedup_window_minutes)

        existing = db.scalar(
            select(Alert)
            .where(
                and_(
                    Alert.dedup_key == dedup_key,
                    Alert.created_at >= cutoff,
                    Alert.status.in_(
                        [
                            AlertStatus.new.value,
                            AlertStatus.triaged.value,
                            AlertStatus.investigating.value,
                        ]
                    ),
                )
            )
            .order_by(desc(Alert.created_at))
        )

        if existing is not None:
            if confidence > existing.confidence:
                existing.confidence = confidence
                existing.severity = self._severity(confidence)
            existing.updated_at = datetime.utcnow()
            return event, existing

        alert = Alert(
            event_id=event.id,
            dedup_key=dedup_key,
            type=prediction,
            severity=self._severity(confidence),
            source_ip=source_ip,
            destination_ip=destination_ip,
            confidence=confidence,
            status=AlertStatus.new.value,
        )
        db.add(alert)
        db.flush()
        notification_service.notify_alert(
            {
                "id": alert.id,
                "event_id": event.id,
                "type": alert.type,
                "severity": alert.severity,
                "source_ip": alert.source_ip,
                "destination_ip": alert.destination_ip,
                "confidence": alert.confidence,
                "status": alert.status,
                "model_version": model_version,
                "source": source,
            }
        )
        return event, alert

    def dashboard_stats(self, db: Session) -> dict[str, Any]:
        total_flows = db.scalar(select(func.count(ClassificationEvent.id))) or 0
        threats_detected = db.scalar(
            select(func.count(ClassificationEvent.id)).where(ClassificationEvent.is_threat.is_(True))
        ) or 0
        benign_flows = max(total_flows - threats_detected, 0)

        critical_alerts = db.scalar(
            select(func.count(Alert.id)).where(
                and_(Alert.severity == AlertSeverity.critical.value, Alert.status != AlertStatus.resolved.value)
            )
        ) or 0

        last_updated = db.scalar(
            select(func.max(ClassificationEvent.created_at))
        )

        return {
            "total_flows": total_flows,
            "threats_detected": threats_detected,
            "benign_flows": benign_flows,
            "critical_alerts": critical_alerts,
            "last_updated": last_updated.isoformat() if last_updated else None,
        }

    def attack_distribution(self, db: Session) -> dict[str, Any]:
        rows = db.execute(
            select(ClassificationEvent.prediction, func.count(ClassificationEvent.id))
            .where(ClassificationEvent.is_threat.is_(True))
            .group_by(ClassificationEvent.prediction)
            .order_by(desc(func.count(ClassificationEvent.id)))
        ).all()

        total_threats = sum(count for _, count in rows)
        distribution = [
            {
                "type": prediction,
                "count": count,
                "percentage": round((count / total_threats) * 100, 1) if total_threats else 0.0,
            }
            for prediction, count in rows
        ]

        return {
            "distribution": distribution,
            "total_threats": total_threats,
        }


detection_service = DetectionService()
