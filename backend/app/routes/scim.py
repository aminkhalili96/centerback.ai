"""SCIM v2 user provisioning routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.entities import User, UserRole
from app.services.audit_service import audit_service
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


def _scim_authz(authorization: str | None = Header(default=None)) -> None:
    if not settings.scim_bearer_token:
        raise HTTPException(status_code=503, detail="SCIM is not configured")

    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or token != settings.scim_bearer_token:
        raise HTTPException(status_code=401, detail="Invalid SCIM token")


class ScimEmail(BaseModel):
    value: str
    primary: bool | None = None


class ScimRole(BaseModel):
    value: str


class ScimCreateUser(BaseModel):
    userName: str = Field(min_length=3, max_length=120)
    active: bool = True
    externalId: str | None = None
    emails: list[ScimEmail] | None = None
    roles: list[ScimRole] | None = None


def _normalized_role(raw_role: str | None) -> str:
    if raw_role in {r.value for r in UserRole}:
        return raw_role
    return UserRole.viewer.value


def _to_scim_user(user: User) -> dict:
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": user.id,
        "userName": user.username,
        "active": bool(user.is_active),
        "externalId": user.external_subject,
        "roles": [{"value": user.role}],
        "meta": {
            "resourceType": "User",
            "created": user.created_at.isoformat() if user.created_at else None,
            "lastModified": user.updated_at.isoformat() if user.updated_at else None,
        },
    }


@router.get("/scim/v2/Users", dependencies=[Depends(_scim_authz)])
async def list_scim_users(
    db: Session = Depends(get_db),
    start_index: int = Query(default=1, alias="startIndex", ge=1),
    count: int = Query(default=100, ge=1, le=500),
):
    total = db.scalar(select(func.count(User.id)))
    users = db.execute(
        select(User).order_by(User.created_at).offset(start_index - 1).limit(count)
    ).scalars().all()
    resources = [_to_scim_user(user) for user in users]
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": int(total or 0),
        "startIndex": start_index,
        "itemsPerPage": len(resources),
        "Resources": resources,
    }


@router.post("/scim/v2/Users", dependencies=[Depends(_scim_authz)])
async def create_scim_user(payload: ScimCreateUser, db: Session = Depends(get_db)):
    if db.scalar(select(User.id).where(User.username == payload.userName)) is not None:
        raise HTTPException(status_code=409, detail="User already exists")

    role = _normalized_role(payload.roles[0].value if payload.roles else None)
    user = auth_service.create_user(
        db=db,
        username=payload.userName,
        password=str(uuid.uuid4()),
        role=role,
    )
    user.is_active = payload.active
    user.auth_provider = "scim"
    user.external_subject = payload.externalId
    db.flush()

    audit_service.log(
        db=db,
        action="scim.create_user",
        target_type="user",
        target_id=user.id,
        actor=None,
        details={"username": user.username, "role": user.role},
    )
    db.commit()

    return _to_scim_user(user)


@router.patch("/scim/v2/Users/{user_id}", dependencies=[Depends(_scim_authz)])
async def patch_scim_user(user_id: str, payload: dict, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    operations = payload.get("Operations", [])
    if not isinstance(operations, list):
        raise HTTPException(status_code=400, detail="Invalid SCIM patch payload")

    for operation in operations:
        op = str(operation.get("op", "")).lower()
        value = operation.get("value", {})
        path = str(operation.get("path", "")).lower()
        if op not in {"add", "replace", "remove"}:
            continue
        if path in {"active", "is_active"}:
            if op == "remove":
                user.is_active = False
            else:
                user.is_active = bool(value)
        elif path in {"role", "roles"}:
            role_value = value
            if isinstance(value, list) and value:
                role_value = value[0].get("value")
            if isinstance(role_value, dict):
                role_value = role_value.get("value")
            if op != "remove":
                user.role = _normalized_role(str(role_value))

    audit_service.log(
        db=db,
        action="scim.patch_user",
        target_type="user",
        target_id=user.id,
        actor=None,
        details={"active": user.is_active, "role": user.role},
    )
    db.commit()
    return _to_scim_user(user)


@router.delete("/scim/v2/Users/{user_id}", dependencies=[Depends(_scim_authz)])
async def deactivate_scim_user(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    audit_service.log(
        db=db,
        action="scim.deactivate_user",
        target_type="user",
        target_id=user.id,
        actor=None,
        details={"username": user.username},
    )
    db.commit()
    return {}
