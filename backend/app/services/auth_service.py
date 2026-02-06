"""Authentication and authorization helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

import jwt
from jwt import PyJWKClient
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.entities import User, UserRole

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for user authentication and token management."""
    def __init__(self) -> None:
        self._jwks_client: PyJWKClient | None = None
        self._jwks_url: str | None = None

    @property
    def is_oidc_mode(self) -> bool:
        return settings.auth_mode.lower() == "oidc"

    def hash_password(self, password: str) -> str:
        return password_context.hash(password)

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        return password_context.verify(plain_password, password_hash)

    def create_user(self, db: Session, username: str, password: str, role: str) -> User:
        normalized_role = role if role in {r.value for r in UserRole} else UserRole.viewer.value
        user = User(
            username=username,
            password_hash=self.hash_password(password),
            role=normalized_role,
            auth_provider="local",
            is_active=True,
        )
        db.add(user)
        return user

    def authenticate(self, db: Session, username: str, password: str) -> User | None:
        user = db.scalar(select(User).where(User.username == username))
        if user is None or not user.is_active:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    def get_or_create_oidc_user(self, db: Session, payload: dict[str, Any]) -> User:
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            raise ValueError("OIDC token missing subject claim")

        user = db.scalar(select(User).where(User.external_subject == subject))
        if user is not None:
            return user

        username_claim = settings.auth_oidc_username_claim or "email"
        username_val = payload.get(username_claim) or payload.get("email") or payload.get("preferred_username")
        if not isinstance(username_val, str) or not username_val:
            username_val = f"oidc-{subject[:12]}"

        base_username = username_val[:120]
        candidate = base_username
        counter = 1
        while db.scalar(select(User.id).where(User.username == candidate)) is not None:
            suffix = f"-{counter}"
            candidate = f"{base_username[: max(1, 120 - len(suffix))]}{suffix}"
            counter += 1

        user = User(
            username=candidate,
            external_subject=subject,
            auth_provider="oidc",
            password_hash=self.hash_password(str(uuid.uuid4())),
            role=UserRole.viewer.value,
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.commit()
        db.refresh(user)
        return user

    def create_access_token(self, subject: str, role: str) -> str:
        expires_delta = timedelta(minutes=settings.auth_access_token_expire_minutes)
        expire = datetime.now(tz=timezone.utc) + expires_delta
        payload: dict[str, Any] = {
            "sub": subject,
            "role": role,
            "exp": expire,
            "iat": datetime.now(tz=timezone.utc),
        }
        return jwt.encode(payload, settings.auth_jwt_secret, algorithm=settings.auth_jwt_algorithm)

    def decode_local_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, settings.auth_jwt_secret, algorithms=[settings.auth_jwt_algorithm])

    def _jwks(self) -> PyJWKClient:
        if not settings.auth_oidc_jwks_url:
            raise ValueError("AUTH_OIDC_JWKS_URL is required in oidc auth mode")
        if self._jwks_client is None or self._jwks_url != settings.auth_oidc_jwks_url:
            self._jwks_client = PyJWKClient(settings.auth_oidc_jwks_url)
            self._jwks_url = settings.auth_oidc_jwks_url
        return self._jwks_client

    def decode_oidc_token(self, token: str) -> dict[str, Any]:
        jwks_client = self._jwks()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        if not settings.auth_oidc_audience:
            raise ValueError("AUTH_OIDC_AUDIENCE is required in oidc auth mode")
        if not settings.auth_oidc_issuer:
            raise ValueError("AUTH_OIDC_ISSUER is required in oidc auth mode")

        allowed_algorithms = ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]
        configured_algorithm = settings.auth_jwt_algorithm.upper()
        if configured_algorithm in allowed_algorithms:
            allowed_algorithms = [configured_algorithm]

        return jwt.decode(
            token,
            signing_key.key,
            algorithms=allowed_algorithms,
            audience=settings.auth_oidc_audience,
            issuer=settings.auth_oidc_issuer,
        )

    def decode_access_token(self, token: str) -> dict[str, Any]:
        if self.is_oidc_mode:
            return self.decode_oidc_token(token)
        return self.decode_local_token(token)
