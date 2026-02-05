"""Stats service - dashboard statistics."""

from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime, timedelta
import random

from ml.inference import inference


class StatsService:
    """Service for dashboard statistics."""
    
    def __init__(self) -> None:
        # In production, this would query the database.
        self._inference = inference
        if not self._inference.is_loaded():
            self._inference.load_model()
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get main dashboard statistics.
        
        Returns:
            Dictionary with stats for dashboard cards
        """
        # Mock data for development - replace with database queries.
        model_accuracy_pct: float = 0.0
        if self._inference.is_loaded():
            if self._inference.accuracy is not None:
                model_accuracy_pct = round(float(self._inference.accuracy) * 100, 2)

        total_flows = 12847
        threats_detected = 26
        benign_flows = max(total_flows - threats_detected, 0)

        return {
            "total_flows": total_flows,
            "threats_detected": threats_detected,
            "benign_flows": benign_flows,
            "critical_alerts": 3,
            "model_accuracy": model_accuracy_pct,
            "model_loaded": self._inference.is_loaded(),
            "last_updated": datetime.utcnow().isoformat(),
        }
    
    def get_attack_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of attack types.
        
        Returns:
            Dictionary with attack type counts and percentages
        """
        # Mock data for development
        distribution = [
            {"type": "DDoS", "count": 45, "percentage": 40.2},
            {"type": "PortScan", "count": 32, "percentage": 28.6},
            {"type": "DoS Hulk", "count": 15, "percentage": 13.4},
            {"type": "Bot", "count": 10, "percentage": 8.9},
            {"type": "Web Attack", "count": 8, "percentage": 7.1},
            {"type": "Other", "count": 2, "percentage": 1.8},
        ]
        
        return {
            "distribution": distribution,
            "total_threats": 112,
        }
    
    def get_traffic_timeline(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get traffic analysis timeline.
        
        Args:
            hours: Number of hours to include
            
        Returns:
            List of hourly traffic data points
        """
        timeline = []
        now = datetime.utcnow()
        
        for i in range(hours):
            timestamp = now - timedelta(hours=hours - i - 1)
            timeline.append({
                "timestamp": timestamp.isoformat(),
                "total": random.randint(400, 600),
                "benign": random.randint(380, 580),
                "threats": random.randint(0, 20),
            })
        
        return timeline
