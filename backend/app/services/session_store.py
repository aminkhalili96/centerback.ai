"""Session-based stats storage for demo mode."""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import threading


@dataclass
class SessionStats:
    """In-memory session statistics."""
    total_flows: int = 0
    threats_detected: int = 0
    benign_flows: int = 0
    critical_alerts: int = 0
    classifications: List[Dict[str, Any]] = field(default_factory=list)
    attack_distribution: Dict[str, int] = field(default_factory=dict)
    started_at: Optional[str] = None
    last_updated: Optional[str] = None


class SessionStore:
    """Thread-safe session storage for demo statistics."""
    
    _instance: Optional["SessionStore"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "SessionStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._stats = SessionStats()
        return cls._instance
    
    def reset(self) -> None:
        """Reset all session stats."""
        with self._lock:
            self._stats = SessionStats()
    
    def add_classification(self, prediction: str, is_threat: bool, confidence: float) -> None:
        """Add a classification result to session stats."""
        with self._lock:
            now = datetime.utcnow().isoformat()
            
            if self._stats.started_at is None:
                self._stats.started_at = now
            
            self._stats.last_updated = now
            self._stats.total_flows += 1
            
            if is_threat:
                self._stats.threats_detected += 1
                # Track attack distribution
                self._stats.attack_distribution[prediction] = \
                    self._stats.attack_distribution.get(prediction, 0) + 1
                # High confidence threats are critical
                if confidence >= 0.9:
                    self._stats.critical_alerts += 1
            else:
                self._stats.benign_flows += 1
            
            # Store last 100 classifications for display
            if len(self._stats.classifications) < 100:
                self._stats.classifications.append({
                    "prediction": prediction,
                    "is_threat": is_threat,
                    "confidence": confidence,
                    "timestamp": now,
                })
    
    def add_batch_classification(self, results: List[Dict[str, Any]]) -> None:
        """Add batch classification results."""
        for result in results:
            self.add_classification(
                prediction=result.get("prediction", "UNKNOWN"),
                is_threat=result.get("is_threat", False),
                confidence=result.get("confidence", 0.0),
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        with self._lock:
            has_data = self._stats.total_flows > 0
            
            # Calculate attack distribution percentages
            distribution = []
            total_threats = self._stats.threats_detected
            for attack_type, count in sorted(
                self._stats.attack_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                pct = round((count / total_threats * 100), 1) if total_threats > 0 else 0
                distribution.append({
                    "type": attack_type,
                    "count": count,
                    "percentage": pct,
                })
            
            return {
                "has_data": has_data,
                "total_flows": self._stats.total_flows,
                "threats_detected": self._stats.threats_detected,
                "benign_flows": self._stats.benign_flows,
                "critical_alerts": self._stats.critical_alerts,
                "attack_distribution": distribution,
                "started_at": self._stats.started_at,
                "last_updated": self._stats.last_updated,
            }
    
    def get_recent_classifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent classifications."""
        with self._lock:
            return list(reversed(self._stats.classifications[-limit:]))


# Global singleton
session_store = SessionStore()
