"""
Classifier Service - ML Model Inference
"""

import logging
from typing import List, Dict, Any
from pathlib import Path
import numpy as np

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


class ClassifierService:
    """Service for network traffic classification."""
    
    def __init__(self):
        """Initialize the classifier service."""
        self.model = None
        self.model_path = Path("ml/models/random_forest_v1.joblib")
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the trained model."""
        try:
            if self.model_path.exists():
                import joblib
                self.model = joblib.load(self.model_path)
                logger.info(f"Model loaded from {self.model_path}")
            else:
                logger.warning(f"Model not found at {self.model_path}. Using mock predictions.")
                self.model = None
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = None
    
    def predict_single(self, features: List[float]) -> Dict[str, Any]:
        """
        Predict class for a single network flow.
        
        Args:
            features: List of 78 float features
            
        Returns:
            Dictionary with prediction, confidence, and threat status
        """
        if self.model is None:
            # Mock prediction for demo when model not trained yet
            return self._mock_prediction()
        
        features_array = np.array(features).reshape(1, -1)
        prediction = self.model.predict(features_array)[0]
        probabilities = self.model.predict_proba(features_array)[0]
        confidence = float(np.max(probabilities))
        
        return {
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "is_threat": prediction != "BENIGN",
        }
    
    def predict_batch(self, df) -> Dict[str, Any]:
        """
        Predict classes for multiple network flows.
        
        Args:
            df: DataFrame with features
            
        Returns:
            Dictionary with results summary and individual predictions
        """
        results = []
        benign_count = 0
        threat_count = 0
        
        # Get feature columns (exclude label if present)
        feature_cols = [col for col in df.columns if col.lower() != 'label']
        
        for idx, row in df.iterrows():
            features = row[feature_cols[:78]].tolist()
            result = self.predict_single(features)
            results.append(result)
            
            if result["is_threat"]:
                threat_count += 1
            else:
                benign_count += 1
        
        return {
            "total": len(results),
            "benign": benign_count,
            "threats": threat_count,
            "results": results[:100],  # Limit to first 100 for response size
        }
    
    def predict_sample(self) -> Dict[str, Any]:
        """
        Predict on sample data for demo.
        
        Returns:
            Sample predictions
        """
        # Mock sample results for demo
        sample_results = [
            {"prediction": "BENIGN", "confidence": 0.98, "is_threat": False},
            {"prediction": "DDoS", "confidence": 0.95, "is_threat": True},
            {"prediction": "PortScan", "confidence": 0.87, "is_threat": True},
            {"prediction": "BENIGN", "confidence": 0.99, "is_threat": False},
            {"prediction": "DoS Hulk", "confidence": 0.92, "is_threat": True},
        ]
        
        return {
            "total": 5,
            "benign": 2,
            "threats": 3,
            "results": sample_results,
        }
    
    def _mock_prediction(self) -> Dict[str, Any]:
        """Generate mock prediction when model not available."""
        import random
        
        is_threat = random.random() > 0.7
        if is_threat:
            prediction = random.choice(ATTACK_LABELS[1:])  # Exclude BENIGN
        else:
            prediction = "BENIGN"
        
        return {
            "prediction": prediction,
            "confidence": round(random.uniform(0.85, 0.99), 4),
            "is_threat": is_threat,
        }
