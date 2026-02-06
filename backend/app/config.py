"""Application configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "centerback.db"


class Settings(BaseSettings):
    """Environment-driven application settings."""

    app_env: str = "development"
    database_url: str = Field(default=f"sqlite:///{DEFAULT_DB_PATH}")

    auth_required: bool = False
    auth_mode: str = "local"
    auth_jwt_secret: str = "change-me-in-production"
    auth_jwt_algorithm: str = "HS256"
    auth_access_token_expire_minutes: int = 60
    auth_oidc_issuer: str | None = None
    auth_oidc_audience: str | None = None
    auth_oidc_jwks_url: str | None = None
    auth_oidc_username_claim: str = "email"
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = "change-me-now"
    bootstrap_admin_role: str = "admin"
    scim_bearer_token: str | None = None

    enable_demo_fallback: bool = False
    alert_dedup_window_minutes: int = 10

    ingest_poll_interval_seconds: int = 2
    ingest_batch_size: int = 100
    ingest_max_attempts: int = 5
    ingest_pipeline_enabled: bool = True
    ingest_max_queue_depth: int = 5000
    ingest_idempotency_window_minutes: int = 30

    rate_limit_per_minute: int = 120
    max_request_bytes: int = 5 * 1024 * 1024

    notification_webhook_url: str | None = None
    notification_slack_webhook_url: str | None = None
    notification_timeout_seconds: int = 5

    canary_enabled: bool = False
    canary_model_path: str | None = None
    canary_traffic_percent: int = 5

    drift_window_events: int = 500
    drift_alert_threshold: float = 0.2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def auth_enforced(self) -> bool:
        return self.auth_required or self.is_production


settings = Settings()
