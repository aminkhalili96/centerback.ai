"""Stats service - dashboard statistics."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.entities import IngestionMessage, QueueStatus
from app.services.detection_service import detection_service
from ml.inference import inference


class StatsService:
    """Service for dashboard and distribution statistics."""

    def __init__(self) -> None:
        self._inference = inference
        if not self._inference.is_loaded():
            self._inference.load_model()

    def get_dashboard_stats(self, db: Session) -> dict[str, Any]:
        stats = detection_service.dashboard_stats(db)
        model_accuracy_pct = None
        if self._inference.is_loaded() and self._inference.accuracy is not None:
            model_accuracy_pct = round(float(self._inference.accuracy) * 100, 2)

        queue_depth = db.scalar(
            select(func.count(IngestionMessage.id)).where(
                IngestionMessage.status.in_(
                    [QueueStatus.queued.value, QueueStatus.processing.value, QueueStatus.failed.value]
                )
            )
        ) or 0
        oldest_queued = db.scalar(
            select(func.min(IngestionMessage.created_at)).where(
                and_(
                    IngestionMessage.status.in_([QueueStatus.queued.value, QueueStatus.failed.value]),
                    IngestionMessage.created_at.is_not(None),
                )
            )
        )
        queue_lag_seconds = None
        if oldest_queued is not None:
            queue_lag_seconds = max(int((datetime.utcnow() - oldest_queued).total_seconds()), 0)

        return {
            "total_flows": stats["total_flows"],
            "threats_detected": stats["threats_detected"],
            "benign_flows": stats["benign_flows"],
            "critical_alerts": stats["critical_alerts"],
            "model_accuracy": model_accuracy_pct,
            "model_loaded": self._inference.is_loaded(),
            "ingestion_queue_depth": int(queue_depth),
            "ingestion_queue_lag_seconds": queue_lag_seconds,
            "last_updated": stats["last_updated"] or datetime.utcnow().isoformat(),
        }

    def get_session_stats(self, db: Session) -> dict[str, Any]:
        dashboard = self.get_dashboard_stats(db)
        distribution = detection_service.attack_distribution(db)

        return {
            "has_data": dashboard["total_flows"] > 0,
            "total_flows": dashboard["total_flows"],
            "threats_detected": dashboard["threats_detected"],
            "benign_flows": dashboard["benign_flows"],
            "critical_alerts": dashboard["critical_alerts"],
            "attack_distribution": distribution["distribution"],
            "model_accuracy": dashboard["model_accuracy"],
            "started_at": None,
            "last_updated": dashboard["last_updated"],
        }

    def get_attack_distribution(self, db: Session) -> dict[str, Any]:
        return detection_service.attack_distribution(db)

    def get_traffic_timeline(self, db: Session, hours: int = 24) -> list[dict[str, Any]]:
        """Simple derived timeline for charting.

        This currently provides a deterministic placeholder based on current totals.
        """
        stats = detection_service.dashboard_stats(db)
        if hours <= 0:
            return []

        avg_total = max(int(stats["total_flows"] / hours), 1)
        avg_threats = int(stats["threats_detected"] / hours)
        now = datetime.utcnow()
        timeline: list[dict[str, Any]] = []
        for i in range(hours):
            ts = now - timedelta(hours=hours - i - 1)
            threats = max(avg_threats, 0)
            total = max(avg_total, threats)
            timeline.append(
                {
                    "timestamp": ts.isoformat(),
                    "total": total,
                    "benign": max(total - threats, 0),
                    "threats": threats,
                }
            )
        return timeline


stats_service = StatsService()
