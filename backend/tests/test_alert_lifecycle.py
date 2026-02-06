from __future__ import annotations

from fastapi.testclient import TestClient

from app.routes import classify as classify_route


def test_alert_status_transition_validation(
    client: TestClient,
    admin_headers: dict[str, str],
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        classify_route.classifier,
        "predict_single",
        lambda features: {
            "prediction": "PortScan",
            "confidence": 0.93,
            "is_threat": True,
            "model_version": "pytest-model",
        },
    )

    classify_response = client.post(
        "/api/classify",
        headers=admin_headers,
        json={
            "features": [0.2] * 78,
            "source_ip": "192.168.1.10",
            "destination_ip": "192.168.1.20",
        },
    )
    assert classify_response.status_code == 200
    alert_id = classify_response.json()["data"]["alert_id"]
    assert alert_id is not None

    resolve_response = client.patch(
        f"/api/alerts/{alert_id}/status",
        headers=admin_headers,
        json={"status": "resolved"},
    )
    assert resolve_response.status_code == 200
    assert resolve_response.json()["data"]["status"] == "resolved"

    invalid_transition = client.patch(
        f"/api/alerts/{alert_id}/status",
        headers=admin_headers,
        json={"status": "investigating"},
    )
    assert invalid_transition.status_code == 400
    assert "Invalid transition" in invalid_transition.json()["error"]
