"""
ML Inference Service for CenterBack.AI
Loads trained model and provides prediction methods
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import joblib

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = Path(__file__).resolve().parent / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "random_forest_v1.joblib"

_env_model_path = os.environ.get("MODEL_PATH")
if _env_model_path:
    env_path = Path(_env_model_path)
    MODEL_PATH = env_path if env_path.is_absolute() else (BACKEND_DIR / env_path)
else:
    MODEL_PATH = DEFAULT_MODEL_PATH


class MLInference:
    """ML inference service for network traffic classification."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to reuse loaded model."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.model = None
        self.label_encoder = None
        self.feature_names = None
        self.accuracy = None
        self._initialized = True
        
    def load_model(self) -> bool:
        """Load the trained model from disk."""
        if not MODEL_PATH.exists():
            logger.error(f"Model not found at {MODEL_PATH}")
            logger.info("Run 'python ml/train.py' to train the model first")
            return False
        
        try:
            logger.info(f"Loading model from {MODEL_PATH}...")
            data = joblib.load(MODEL_PATH)
            self.model = data['model']
            self.label_encoder = data['label_encoder']
            self.feature_names = data['feature_names']
            self.accuracy = data['accuracy']
            logger.info(f"Model loaded successfully (accuracy: {self.accuracy:.2%})")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None
    
    def predict(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Predict attack type for a single flow.
        
        Args:
            features: Array of 78 features
            
        Returns:
            Dict with prediction, confidence, and is_threat flag
        """
        if not self.is_loaded():
            if not self.load_model():
                return {"error": "Model not loaded"}
        
        # Reshape for single prediction
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Get prediction and probabilities
        prediction_idx = self.model.predict(features)[0]
        probabilities = self.model.predict_proba(features)[0]
        
        prediction = self.label_encoder.inverse_transform([prediction_idx])[0]
        confidence = float(probabilities[prediction_idx])
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "is_threat": prediction != "BENIGN",
            "all_probabilities": {
                label: float(prob) 
                for label, prob in zip(self.label_encoder.classes_, probabilities)
            }
        }
    
    def predict_batch(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Predict attack types for a batch of flows.
        
        Args:
            df: DataFrame with flow features
            
        Returns:
            List of prediction dicts
        """
        if not self.is_loaded():
            if not self.load_model():
                return [{"error": "Model not loaded"}]
        
        # Align columns with model features
        missing_cols = set(self.feature_names) - set(df.columns)
        if missing_cols:
            logger.warning(f"Missing features: {missing_cols}")
            for col in missing_cols:
                df[col] = 0
        
        # Select and order features
        X = df[self.feature_names].values
        
        # Handle NaN/Inf
        X = np.nan_to_num(X, nan=0, posinf=0, neginf=0)
        
        # Get predictions
        predictions_idx = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        
        results = []
        for i, (pred_idx, probs) in enumerate(zip(predictions_idx, probabilities)):
            prediction = self.label_encoder.inverse_transform([pred_idx])[0]
            confidence = float(probs[pred_idx])
            
            results.append({
                "prediction": prediction,
                "confidence": confidence,
                "is_threat": prediction != "BENIGN",
            })
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model metadata."""
        if not self.is_loaded():
            self.load_model()
            
        return {
            "loaded": self.is_loaded(),
            "accuracy": self.accuracy,
            "n_features": len(self.feature_names) if self.feature_names else 0,
            "classes": list(self.label_encoder.classes_) if self.label_encoder else [],
        }


# Global instance
inference = MLInference()
