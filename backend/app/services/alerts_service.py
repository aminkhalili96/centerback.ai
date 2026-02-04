"""
Alerts Service - Threat Alerts Management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid


# Mock alerts for development
MOCK_ALERTS = [
    {
        "id": str(uuid.uuid4()),
        "type": "DDoS",
        "severity": "critical",
        "source_ip": "192.168.1.105",
        "destination_ip": "10.0.0.50",
        "confidence": 0.95,
        "timestamp": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
        "status": "active",
    },
    {
        "id": str(uuid.uuid4()),
        "type": "PortScan",
        "severity": "high",
        "source_ip": "192.168.1.42",
        "destination_ip": "10.0.0.0/24",
        "confidence": 0.89,
        "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
        "status": "active",
    },
    {
        "id": str(uuid.uuid4()),
        "type": "DoS Hulk",
        "severity": "high",
        "source_ip": "192.168.2.15",
        "destination_ip": "10.0.0.80",
        "confidence": 0.92,
        "timestamp": (datetime.utcnow() - timedelta(minutes=12)).isoformat(),
        "status": "investigating",
    },
    {
        "id": str(uuid.uuid4()),
        "type": "Bot",
        "severity": "medium",
        "source_ip": "192.168.1.200",
        "destination_ip": "external",
        "confidence": 0.78,
        "timestamp": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
        "status": "resolved",
    },
    {
        "id": str(uuid.uuid4()),
        "type": "Web Attack - SQL Injection",
        "severity": "critical",
        "source_ip": "192.168.3.50",
        "destination_ip": "10.0.0.100",
        "confidence": 0.97,
        "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        "status": "resolved",
    },
]


class AlertsService:
    """Service for managing threat alerts."""
    
    def __init__(self):
        """Initialize alerts service."""
        # In production, this would connect to database
        self.alerts = MOCK_ALERTS.copy()
    
    def get_recent_alerts(
        self,
        limit: int = 10,
        severity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent alerts.
        
        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity level
            
        Returns:
            List of alert dictionaries
        """
        alerts = self.alerts.copy()
        
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return alerts[:limit]
    
    def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific alert by ID.
        
        Args:
            alert_id: Alert UUID
            
        Returns:
            Alert dictionary or None if not found
        """
        for alert in self.alerts:
            if alert["id"] == alert_id:
                return alert
        return None
    
    def create_alert(
        self,
        alert_type: str,
        severity: str,
        source_ip: str,
        destination_ip: str,
        confidence: float,
    ) -> Dict[str, Any]:
        """
        Create a new alert.
        
        Args:
            alert_type: Type of attack detected
            severity: low, medium, high, or critical
            source_ip: Source IP address
            destination_ip: Destination IP address
            confidence: Model confidence score
            
        Returns:
            Created alert dictionary
        """
        alert = {
            "id": str(uuid.uuid4()),
            "type": alert_type,
            "severity": severity,
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active",
        }
        
        self.alerts.insert(0, alert)
        return alert
