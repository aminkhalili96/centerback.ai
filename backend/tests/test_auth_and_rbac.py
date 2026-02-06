from __future__ import annotations

from fastapi.testclient import TestClient


def test_protected_endpoint_requires_auth(client: TestClient) -> None:
    response = client.post("/api/classify", json={"features": [0.0] * 78})
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert "authorization" in body["error"].lower() or "authentication" in body["error"].lower()


def test_admin_can_create_user_and_login(client: TestClient, admin_headers: dict[str, str]) -> None:
    create_user_response = client.post(
        "/api/auth/users",
        headers=admin_headers,
        json={
            "username": "analyst1",
            "password": "StrongPass123!",
            "role": "analyst",
        },
    )
    assert create_user_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "analyst1",
            "password": "StrongPass123!",
        },
    )
    assert login_response.status_code == 200
    payload = login_response.json()["data"]
    assert payload["token_type"] == "bearer"
    assert payload["user"]["role"] == "analyst"
