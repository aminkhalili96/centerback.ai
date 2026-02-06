"""Model drift and canary divergence analytics."""

from __future__ import annotations

from collections import Counter
import math
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.entities import ClassificationEvent, ModelEvaluationEvent


class DriftService:
    """Computes prediction-distribution and canary divergence drift signals."""

    @staticmethod
    def _distribution(values: list[str]) -> dict[str, float]:
        total = len(values)
        if total == 0:
            return {}
        counts = Counter(values)
        return {label: count / total for label, count in counts.items()}

    @staticmethod
    def _jensen_shannon(p: dict[str, float], q: dict[str, float]) -> float:
        labels = set(p) | set(q)
        if not labels:
            return 0.0

        def _kl(a: dict[str, float], b: dict[str, float]) -> float:
            value = 0.0
            for label in labels:
                av = a.get(label, 0.0)
                bv = b.get(label, 0.0)
                if av > 0 and bv > 0:
                    value += av * math.log2(av / bv)
            return value

        m = {label: (p.get(label, 0.0) + q.get(label, 0.0)) / 2 for label in labels}
        return math.sqrt(max((_kl(p, m) + _kl(q, m)) / 2, 0.0))

    def get_drift_report(self, db: Session, window_events: int | None = None) -> dict[str, Any]:
        window = window_events or settings.drift_window_events
        if window < 50:
            window = 50

        predictions = db.execute(
            select(ClassificationEvent.prediction)
            .order_by(desc(ClassificationEvent.created_at))
            .limit(window * 2)
        ).scalars().all()

        if len(predictions) < window * 2:
            return {
                "status": "insufficient_data",
                "required_events": window * 2,
                "available_events": len(predictions),
                "prediction_js_divergence": None,
                "canary_divergence_rate": None,
            }

        current = predictions[:window]
        baseline = predictions[window : window * 2]
        current_dist = self._distribution(current)
        baseline_dist = self._distribution(baseline)
        js_score = self._jensen_shannon(current_dist, baseline_dist)

        canary_rows = db.execute(
            select(ModelEvaluationEvent.diverged)
            .order_by(desc(ModelEvaluationEvent.created_at))
            .limit(window)
        ).scalars().all()
        if canary_rows:
            canary_divergence_rate = sum(1 for row in canary_rows if row) / len(canary_rows)
        else:
            canary_divergence_rate = None

        threshold = settings.drift_alert_threshold
        is_alert = js_score >= threshold
        if canary_divergence_rate is not None:
            is_alert = is_alert or canary_divergence_rate >= threshold

        return {
            "status": "alert" if is_alert else "ok",
            "window_events": window,
            "threshold": threshold,
            "prediction_js_divergence": round(js_score, 6),
            "canary_divergence_rate": round(canary_divergence_rate, 6) if canary_divergence_rate is not None else None,
            "current_distribution": current_dist,
            "baseline_distribution": baseline_dist,
        }


drift_service = DriftService()
