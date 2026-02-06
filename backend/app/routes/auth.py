"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.entities import User, UserRole
from app.services.audit_service import audit_service
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=8, max_length=256)


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=8, max_length=256)
    role: str = Field(default=UserRole.viewer.value)


@router.post("/auth/login", response_model=dict)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    if settings.auth_mode.lower() == "oidc":
        raise HTTPException(status_code=400, detail="Local login disabled in oidc auth mode")

    user = auth_service.authenticate(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = auth_service.create_access_token(subject=user.id, role=user.role)
    audit_service.log(
        db,
        action="auth.login",
        target_type="user",
        target_id=user.id,
        actor=user,
        details={"username": user.username},
    )
    db.commit()

    return {
        "success": True,
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            },
        },
        "message": "Login successful",
    }


@router.get("/auth/me", response_model=dict)
async def me(current_user: User | None = Depends(get_current_user)):
    if current_user is None:
        return {
            "success": True,
            "data": None,
            "message": "Anonymous access",
        }

    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "is_active": current_user.is_active,
        },
        "message": "User profile retrieved",
    }


@router.post("/auth/users", response_model=dict, dependencies=[Depends(require_roles(UserRole.admin.value))])
async def create_user(
    payload: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    exists = db.scalar(select(User).where(User.username == payload.username))
    if exists is not None:
        raise HTTPException(status_code=409, detail="Username already exists")

    role = payload.role if payload.role in {r.value for r in UserRole} else UserRole.viewer.value
    user = auth_service.create_user(db=db, username=payload.username, password=payload.password, role=role)
    db.flush()

    audit_service.log(
        db,
        action="auth.create_user",
        target_type="user",
        target_id=user.id,
        actor=current_user,
        details={"username": user.username, "role": user.role},
    )
    db.commit()

    return {
        "success": True,
        "data": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
        "message": "User created",
    }
