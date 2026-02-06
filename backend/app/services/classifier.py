"""Classifier service - ML model inference."""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from app.config import settings
from ml.inference import inference

logger = logging.getLogger(__name__)

# Attack type labels from CICIDS2017
ATTACK_LABELS = [
    "BENIGN",
    "Bot",
    "DDoS",
    "DoS GoldenEye",
    "DoS Hulk",
    "DoS Slowhttptest",
    "DoS Slowloris",
    "FTP-Patator",
    "Heartbleed",
    "Infiltration",
    "PortScan",
    "SSH-Patator",
    "Web Attack - Brute Force",
    "Web Attack - SQL Injection",
    "Web Attack - XSS",
]

BACKEND_DIR = Path(__file__).resolve().parents[2]
SAMPLE_DATA_PATH = BACKEND_DIR / "data" / "sample_data.csv"


class ClassifierService:
    """Service for network traffic classification."""

    def __init__(self) -> None:
        self._inference = inference
        if not self._inference.is_loaded():
            self._inference.load_model()

    def predict_single(self, features: List[float]) -> Dict[str, Any]:
        """
        Predict class for a single network flow.

        Args:
            features: List of 78 float features

        Returns:
            Dictionary with prediction, confidence, and threat status
        """
        if self._inference.is_loaded() or self._inference.load_model():
            result = self._inference.predict(np.asarray(features, dtype=float))
            if "error" not in result:
                return {
                    "prediction": result["prediction"],
                    "confidence": round(float(result["confidence"]), 4),
                    "is_threat": bool(result["is_threat"]),
                    "model_version": self._inference.get_model_version(),
                }
        if settings.enable_demo_fallback:
            return self._mock_prediction()
        raise RuntimeError("Model unavailable for classification")

    def predict_batch(self, df: pd.DataFrame) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Predict classes for multiple network flows.

        Args:
            df: DataFrame with flow features

        Returns:
            (summary, full_results) where:
              - summary contains a preview list (first 100) for API responses
              - full_results contains all per-row results for session tracking
        """
        if df is None or df.empty:
            empty = {"total": 0, "benign": 0, "threats": 0, "results": []}
            return empty, []

        df = df.copy()
        df.columns = df.columns.astype(str).str.strip()

        if self._inference.is_loaded() or self._inference.load_model():
            batch_results = self._inference.predict_batch(df)
            if batch_results and isinstance(batch_results, list) and "error" not in batch_results[0]:
                model_version = self._inference.get_model_version()
                enriched_results = [
                    {
                        **item,
                        "model_version": model_version,
                    }
                    for item in batch_results
                ]
                benign_count = sum(1 for r in batch_results if not r["is_threat"])
                threat_count = len(batch_results) - benign_count
                summary = {
                    "total": len(enriched_results),
                    "benign": benign_count,
                    "threats": threat_count,
                    "results": enriched_results[:100],
                }
                return summary, enriched_results

            logger.warning("Model predict_batch returned invalid payload.")

        if not settings.enable_demo_fallback:
            raise RuntimeError("Model unavailable for batch classification")

        # Fallback for demo mode when explicitly enabled
        benign_count = 0
        threat_count = 0
        preview_results: List[Dict[str, Any]] = []
        all_results: List[Dict[str, Any]] = []
        for idx in range(len(df)):
            result = self._mock_prediction()
            all_results.append(result)
            if idx < 100:
                preview_results.append(result)
            if result["is_threat"]:
                threat_count += 1
            else:
                benign_count += 1

        summary = {
            "total": len(df),
            "benign": benign_count,
            "threats": threat_count,
            "results": preview_results,
        }
        return summary, all_results

    def predict_sample(self) -> Dict[str, Any]:
        """
        Predict on sample data for demo.

        Returns:
            Sample predictions
        """
        if SAMPLE_DATA_PATH.exists() and (self._inference.is_loaded() or self._inference.load_model()):
            try:
                sample_df = pd.read_csv(SAMPLE_DATA_PATH, nrows=25)
                sample_df.columns = sample_df.columns.astype(str).str.strip()
                if "Label" in sample_df.columns:
                    sample_df = sample_df.drop(columns=["Label"])

                batch_results = self._inference.predict_batch(sample_df)
                if batch_results and isinstance(batch_results, list) and "error" not in batch_results[0]:
                    model_version = self._inference.get_model_version()
                    enriched_results = [
                        {
                            **item,
                            "model_version": model_version,
                        }
                        for item in batch_results
                    ]
                    benign_count = sum(1 for r in batch_results if not r["is_threat"])
                    threat_count = len(batch_results) - benign_count
                    return {
                        "total": len(enriched_results),
                        "benign": benign_count,
                        "threats": threat_count,
                        "results": enriched_results,
                    }
            except Exception:
                logger.exception("Failed to generate sample predictions from sample_data.csv")

        if not settings.enable_demo_fallback:
            raise RuntimeError("Sample classification unavailable: model or sample data missing")

        sample_results = [
            {"prediction": "BENIGN", "confidence": 0.98, "is_threat": False, "model_version": "demo"},
            {"prediction": "DDoS", "confidence": 0.95, "is_threat": True, "model_version": "demo"},
            {"prediction": "PortScan", "confidence": 0.87, "is_threat": True, "model_version": "demo"},
            {"prediction": "BENIGN", "confidence": 0.99, "is_threat": False, "model_version": "demo"},
            {"prediction": "DoS Hulk", "confidence": 0.92, "is_threat": True, "model_version": "demo"},
        ]

        return {"total": 5, "benign": 2, "threats": 3, "results": sample_results}

    def _mock_prediction(self) -> Dict[str, Any]:
        """Generate mock prediction when model not available."""
        is_threat = random.random() > 0.7
        prediction = random.choice(ATTACK_LABELS[1:]) if is_threat else "BENIGN"

        return {
            "prediction": prediction,
            "confidence": round(random.uniform(0.85, 0.99), 4),
            "is_threat": is_threat,
            "model_version": "demo",
        }
