"""Auth and RBAC dependencies."""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, Header, HTTPException
from jwt import PyJWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.entities import User
from app.services.auth_service import AuthService

auth_service = AuthService()


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User | None:
    """Resolve current user from JWT bearer token."""
    if not authorization:
        if settings.auth_enforced:
            raise HTTPException(status_code=401, detail="Missing authorization token")
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    try:
        payload = auth_service.decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    if auth_service.is_oidc_mode:
        try:
            user = auth_service.get_or_create_oidc_user(db, payload)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
    else:
        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            raise HTTPException(status_code=401, detail="Invalid token subject")
        user = db.get(User, user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


def require_roles(*roles: str) -> Callable:
    """RBAC dependency factory."""

    def _enforce(user: User | None = Depends(get_current_user)) -> User | None:
        if not settings.auth_enforced:
            return user

        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        if roles and user.role not in set(roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _enforce
