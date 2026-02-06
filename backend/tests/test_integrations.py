from __future__ import annotations

from fastapi.testclient import TestClient


def test_integration_status_and_notify_test(client: TestClient, admin_headers: dict[str, str]) -> None:
    status_response = client.get("/api/integrations/status", headers=admin_headers)
    assert status_response.status_code == 200
    status_payload = status_response.json()["data"]
    assert "webhook_enabled" in status_payload
    assert "slack_enabled" in status_payload

    notify_response = client.post(
        "/api/integrations/notify/test",
        headers=admin_headers,
        json={
            "type": "PortScan",
            "severity": "medium",
            "source_ip": "1.1.1.1",
            "destination_ip": "2.2.2.2",
            "confidence": 0.88,
        },
    )
    assert notify_response.status_code == 200
    assert notify_response.json()["data"]["delivered_async"] is True
