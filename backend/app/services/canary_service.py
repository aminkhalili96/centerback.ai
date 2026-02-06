"""Canary model evaluation service."""

from __future__ import annotations

from pathlib import Path
import random
import threading
from typing import Any

import joblib
import numpy as np

from app.config import settings


class CanaryService:
    """Loads and evaluates a canary model on sampled traffic."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._enabled = False
        self._traffic_percent = 0
        self._model_path: str | None = None
        self._model = None
        self._label_encoder = None
        self._feature_names = None
        self._version: str | None = None

    def _resolve_path(self, model_path: str) -> Path:
        path = Path(model_path)
        if path.is_absolute():
            return path
        return Path(__file__).resolve().parents[2] / path

    def configure_from_settings(self) -> None:
        if not settings.canary_enabled or not settings.canary_model_path:
            return
        self.enable(settings.canary_model_path, settings.canary_traffic_percent)

    def enable(self, model_path: str, traffic_percent: int) -> dict[str, Any]:
        resolved_path = self._resolve_path(model_path)
        if not resolved_path.exists():
            raise ValueError(f"Canary model artifact not found at {resolved_path}")

        data = joblib.load(resolved_path)
        model = data.get("model")
        label_encoder = data.get("label_encoder")
        feature_names = data.get("feature_names")
        if model is None or label_encoder is None or feature_names is None:
            raise ValueError("Invalid canary model artifact format")

        with self._lock:
            self._model = model
            self._label_encoder = label_encoder
            self._feature_names = list(feature_names)
            self._model_path = str(resolved_path)
            self._version = resolved_path.stem
            self._traffic_percent = max(1, min(100, int(traffic_percent)))
            self._enabled = True

        return self.status()

    def disable(self) -> dict[str, Any]:
        with self._lock:
            self._enabled = False
            self._traffic_percent = 0
            self._model_path = None
            self._model = None
            self._label_encoder = None
            self._feature_names = None
            self._version = None
        return self.status()

    def should_sample(self) -> bool:
        return self._enabled and random.random() * 100 < self._traffic_percent

    def evaluate(self, features: list[float]) -> dict[str, Any] | None:
        if not self._enabled or self._model is None or self._label_encoder is None:
            return None

        np_features = np.asarray(features, dtype=float)
        if np_features.ndim == 1:
            np_features = np_features.reshape(1, -1)

        pred_idx = self._model.predict(np_features)[0]
        probs = self._model.predict_proba(np_features)[0]
        prediction = self._label_encoder.inverse_transform([pred_idx])[0]
        confidence = float(probs[pred_idx])
        return {
            "prediction": prediction,
            "confidence": confidence,
            "model_version": self._version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self._enabled,
            "traffic_percent": self._traffic_percent,
            "model_path": self._model_path,
            "model_version": self._version,
        }


canary_service = CanaryService()
