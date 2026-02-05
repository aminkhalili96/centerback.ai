"""Classifier service - ML model inference."""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

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
                }

        return self._mock_prediction()

    def predict_batch(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Predict classes for multiple network flows.

        Args:
            df: DataFrame with flow features

        Returns:
            Dictionary with results summary and individual predictions
        """
        if df is None or df.empty:
            return {"total": 0, "benign": 0, "threats": 0, "results": []}

        df = df.copy()
        df.columns = df.columns.astype(str).str.strip()

        if self._inference.is_loaded() or self._inference.load_model():
            batch_results = self._inference.predict_batch(df)
            if batch_results and isinstance(batch_results, list) and "error" not in batch_results[0]:
                benign_count = sum(1 for r in batch_results if not r["is_threat"])
                threat_count = len(batch_results) - benign_count
                return {
                    "total": len(batch_results),
                    "benign": benign_count,
                    "threats": threat_count,
                    "results": batch_results[:100],
                }

            logger.warning("Falling back to mock predictions for batch classification.")

        # Fallback for demo when model is unavailable
        benign_count = 0
        threat_count = 0
        results: List[Dict[str, Any]] = []
        for idx in range(len(df)):
            result = self._mock_prediction()
            if idx < 100:
                results.append(result)
            if result["is_threat"]:
                threat_count += 1
            else:
                benign_count += 1

        return {
            "total": len(df),
            "benign": benign_count,
            "threats": threat_count,
            "results": results,
        }

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
                    benign_count = sum(1 for r in batch_results if not r["is_threat"])
                    threat_count = len(batch_results) - benign_count
                    return {
                        "total": len(batch_results),
                        "benign": benign_count,
                        "threats": threat_count,
                        "results": batch_results,
                    }
            except Exception:
                logger.exception("Failed to generate sample predictions from sample_data.csv")

        sample_results = [
            {"prediction": "BENIGN", "confidence": 0.98, "is_threat": False},
            {"prediction": "DDoS", "confidence": 0.95, "is_threat": True},
            {"prediction": "PortScan", "confidence": 0.87, "is_threat": True},
            {"prediction": "BENIGN", "confidence": 0.99, "is_threat": False},
            {"prediction": "DoS Hulk", "confidence": 0.92, "is_threat": True},
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
        }
