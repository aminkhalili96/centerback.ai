from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings
from app.db import Base, engine, init_db
from app.main import app
from app.services.canary_service import canary_service


@pytest.fixture()
def client() -> TestClient:
    original_auth_required = settings.auth_required
    original_auth_mode = settings.auth_mode
    original_ingest_pipeline_enabled = settings.ingest_pipeline_enabled
    original_demo_fallback = settings.enable_demo_fallback
    original_scim_bearer_token = settings.scim_bearer_token

    settings.auth_required = True
    settings.auth_mode = "local"
    settings.ingest_pipeline_enabled = False
    settings.enable_demo_fallback = False
    settings.scim_bearer_token = None
    canary_service.disable()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    init_db()

    with TestClient(app) as test_client:
        yield test_client

    settings.auth_required = original_auth_required
    settings.auth_mode = original_auth_mode
    settings.ingest_pipeline_enabled = original_ingest_pipeline_enabled
    settings.enable_demo_fallback = original_demo_fallback
    settings.scim_bearer_token = original_scim_bearer_token
    canary_service.disable()


@pytest.fixture()
def admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={
            "username": settings.bootstrap_admin_username,
            "password": settings.bootstrap_admin_password,
        },
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
