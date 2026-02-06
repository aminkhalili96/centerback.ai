from __future__ import annotations

from fastapi.testclient import TestClient

from app.routes import classify as classify_route


def test_canary_and_drift_endpoints(
    client: TestClient,
    admin_headers: dict[str, str],
    monkeypatch,
) -> None:
    enable_response = client.post(
        "/api/model/canary/enable",
        headers=admin_headers,
        json={
            "model_path": "ml/models/random_forest_v1.joblib",
            "traffic_percent": 100,
        },
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["data"]["enabled"] is True

    monkeypatch.setattr(
        classify_route.classifier,
        "predict_single",
        lambda features: {
            "prediction": "BENIGN",
            "confidence": 0.91,
            "is_threat": False,
            "model_version": "prod-test",
        },
    )

    for _ in range(5):
        response = client.post(
            "/api/classify",
            headers=admin_headers,
            json={
                "features": [0.1] * 78,
                "source_ip": "1.1.1.1",
                "destination_ip": "2.2.2.2",
            },
        )
        assert response.status_code == 200

    evaluations_response = client.get("/api/model/evaluations", headers=admin_headers)
    assert evaluations_response.status_code == 200
    assert evaluations_response.json()["data"]["total"] >= 1

    drift_response = client.get("/api/model/drift?window_events=2", headers=admin_headers)
    assert drift_response.status_code == 200
    assert "status" in drift_response.json()["data"]

    disable_response = client.post("/api/model/canary/disable", headers=admin_headers)
    assert disable_response.status_code == 200
    assert disable_response.json()["data"]["enabled"] is False
