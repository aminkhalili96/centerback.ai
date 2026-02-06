from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings


def test_scim_user_provisioning(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "scim_bearer_token", "test-scim-token")
    headers = {"Authorization": "Bearer test-scim-token"}

    create_response = client.post(
        "/api/scim/v2/Users",
        headers=headers,
        json={
            "userName": "scim.user",
            "active": True,
            "externalId": "ext-123",
            "roles": [{"value": "analyst"}],
        },
    )
    assert create_response.status_code == 200
    user = create_response.json()
    assert user["userName"] == "scim.user"
    assert user["roles"][0]["value"] == "analyst"

    list_response = client.get("/api/scim/v2/Users", headers=headers)
    assert list_response.status_code == 200
    resources = list_response.json()["Resources"]
    assert any(item["userName"] == "scim.user" for item in resources)

    patch_response = client.patch(
        f"/api/scim/v2/Users/{user['id']}",
        headers=headers,
        json={
            "Operations": [
                {"op": "replace", "path": "active", "value": False},
                {"op": "replace", "path": "role", "value": "viewer"},
            ]
        },
    )
    assert patch_response.status_code == 200
    patched_user = patch_response.json()
    assert patched_user["active"] is False
    assert patched_user["roles"][0]["value"] == "viewer"
