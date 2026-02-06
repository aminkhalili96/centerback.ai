"""Outbound alert notification integrations."""

from __future__ import annotations

from datetime import datetime
import logging
import threading
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Sends alert notifications to external systems."""

    def _post_json(self, url: str, payload: dict[str, Any]) -> None:
        with httpx.Client(timeout=settings.notification_timeout_seconds) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()

    def _send(self, payload: dict[str, Any]) -> None:
        if settings.notification_webhook_url:
            try:
                self._post_json(settings.notification_webhook_url, payload)
            except Exception as exc:
                logger.warning("Webhook notification failed: %s", exc)

        if settings.notification_slack_webhook_url:
            try:
                self._post_json(
                    settings.notification_slack_webhook_url,
                    {
                        "text": (
                            f"[CenterBack] {payload.get('type')} {payload.get('severity')} "
                            f"{payload.get('source_ip')} -> {payload.get('destination_ip')}"
                        ),
                    },
                )
            except Exception as exc:
                logger.warning("Slack notification failed: %s", exc)

    def notify_alert(self, alert_payload: dict[str, Any]) -> None:
        if not settings.notification_webhook_url and not settings.notification_slack_webhook_url:
            return
        payload = {
            **alert_payload,
            "sent_at": datetime.utcnow().isoformat(),
        }
        threading.Thread(target=self._send, args=(payload,), daemon=True).start()

    def status(self) -> dict[str, Any]:
        return {
            "webhook_enabled": bool(settings.notification_webhook_url),
            "slack_enabled": bool(settings.notification_slack_webhook_url),
            "timeout_seconds": settings.notification_timeout_seconds,
        }


notification_service = NotificationService()
