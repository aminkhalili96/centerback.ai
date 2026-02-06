from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings
from app.services.ingest_pipeline import ingestion_pipeline


def test_ingest_enqueue_and_process(client: TestClient, admin_headers: dict[str, str], monkeypatch) -> None:
    ingest_response = client.post(
        "/api/ingest/flows",
        headers=admin_headers,
        json={
            "source": "pytest",
            "flows": [
                {
                    "flow_id": "f-1",
                    "source_ip": "10.0.0.1",
                    "destination_ip": "10.0.0.2",
                    "features": [0.1] * 78,
                }
            ],
        },
    )
    assert ingest_response.status_code == 200
    assert ingest_response.json()["data"]["queued"] == 1

    monkeypatch.setattr(
        ingestion_pipeline._classifier,
        "predict_single",
        lambda features: {
            "prediction": "DDoS",
            "confidence": 0.97,
            "is_threat": True,
            "model_version": "pytest-model",
        },
    )

    processed = ingestion_pipeline._process_batch()
    assert processed >= 1

    queue_response = client.get("/api/ingest/queue", headers=admin_headers)
    assert queue_response.status_code == 200
    queue_data = queue_response.json()["data"]
    assert queue_data.get("done", 0) >= 1

    stats_response = client.get("/api/stats", headers=admin_headers)
    assert stats_response.status_code == 200
    stats_data = stats_response.json()["data"]
    assert stats_data["total_flows"] >= 1
    assert stats_data["threats_detected"] >= 1


def test_ingest_idempotency_skips_duplicate_flows(client: TestClient, admin_headers: dict[str, str]) -> None:
    payload = {
        "source": "pytest",
        "flows": [
            {
                "flow_id": "dup-flow-1",
                "source_ip": "10.0.0.1",
                "destination_ip": "10.0.0.2",
                "features": [0.2] * 78,
            }
        ],
    }

    first = client.post("/api/ingest/flows", headers=admin_headers, json=payload)
    assert first.status_code == 200
    assert first.json()["data"]["queued"] == 1
    assert first.json()["data"]["duplicates_skipped"] == 0

    second = client.post("/api/ingest/flows", headers=admin_headers, json=payload)
    assert second.status_code == 200
    assert second.json()["data"]["queued"] == 0
    assert second.json()["data"]["duplicates_skipped"] == 1


def test_ingest_backpressure_rejects_over_capacity(client: TestClient, admin_headers: dict[str, str], monkeypatch) -> None:
    monkeypatch.setattr(settings, "ingest_max_queue_depth", 0)
    response = client.post(
        "/api/ingest/flows",
        headers=admin_headers,
        json={
            "source": "pytest",
            "flows": [
                {
                    "flow_id": "flow-over-capacity",
                    "source_ip": "10.0.0.10",
                    "destination_ip": "10.0.0.20",
                    "features": [0.3] * 78,
                }
            ],
        },
    )
    assert response.status_code == 429
